from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
DEFAULT_MODEL = "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"
API_KEY_VARS = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY",
)


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8").strip()


def llm_configured() -> bool:
    return any(os.getenv(k) for k in API_KEY_VARS)


def resolve_model() -> str:
    model = (os.getenv("LLM_MODEL") or DEFAULT_MODEL).strip()
    if os.getenv("OPENROUTER_API_KEY") and not model.startswith(("openrouter/", "openai/", "groq/", "gemini/")):
        model = f"openrouter/{model}"
    return model


def complete(
    system: str,
    user: str,
    *,
    json_mode: bool = False,
    temperature: float = 0.2,
) -> tuple[str, dict]:
    """Chama LiteLLM. Retorna (texto, usage_dict)."""
    import litellm
    from litellm import completion

    litellm.drop_params = True
    model = resolve_model()
    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "timeout": 180,
        "max_tokens": 8192,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = completion(**kwargs)
    except Exception:
        if "response_format" in kwargs:
            kwargs.pop("response_format")
            resp = completion(**kwargs)
        else:
            raise
    text = resp.choices[0].message.content or ""
    usage = getattr(resp, "usage", None)
    usage_dict: dict = {"model": model}
    if usage is not None:
        usage_dict.update(
            {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
        )
    try:
        from litellm import completion_cost

        usage_dict["cost_usd"] = float(completion_cost(completion_response=resp) or 0.0)
    except Exception:
        usage_dict["cost_usd"] = 0.0
    return text, usage_dict


def parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("resposta sem objeto JSON")
    return json.loads(text[start : end + 1])


def summarize_usage(token_usage: list[dict]) -> dict:
    prompt = sum(int(u.get("prompt_tokens") or 0) for u in token_usage)
    completion = sum(int(u.get("completion_tokens") or 0) for u in token_usage)
    cost = sum(float(u.get("cost_usd") or 0) for u in token_usage)
    models = [u.get("model") for u in token_usage if u.get("model")]
    return {
        "calls": len(token_usage),
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "cost_usd": round(cost, 6),
        "model": models[-1] if models else None,
    }
