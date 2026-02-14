from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReconciliationItem:
    module_name: str
    ledger_balance: float
    subledger_balance: float
    evidence: str = ""
    status: str = "open"


@dataclass
class ReconciliationWorkflow:
    preparer: str
    reviewer: str
    approver: str
    items: list[ReconciliationItem] = field(default_factory=list)

    def add_item(self, item: ReconciliationItem):
        self.items.append(item)

    def run(self, tolerance: float = 0.01) -> list[str]:
        issues: list[str] = []
        for item in self.items:
            diff = round(item.ledger_balance - item.subledger_balance, 2)
            if abs(diff) > tolerance:
                item.status = "open"
                issues.append(f"{item.module_name} descuadrado por {diff}")
            else:
                item.status = "reconciled"
        return issues
