"""Savings goals helpers."""

from dataclasses import dataclass, field
from typing import Iterable, List

@dataclass
class Goal:
    """Simple savings goal."""

    name: str
    target_amount: float
    saved_amount: float = 0.0

    def progress(self) -> float:
        if self.target_amount == 0:
            return 0.0
        return min(self.saved_amount / self.target_amount, 1.0)

@dataclass
class GoalManager:
    """Manage a collection of goals."""

    goals: List[Goal] = field(default_factory=list)

    def add_goal(self, goal: Goal):
        self.goals.append(goal)

    def update_goal(self, name: str, amount: float):
        for g in self.goals:
            if g.name == name:
                g.saved_amount += amount
                break

    def remove_goal(self, name: str) -> bool:
        """Remove goal by name."""
        for idx, g in enumerate(self.goals):
            if g.name == name:
                del self.goals[idx]
                return True
        return False

    def get_goal(self, name: str) -> Goal | None:
        for g in self.goals:
            if g.name == name:
                return g
        return None

    def all_goals(self) -> Iterable[Goal]:
        """Return iterator over all goals."""
        return list(self.goals)
