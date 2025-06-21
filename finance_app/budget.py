"""Budget management."""

from dataclasses import dataclass, field
from typing import Dict, Iterable

@dataclass
class Budget:
    """Store spending limits and track spent amounts per category."""

    limits: Dict[str, float] = field(default_factory=dict)
    spent: Dict[str, float] = field(default_factory=dict)

    def set_limit(self, category: str, amount: float) -> None:
        self.limits[category] = amount

    # ------------------------------------------------------------------
    # Tracking helpers
    def add_expense(self, category: str, amount: float) -> None:
        """Record a new expense amount for the given category."""
        self.spent[category] = self.spent.get(category, 0.0) + abs(amount)

    def spent_so_far(self, category: str) -> float:
        return self.spent.get(category, 0.0)

    def get_limit(self, category: str) -> float:
        return self.limits.get(category, 0.0)

    def is_exceeded(self, category: str) -> bool:
        return self.spent_so_far(category) > self.get_limit(category)

    def remaining(self, category: str) -> float:
        """Return how much is left for the given category."""
        return self.get_limit(category) - self.spent_so_far(category)

    def reset(self, categories: Iterable[str] | None = None) -> None:
        """Reset tracked spending for given categories or all."""
        if categories is None:
            self.spent.clear()
        else:
            for cat in categories:
                self.spent.pop(cat, None)

    def summary(self) -> Dict[str, Dict[str, float]]:
        """Return current budget summary per category."""
        data: Dict[str, Dict[str, float]] = {}
        all_cats = set(self.limits) | set(self.spent)
        for cat in all_cats:
            data[cat] = {
                'limit': self.get_limit(cat),
                'spent': self.spent_so_far(cat),
                'remaining': self.remaining(cat),
            }
        return data
