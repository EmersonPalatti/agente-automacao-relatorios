"""Avalia os prompts do pipeline com métricas objetivas.

Roda o pipeline com LLM (e codegen) em datasets de domínios diferentes e mede:

- planner: plano aceito, colunas inexistentes, colunas de ID, análises repetidas
- coder: análises resolvidas por código gerado, sucesso na 1ª tentativa, fallbacks
- writer: números citados que não aparecem no payload recebido (grounding)

Uso:
    python scripts/eval_prompts.py --label baseline --runs 2
    python scripts/eval_prompts.py --label v2 --runs 2 --compare outputs/eval/baseline.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.nodes import writer_payload  # noqa: E402
from graph.workflow import run_pipeline  # noqa: E402
from tools.llm import llm_configured  # noqa: E402
from tools.models import AnalysisPlan, AnalysisResult, DataProfile  # noqa: E402

# Número que não faz parte de um identificador (a1, P90, col_2). Pode vir seguido
# de unidade (21,0h, 45min, 3x), que não impede a contagem.
NUMBER = re.compile(r"(?<![A-Za-z_\d.,])-?\d(?:[\d.,]*\d)?(?![\d])")


# --------------------------------------------------------------------------- datasets


def make_tickets_csv(path: Path, n: int = 600, seed: int = 7) -> Path:
    """Chamados de suporte: domínio diferente do de pedidos, com nulos e datas BR."""
    rng = random.Random(seed)
    channels = ["Chat", "E-mail", "Telefone", "WhatsApp"]
    products = ["App", "Pagamentos", "Entrega", "Conta", "Cupom"]
    priorities = ["baixa", "média", "alta", "crítica"]
    teams = ["N1", "N2", "Especialistas"]
    start = datetime(2026, 3, 1)
    lines = ["ticket_id,aberto_em,canal,produto,prioridade,horas_resolucao,csat,reaberto,equipe"]
    for i in range(1, n + 1):
        opened = start + timedelta(hours=rng.randint(0, 24 * 120))
        prio = rng.choices(priorities, weights=[40, 35, 20, 5])[0]
        base = {"baixa": 30, "média": 18, "alta": 8, "crítica": 3}[prio]
        hours = round(rng.expovariate(1 / base), 1)
        csat = "" if rng.random() < 0.35 else str(max(1, min(5, round(5 - hours / 20 + rng.gauss(0, 0.8)))))
        lines.append(
            ",".join(
                [
                    f"T{i:05d}",
                    opened.strftime("%d/%m/%Y %H:%M"),
                    rng.choice(channels),
                    rng.choices(products, weights=[30, 25, 25, 12, 8])[0],
                    prio,
                    "" if rng.random() < 0.05 else str(hours),
                    csat,
                    "sim" if rng.random() < 0.12 else "não",
                    rng.choice(teams),
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------- grounding


def _walk_numbers(obj, out: set[float]) -> None:
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        out.add(float(obj))
        return
    if isinstance(obj, str):
        for tok in NUMBER.findall(obj):
            out.update(_interpretations(tok))
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            _walk_numbers(k, out)
            _walk_numbers(v, out)
        return
    if isinstance(obj, (list, tuple)):
        for v in obj:
            _walk_numbers(v, out)


def _interpretations(tok: str) -> set[float]:
    """Um token como '1.234,5' ou '39.98' pode estar em formato BR ou EN."""
    vals: set[float] = set()
    for cand in (tok.replace(",", ""), tok.replace(".", "").replace(",", "."), tok.replace(",", ".")):
        try:
            vals.add(float(cand))
        except ValueError:
            pass
    return vals


def _decimals(tok: str) -> int:
    m = re.search(r"[.,](\d+)$", tok)
    return len(m.group(1)) if m and len(m.group(1)) != 3 else 0


def _grounded(tok: str, allowed: set[float]) -> bool:
    d = _decimals(tok)
    for x in _interpretations(tok):
        for v in allowed:
            for cand in (v, v * 100, v / 100):
                if round(cand, d) == round(x, d) or abs(cand - x) <= max(abs(cand) * 0.005, 0.051 if d else 0.5):
                    return True
    return False


def grounding(text: str, payload: dict) -> dict:
    allowed: set[float] = set()
    _walk_numbers(payload, allowed)
    # Não conta marcadores de lista/ordinais nem números dentro de nomes como a1, P90.
    toks = [t for t in NUMBER.findall(text) if not re.fullmatch(r"[0-9]", t)]
    # "7 vezes", "3x": razão calculada pelo modelo, mesmo com um dígito só.
    toks += re.findall(r"(?<![\d.,])(\d)(?=\s*(?:vezes|x\b))", text)
    bad = [t for t in toks if not _grounded(t, allowed)]
    return {"numbers": len(toks), "ungrounded": len(bad), "ungrounded_examples": bad[:8]}


# --------------------------------------------------------------------------- run


def evaluate_run(dataset: Path, out_dir: Path) -> dict:
    events: list[str] = []
    final = run_pipeline(dataset, out_dir, use_llm=True, allow_codegen=True, progress=events.append)
    prof = DataProfile.model_validate(final["profile"])
    planned = AnalysisPlan.model_validate(final["plan"])
    results = [AnalysisResult.model_validate(r) for r in final.get("analysis_results") or []]

    cols = {c.name: c for c in prof.columns}
    hints = [h for a in planned.analyses for h in a.columns_hint]
    keys = [(a.analysis_type, tuple(a.columns_hint)) for a in planned.analyses]
    planner_failed = any("Planner LLM falhou" in e for e in events)

    llm_code = [r for r in results if r.used_llm_code and r.success]
    insights = final.get("insights_md") or ""
    usage = final.get("token_usage") or []
    return {
        "dataset": dataset.name,
        "seconds": round(final["timings"]["total"], 1),
        "tokens": sum(int(u.get("total_tokens") or 0) for u in usage),
        "llm_calls": len(usage),
        "planner_ok": not planner_failed,
        "n_analyses": len(planned.analyses),
        "types": [a.analysis_type for a in planned.analyses],
        "invalid_columns": sum(1 for h in hints if h not in cols),
        "id_columns": sum(1 for h in hints if h in cols and cols[h].is_likely_id),
        "duplicate_analyses": len(keys) - len(set(keys)),
        "codegen_ok": len(llm_code),
        "codegen_first_try": sum(1 for r in llm_code if r.attempts == 1),
        "fallbacks": sum(1 for e in events if "fallback template" in e),
        "failed_analyses": sum(1 for r in results if not r.success),
        "codegen_errors": [e.strip()[:160] for e in events if "codegen falhou" in e],
        "writer_used_llm": not any("Writer LLM falhou" in e for e in events),
        **{f"writer_{k}": v for k, v in grounding(insights, writer_payload(prof, planned, results)).items()},
        "insights_md": insights,
        "writer_payload": writer_payload(prof, planned, results),
    }


def summarize(runs: list[dict]) -> dict:
    n_an = sum(r["n_analyses"] for r in runs) or 1
    nums = sum(r["writer_numbers"] for r in runs) or 1
    return {
        "runs": len(runs),
        "planner_ok_rate": round(sum(r["planner_ok"] for r in runs) / len(runs), 2),
        "invalid_columns": sum(r["invalid_columns"] for r in runs),
        "id_columns": sum(r["id_columns"] for r in runs),
        "duplicate_analyses": sum(r["duplicate_analyses"] for r in runs),
        "codegen_ok_rate": round(sum(r["codegen_ok"] for r in runs) / n_an, 2),
        "codegen_first_try_rate": round(sum(r["codegen_first_try"] for r in runs) / n_an, 2),
        "fallbacks": sum(r["fallbacks"] for r in runs),
        "failed_analyses": sum(r["failed_analyses"] for r in runs),
        "writer_ungrounded_rate": round(sum(r["writer_ungrounded"] for r in runs) / nums, 3),
        "writer_numbers": sum(r["writer_numbers"] for r in runs),
        "avg_seconds": round(sum(r["seconds"] for r in runs) / len(runs), 1),
        "avg_tokens": round(sum(r["tokens"] for r in runs) / len(runs)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--runs", type=int, default=2, help="corridas por dataset")
    ap.add_argument("--compare", type=Path, help="JSON de uma avaliação anterior")
    args = ap.parse_args()

    if not llm_configured():
        sys.exit("Sem chave de LLM: a avaliação precisa do modelo real.")

    out = ROOT / "outputs" / "eval"
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="eval_"))
    datasets = [ROOT / "data" / "raw" / "pedidos_ifood.csv", make_tickets_csv(tmp / "chamados_suporte.csv")]

    runs = []
    for ds in datasets:
        for i in range(args.runs):
            print(f"[{args.label}] {ds.name} #{i + 1}", flush=True)
            r = evaluate_run(ds, out / "reports" / args.label)
            print(
                f"   planner_ok={r['planner_ok']} codegen={r['codegen_ok']}/{r['n_analyses']} "
                f"(1ª={r['codegen_first_try']}) fallbacks={r['fallbacks']} "
                f"ungrounded={r['writer_ungrounded']}/{r['writer_numbers']} {r['seconds']}s",
                flush=True,
            )
            runs.append(r)

    report = {"label": args.label, "summary": summarize(runs), "runs": runs}
    dest = out / f"{args.label}.json"
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if args.compare and args.compare.exists():
        before = json.loads(args.compare.read_text(encoding="utf-8"))["summary"]
        print("\nmétrica                    antes    depois")
        for k, v in report["summary"].items():
            print(f"{k:<26} {before.get(k)!s:>8} {v!s:>8}")
    print(f"\nsalvo em {dest}")


if __name__ == "__main__":
    main()
