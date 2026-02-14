import unittest

from finance_app.financial_statements import FinancialStatements
from finance_app.transactions import Transaction, TransactionManager


class FinancialStatementsTests(unittest.TestCase):
    def test_income_statement(self):
        manager = TransactionManager()
        manager.add_transaction(Transaction('2026-01-01', 'Venta A', 1000.0, 'revenue:sales'))
        manager.add_transaction(Transaction('2026-01-02', 'Renta', -400.0, 'expense:rent'))

        statements = FinancialStatements(manager)
        income = statements.income_statement()

        self.assertEqual(income['revenues'], 1000.0)
        self.assertEqual(income['expenses'], 400.0)
        self.assertEqual(income['net_income'], 600.0)

    def test_balance_sheet_and_cash_flow(self):
        manager = TransactionManager()
        manager.add_transaction(Transaction('2026-01-01', 'Caja inicial', 5000.0, 'asset:cash'))
        manager.add_transaction(Transaction('2026-01-02', 'Prestamo', -2000.0, 'liability:loan'))
        manager.add_transaction(Transaction('2026-01-03', 'Aporte', 1000.0, 'equity:capital'))
        manager.add_transaction(Transaction('2026-01-04', 'Operacion neta', 300.0, 'operating:net'))

        statements = FinancialStatements(manager)
        balance = statements.balance_sheet()
        cash = statements.cash_flow_statement()

        self.assertEqual(balance['assets'], 5000.0)
        self.assertEqual(balance['liabilities'], 2000.0)
        self.assertEqual(cash['operating'], 300.0)
        self.assertEqual(cash['net_cash_change'], 300.0)


if __name__ == '__main__':
    unittest.main()
