from .transactions import TransactionManager

class Analysis:
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
