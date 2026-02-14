import unittest
from datetime import date

from finance_app.intangibles_engine import (
    IntangibleAsset,
    IntangibleEvidence,
    IntangiblesEngine,
    IntangibleTransaction,
)


class IntangiblesEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = IntangiblesEngine()

    def test_research_expensed_and_development_capitalized_when_gate_passes(self):
        asset = IntangibleAsset(
            asset_id="INT-001",
            name="Plataforma",
            entity="MX01",
            profit_center="PC01",
            project="PRJ-RD",
            currency="MXN",
            useful_life_months=60,
        )
        evidence_ok = IntangibleEvidence(
            technical_feasibility=True,
            intent_to_complete=True,
            ability_to_use_or_sell=True,
            probable_future_benefits=True,
            resources_available=True,
            costs_reliably_measurable=True,
        )

        research_tx = IntangibleTransaction(
            tx_id="TX-R",
            tx_date=date(2026, 2, 1),
            amount=1000,
            phase="research",
            approved_for_capitalization=False,
        )
        development_tx = IntangibleTransaction(
            tx_id="TX-D",
            tx_date=date(2026, 3, 1),
            amount=2000,
            phase="development",
            approved_for_capitalization=True,
        )

        self.assertEqual(self.engine.classify_rd_cost(asset, research_tx, evidence_ok), "expense")
        self.assertEqual(self.engine.classify_rd_cost(asset, development_tx, evidence_ok), "capitalize")
        self.assertEqual(asset.expense_locked_amount, 1000)
        self.assertEqual(asset.gross_carrying_amount, 2000)

    def test_amortization_schedule_and_rollforward(self):
        asset = IntangibleAsset(
            asset_id="INT-002",
            name="Licencia",
            entity="MX01",
            profit_center="PC02",
            project="PRJ-ERP",
            currency="MXN",
            useful_life_months=10,
            gross_carrying_amount=1000,
        )

        schedule = self.engine.simulate_amortization_schedule(asset, periods=3)
        self.assertEqual(schedule, [100.0, 100.0, 100.0])

        roll = self.engine.build_rollforward(
            opening_gross=1000,
            additions=200,
            disposals=0,
            amortization=300,
            impairment=50,
        )
        self.assertEqual(roll.closing_carrying_amount, 850)

    def test_saas_classification_defaults_to_expense(self):
        self.assertEqual(self.engine.classify_saas_or_website_cost(False, False), "expense")
        self.assertEqual(self.engine.classify_saas_or_website_cost(True, False), "capitalize")
        self.assertEqual(self.engine.classify_saas_or_website_cost(True, True), "expense")

    def test_indefinite_life_impairment_flow(self):
        asset = IntangibleAsset(
            asset_id="INT-003",
            name="Marca",
            entity="MX01",
            profit_center="PC03",
            project="PRJ-BRAND",
            currency="MXN",
            useful_life_months=None,
            gross_carrying_amount=5000,
        )

        self.assertTrue(asset.requires_annual_impairment_test())
        self.assertEqual(self.engine.amortization_for_period(asset), 0.0)
        impairment = self.engine.run_annual_impairment_test(asset, recoverable_amount=4200)
        self.assertEqual(impairment, 800.0)


if __name__ == "__main__":
    unittest.main()
