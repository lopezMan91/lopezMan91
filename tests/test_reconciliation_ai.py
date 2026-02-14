import unittest

from finance_app.reconciliation import (
    BankStatementLine,
    LedgerLine,
    suggest_fuzzy_matches,
)
from finance_app.smart_classification import suggest_account_and_cost_center


class ReconciliationAndAISuggestionTests(unittest.TestCase):
    def test_fuzzy_match_suggests_expected_pair(self):
        bank = [
            BankStatementLine("B1", "2026-06-01", "PAGO TELMEX INTERNET", 1500.0),
        ]
        ledger = [
            LedgerLine("L1", "2026-06-01", "Pago Telmex Internet Junio", 1500.0),
            LedgerLine("L2", "2026-06-01", "Pago Proveedor X", 1499.0),
        ]

        matches = suggest_fuzzy_matches(bank, ledger, amount_tolerance=1.5, min_score=0.70)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].ledger_line_id, "L1")

    def test_nlp_style_suggestion_by_keyword(self):
        suggestion = suggest_account_and_cost_center("Pago de renta de oficina corporativa")
        self.assertEqual(suggestion.account_code, "6105")
        self.assertEqual(suggestion.cost_center, "CC-ADM")
        self.assertGreater(suggestion.confidence, 0.8)


if __name__ == "__main__":
    unittest.main()
