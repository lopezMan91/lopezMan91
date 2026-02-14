from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .transactions import TransactionManager


@dataclass
class FinancialStatements:
    """Build basic financial statements from transaction data."""

    manager: TransactionManager

    def _sum_category_prefix(self, prefix: str) -> float:
        total = Decimal("0.00")
        target = prefix.lower().strip()
        for transaction in self.manager.transactions:
            category = transaction.category.lower().strip()
            if category.startswith(target):
                total += Decimal(str(transaction.amount))
        return float(total)

    def income_statement(self) -> dict[str, float]:
        revenues = self._sum_category_prefix("revenue") + self._sum_category_prefix("ingreso")
        expenses = abs(self._sum_category_prefix("expense")) + abs(self._sum_category_prefix("gasto"))

        # fallback for uncategorized entries using sign convention
        categorized_total = revenues - expenses
        global_total = self.manager.balance()
        uncategorized_effect = global_total - categorized_total

        net_income = revenues - expenses + uncategorized_effect
        return {
            "revenues": round(revenues, 2),
            "expenses": round(expenses, 2),
            "uncategorized_effect": round(uncategorized_effect, 2),
            "net_income": round(net_income, 2),
        }

    def balance_sheet(self) -> dict[str, float]:
        assets = self._sum_category_prefix("asset") + self._sum_category_prefix("activo")
        liabilities = abs(self._sum_category_prefix("liability")) + abs(self._sum_category_prefix("pasivo"))
        equity = self._sum_category_prefix("equity") + self._sum_category_prefix("capital")

        # retain earnings approximation from current performance
        net_income = self.income_statement()["net_income"]
        closing_equity = equity + net_income

        return {
            "assets": round(assets, 2),
            "liabilities": round(liabilities, 2),
            "equity": round(closing_equity, 2),
            "balance_check": round(assets - liabilities - closing_equity, 2),
        }

    def cash_flow_statement(self) -> dict[str, float]:
        operating = self._sum_category_prefix("operating") + self._sum_category_prefix("operacion")
        investing = self._sum_category_prefix("investing") + self._sum_category_prefix("inversion")
        financing = self._sum_category_prefix("financing") + self._sum_category_prefix("financiamiento")

        if operating == 0 and investing == 0 and financing == 0:
            operating = self.manager.balance()

        net_cash_change = operating + investing + financing
        return {
            "operating": round(operating, 2),
            "investing": round(investing, 2),
            "financing": round(financing, 2),
            "net_cash_change": round(net_cash_change, 2),
        }

    def full_report(self) -> str:
        income = self.income_statement()
        balance = self.balance_sheet()
        cash_flow = self.cash_flow_statement()

        return (
            "Estado de Resultados\n"
            f"- Ingresos: {income['revenues']:.2f}\n"
            f"- Gastos: {income['expenses']:.2f}\n"
            f"- Efecto no clasificado: {income['uncategorized_effect']:.2f}\n"
            f"- Utilidad neta: {income['net_income']:.2f}\n\n"
            "Balance General\n"
            f"- Activos: {balance['assets']:.2f}\n"
            f"- Pasivos: {balance['liabilities']:.2f}\n"
            f"- Capital contable: {balance['equity']:.2f}\n"
            f"- Diferencia (debe tender a 0): {balance['balance_check']:.2f}\n\n"
            "Estado de Flujo de Efectivo\n"
            f"- Operación: {cash_flow['operating']:.2f}\n"
            f"- Inversión: {cash_flow['investing']:.2f}\n"
            f"- Financiamiento: {cash_flow['financing']:.2f}\n"
            f"- Cambio neto de efectivo: {cash_flow['net_cash_change']:.2f}"
        )
