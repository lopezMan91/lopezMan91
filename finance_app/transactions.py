"""Transaction handling."""

import csv
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime

@dataclass
class Transaction:
    """Simple financial transaction."""

    date: str
    description: str
    amount: float
    category: str

    def __post_init__(self):
        # Ensure amount is stored as float
        self.amount = float(self.amount)

@dataclass
class TransactionManager:
    """Manage a list of transactions."""

    transactions: List[Transaction] = field(default_factory=list)

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def total_income(self) -> float:
        return sum(t.amount for t in self.transactions if t.amount > 0)

    def total_expenses(self) -> float:
        return sum(-t.amount for t in self.transactions if t.amount < 0)

    def spent_by_category(self, category: str) -> float:
        """Return total spent (positive value) for a category."""
        return sum(
            -t.amount
            for t in self.transactions
            if t.category == category and t.amount < 0
        )

    def balance(self) -> float:
        return self.total_income() - self.total_expenses()

    def summary_by_category(self) -> Dict[str, float]:
        """Return spent amount per category."""
        summary: Dict[str, float] = {}
        for t in self.transactions:
            if t.amount < 0:
                summary[t.category] = summary.get(t.category, 0.0) - t.amount
        return summary

    def monthly_totals(self) -> Dict[str, float]:
        """Return totals by YYYY-MM for quick reports."""
        totals: Dict[str, float] = {}
        for t in self.transactions:
            month = t.date[:7]  # assumes YYYY-MM-DD
            totals[month] = totals.get(month, 0.0) + t.amount
        return totals

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
