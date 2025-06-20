import csv
from dataclasses import dataclass, field
from typing import List

@dataclass
class Transaction:
    date: str
    description: str
    amount: float
    category: str

@dataclass
class TransactionManager:
    transactions: List[Transaction] = field(default_factory=list)

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def total_income(self) -> float:
        return sum(t.amount for t in self.transactions if t.amount > 0)

    def total_expenses(self) -> float:
        return sum(-t.amount for t in self.transactions if t.amount < 0)

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
