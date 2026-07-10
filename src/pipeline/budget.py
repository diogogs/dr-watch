"""Per-run request budget — the free-tier guard (charter principle 6: honest failure).

The daily pipeline is the only LLM consumer and runs once a day, so a per-run cap is a
per-day cap. When the budget runs out the pipeline publishes a PARTIAL result with an
explicit notice; it never fails silently and never overruns the provider's free tier.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class BudgetExhausted(RuntimeError):
    """Raised on the first request past the cap; the caller degrades gracefully."""


@dataclass
class RequestBudget:
    max_requests: int
    spent: int = field(default=0, init=False)

    def spend(self) -> None:
        if self.spent >= self.max_requests:
            raise BudgetExhausted(f"request budget exhausted ({self.max_requests})")
        self.spent += 1

    @property
    def remaining(self) -> int:
        return self.max_requests - self.spent
