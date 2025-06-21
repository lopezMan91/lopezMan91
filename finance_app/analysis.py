"""Financial analysis helpers."""

from .transactions import TransactionManager

class Analysis:
    """Simple wrappers around transaction statistics."""

    def __init__(self, manager: TransactionManager):
        self.manager = manager

    def summary(self) -> str:
        income = self.manager.total_income()
        expenses = self.manager.total_expenses()
        balance = self.manager.balance()
        return (
            f"Ingresos: {income:.2f}\n"
            f"Gastos: {expenses:.2f}\n"
            f"Balance: {balance:.2f}"
        )

    def expense_ratio(self) -> float:
        """Return the ratio of expenses to income."""
        income = self.manager.total_income()
        expenses = self.manager.total_expenses()
        if income == 0:
            return 0.0
        return expenses / income
