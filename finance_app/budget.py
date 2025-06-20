from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Budget:
    limits: Dict[str, float] = field(default_factory=dict)

    def set_limit(self, category: str, amount: float):
        self.limits[category] = amount

    def get_limit(self, category: str) -> float:
        return self.limits.get(category, 0.0)

    def is_exceeded(self, category: str, spent: float) -> bool:
        return spent > self.get_limit(category)
