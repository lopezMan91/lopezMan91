from __future__ import annotations

from difflib import SequenceMatcher
from dataclasses import dataclass, field


@dataclass
class ReconciliationItem:
    module_name: str
    ledger_balance: float
    subledger_balance: float
    evidence: str = ""
    status: str = "open"


@dataclass
class BankStatementLine:
    line_id: str
    date: str
    description: str
    amount: float


@dataclass
class LedgerLine:
    line_id: str
    date: str
    description: str
    amount: float


@dataclass
class ReconciliationMatch:
    bank_line_id: str
    ledger_line_id: str
    score: float


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


def suggest_fuzzy_matches(
    bank_lines: list[BankStatementLine],
    ledger_lines: list[LedgerLine],
    amount_tolerance: float = 1.0,
    min_score: float = 0.75,
) -> list[ReconciliationMatch]:
    """Suggest potential reconciliation matches using amount and text similarity."""
    matches: list[ReconciliationMatch] = []
    used_ledger_ids: set[str] = set()

    for bank in bank_lines:
        best: ReconciliationMatch | None = None
        for ledger in ledger_lines:
            if ledger.line_id in used_ledger_ids:
                continue
            amount_gap = abs(bank.amount - ledger.amount)
            if amount_gap > amount_tolerance:
                continue
            desc_score = SequenceMatcher(None, bank.description.lower(), ledger.description.lower()).ratio()
            date_bonus = 0.1 if bank.date == ledger.date else 0.0
            score = max(0.0, min(1.0, desc_score + date_bonus))
            if score >= min_score and (best is None or score > best.score):
                best = ReconciliationMatch(
                    bank_line_id=bank.line_id,
                    ledger_line_id=ledger.line_id,
                    score=round(score, 4),
                )

        if best:
            matches.append(best)
            used_ledger_ids.add(best.ledger_line_id)

    return matches
