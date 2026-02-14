from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List, Optional


TWOPLACES = Decimal("0.01")


def _to_decimal(value: float | str | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class FinancialTransaction:
    """Audit-safe immutable transaction model using Decimal precision."""

    transaction_id: str
    transaction_date: date
    amount: Decimal
    currency: str = "MXN"
    ledger_type: str = "FISCAL"
    is_accrual: bool = False
    reversal_date: Optional[date] = None

    def __post_init__(self):
        object.__setattr__(self, "amount", _to_decimal(self.amount))
        if self.amount == Decimal("0.00"):
            raise ValueError("No se permiten transacciones de valor cero en auditoría.")
        if len(self.currency) != 3:
            raise ValueError("currency debe tener 3 caracteres (ISO)")


@dataclass
class Transaction:
    date: str
    description: str
    amount: float
    category: str


@dataclass
class PolicyLine:
    policy_id: str
    date: str
    description: str
    account: str
    debit: float
    credit: float
    category: str = "poliza"
    is_accrual: bool = False
    reversal_date: Optional[str] = None

    def signed_amount(self) -> float:
        return float(_to_decimal(self.debit) - _to_decimal(self.credit))


@dataclass
class PolicyPostingSummary:
    lines_posted: int
    policies_posted: int


@dataclass
class TransactionManager:
    transactions: List[Transaction] = field(default_factory=list)

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def post_policy_lines(self, lines: Iterable[PolicyLine]) -> PolicyPostingSummary:
        grouped: dict[str, List[PolicyLine]] = {}
        line_count = 0
        for line in lines:
            line_count += 1
            grouped.setdefault(line.policy_id, []).append(line)

        if line_count == 0:
            raise ValueError("No hay lineas de poliza para postear")

        for policy_id, policy_lines in grouped.items():
            debit_total = sum(_to_decimal(line.debit) for line in policy_lines)
            credit_total = sum(_to_decimal(line.credit) for line in policy_lines)
            if (debit_total - credit_total).quantize(TWOPLACES, rounding=ROUND_HALF_UP) != Decimal("0.00"):
                raise ValueError(f"Poliza desbalanceada {policy_id}: cargo={debit_total}, abono={credit_total}")

            for line in policy_lines:
                self.add_transaction(Transaction(
                    date=line.date,
                    description=f"{line.description} [{policy_id}/{line.account}]",
                    amount=line.signed_amount(),
                    category=f"{line.category}:{line.account}",
                ))

        return PolicyPostingSummary(lines_posted=line_count, policies_posted=len(grouped))

    def total_income(self) -> float:
        return float(sum(_to_decimal(t.amount) for t in self.transactions if _to_decimal(t.amount) > 0))

    def total_expenses(self) -> float:
        return float(sum(-_to_decimal(t.amount) for t in self.transactions if _to_decimal(t.amount) < 0))

    def balance(self) -> float:
        return self.total_income() - self.total_expenses()

    def export_csv(self, path: str):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'description', 'amount', 'category'])
            for t in self.transactions:
                writer.writerow([t.date, t.description, t.amount, t.category])

    def import_csv(self, path: str):
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.add_transaction(Transaction(
                    date=row['date'],
                    description=row['description'],
                    amount=float(row['amount']),
                    category=row.get('category', '')
                ))
