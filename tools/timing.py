from __future__ import annotations

from dataclasses import dataclass


DEFAULT_MANUAL_MINUTES = 210.0  # 3h30 — EDA + gráficos + relatório escrito


@dataclass(frozen=True)
class TimeEconomy:
    manual_seconds: float
    agent_seconds: float
    saved_seconds: float
    reduction_pct: float

    def as_dict(self) -> dict[str, float]:
        return {
            "manual_seconds": self.manual_seconds,
            "agent_seconds": self.agent_seconds,
            "saved_seconds": self.saved_seconds,
            "reduction_pct": self.reduction_pct,
        }


def compute_economy(manual_minutes: float, agent_seconds: float) -> TimeEconomy:
    manual_seconds = max(manual_minutes, 0.0) * 60.0
    agent_seconds = max(agent_seconds, 0.0)
    saved = max(manual_seconds - agent_seconds, 0.0)
    pct = (saved / manual_seconds * 100.0) if manual_seconds else 0.0
    return TimeEconomy(
        manual_seconds=manual_seconds,
        agent_seconds=agent_seconds,
        saved_seconds=saved,
        reduction_pct=pct,
    )


def format_duration(seconds: float) -> str:
    seconds = max(seconds, 0.0)
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, rem = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}min {rem:.0f}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes):02d}min"
