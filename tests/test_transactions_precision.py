import unittest
from datetime import date
from decimal import Decimal

from finance_app.transactions import FinancialTransaction, PolicyLine, TransactionManager, sanitize_money


class TransactionsPrecisionTests(unittest.TestCase):
    def test_financial_transaction_decimal_and_non_zero(self):
        tx = FinancialTransaction(
            transaction_id="TX-1",
            transaction_date=date(2026, 1, 1),
            amount=Decimal("100.129"),
            ledger_type="IFRS",
            is_accrual=True,
        )
        self.assertEqual(tx.amount, Decimal("100.13"))


    def test_sanitize_money_rejects_float(self):
        with self.assertRaises(TypeError):
            sanitize_money(10.5)

    def test_policy_posting_balances_with_decimal_guard(self):
        manager = TransactionManager()
        lines = [
            PolicyLine("P1", "2026-01-01", "Cargo", "6000", 100.005, 0),
            PolicyLine("P1", "2026-01-01", "Abono", "1000", 0, 100.005),
        ]
        summary = manager.post_policy_lines(lines)
        self.assertEqual(summary.policies_posted, 1)
        self.assertEqual(summary.lines_posted, 2)


if __name__ == "__main__":
    unittest.main()
