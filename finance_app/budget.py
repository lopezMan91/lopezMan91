"""Budget management."""

from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Budget:
    """Store spending limits per category."""

    limits: Dict[str, float] = field(default_factory=dict)

    def set_limit(self, category: str, amount: float):
        self.limits[category] = amount

    def get_limit(self, category: str) -> float:
        return self.limits.get(category, 0.0)

    def is_exceeded(self, category: str, spent: float) -> bool:
        return spent > self.get_limit(category)

    def remaining(self, category: str, spent: float) -> float:
        """Return how much is left for the given category."""
        return self.get_limit(category) - spent
