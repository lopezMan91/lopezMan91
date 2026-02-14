import unittest
from decimal import Decimal

from finance_app.gaap_router import (
    AccountingStandard,
    AssetRevaluationRouter,
    LedgerContext,
    run_monthly_depreciation_by_ledger,
)


class GaapRouterTests(unittest.TestCase):
    def test_revaluation_applies_only_ifrs_layer(self):
        router = AssetRevaluationRouter()
        ledgers = [
            LedgerContext("L01", "Local", AccountingStandard.NIF_MX),
            LedgerContext("L02", "IFRS", AccountingStandard.IFRS),
            LedgerContext("L03", "US", AccountingStandard.US_GAAP),
        ]
        impacts = router.process_revaluation(
            ledgers=ledgers,
            current_book_values={"L01": Decimal("100"), "L02": Decimal("100"), "L03": Decimal("100")},
            new_fair_value=Decimal("150"),
            tax_basis_by_ledger={"L02": Decimal("100")},
        )
        by_standard = {impact.standard: impact for impact in impacts}
        self.assertEqual(by_standard[AccountingStandard.NIF_MX].action, "SKIPPED_RULE_VIOLATION")
        self.assertEqual(by_standard[AccountingStandard.US_GAAP].action, "SKIPPED_RULE_VIOLATION")
        self.assertEqual(by_standard[AccountingStandard.IFRS].action, "SUCCESS")
        self.assertIsNotNone(by_standard[AccountingStandard.IFRS].deferred_tax)

    def test_monthly_depreciation_by_ledger(self):
        values = run_monthly_depreciation_by_ledger(
            {"L01": Decimal("1000"), "L02": Decimal("1200")},
            remaining_life_months=10,
        )
        self.assertEqual(values["L01"], Decimal("100.00"))
        self.assertEqual(values["L02"], Decimal("120.00"))


if __name__ == "__main__":
    unittest.main()
