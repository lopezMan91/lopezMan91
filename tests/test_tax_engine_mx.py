import unittest
from decimal import Decimal

from finance_app.tax_engine_mx import (
    DeferredTaxCalculator,
    FiscalLine,
    TaxAssetEngine,
    TaxEngineMX,
    TaxEvidencePack,
    TaxLineAttributes,
    TaxLossCarryforward,
    TaxRateProvider,
    TemporaryDifference,
    compute_dta_from_tax_losses,
)


class TaxEngineMXTests(unittest.TestCase):
    def setUp(self):
        self.engine = TaxEngineMX(rate_provider=TaxRateProvider(rates={"IVA_GENERAL": Decimal("0.16"), "ISR_CORPORATE": Decimal("0.30"), "PTU_MONTHS_CAP": Decimal("3")}))

    def test_iva_summary_with_blocked_lines_and_diot(self):
        complete = TaxEvidencePack(xml_attached=True, pdf_attached=True, payment_proof_attached=True)
        incomplete = TaxEvidencePack(xml_attached=True, pdf_attached=False, payment_proof_attached=False)
        lines = [
            FiscalLine(
                line_id="L1",
                vendor_rfc="AAA010101AAA",
                concept="Servicio gravado",
                base_amount=Decimal("1000"),
                attrs=TaxLineAttributes(
                    iva_kind="16",
                    iva_creditable=True,
                    withheld_iva_rate=0.106667,
                    withheld_isr_rate=0.1,
                    evidence=complete,
                ),
            ),
            FiscalLine(
                line_id="L2",
                vendor_rfc="BBB010101BBB",
                concept="Servicio sin evidencia completa",
                base_amount=Decimal("500"),
                attrs=TaxLineAttributes(
                    iva_kind="16",
                    iva_creditable=True,
                    evidence=incomplete,
                ),
            ),
        ]

        result = self.engine.compute_iva_summary(lines)
        self.assertEqual(result.transferred_iva, Decimal("240.00"))
        self.assertEqual(result.creditable_iva, Decimal("160.00"))
        self.assertEqual(result.non_creditable_iva, Decimal("80.00"))
        self.assertEqual(result.withheld_iva, Decimal("106.67"))
        self.assertEqual(result.withheld_isr, Decimal("100.00"))
        self.assertEqual(result.diot_by_vendor["AAA010101AAA"], Decimal("1000.00"))
        self.assertIn("L2", result.blocked_lines)

    def test_isr_reconciliation(self):
        result = self.engine.compute_isr_reconciliation(
            accounting_profit=100000,
            permanent_add_backs=5000,
            permanent_deductions=2000,
            temporary_add_backs=1000,
            temporary_deductions=3000,
        )
        self.assertEqual(result.taxable_profit, 101000)

    def test_ptu_cap_rule(self):
        # Debe aplicar el más favorable para el trabajador
        cap = self.engine.compute_ptu_legal_cap(monthly_salary=20000, avg_ptu_last_3_years=45000)
        self.assertEqual(cap, 60000)
        paid = self.engine.compute_ptu_legal_for_employee(
            proportional_amount=70000,
            monthly_salary=20000,
            avg_ptu_last_3_years=45000,
        )
        self.assertEqual(paid, 60000)

    def test_deferred_tax_totals(self):
        differences = [
            TemporaryDifference(code="FA_DEP", carrying_amount=12000, tax_base=9000, tax_rate=0.3),
            TemporaryDifference(code="PROV", carrying_amount=5000, tax_base=7000, tax_rate=0.3),
        ]
        totals = self.engine.compute_deferred_tax_totals(differences)
        self.assertEqual(totals["dtl_total"], 900.0)
        self.assertEqual(totals["dta_total"], 600.0)
        self.assertEqual(totals["net_deferred_tax"], 300.0)
        self.assertEqual(totals["movement_count"], 2)

    def test_deferred_tax_policy_lines_generation(self):
        differences = [
            TemporaryDifference(code="ROU", carrying_amount=10000, tax_base=7000, tax_rate=0.3),
        ]
        lines = self.engine.build_deferred_tax_policy_lines(
            policy_id="DT-001",
            posting_date="2026-12-31",
            differences=differences,
            ledger_tag="ledger_ifrs",
        )
        self.assertEqual(len(lines), 2)
        self.assertEqual(round(sum(l.debit for l in lines), 2), round(sum(l.credit for l in lines), 2))



    def test_configurable_tax_rates_provider(self):
        provider = TaxRateProvider(rates={"IVA_GENERAL": Decimal("0.15")})
        engine = TaxEngineMX(rate_provider=provider)
        complete = TaxEvidencePack(xml_attached=True, pdf_attached=True, payment_proof_attached=True)
        lines = [
            FiscalLine(
                line_id="L1",
                vendor_rfc="AAA010101AAA",
                concept="Servicio gravado",
                base_amount=Decimal("1000"),
                attrs=TaxLineAttributes(iva_kind="16", iva_creditable=True, evidence=complete),
            )
        ]
        result = engine.compute_iva_summary(lines)
        self.assertEqual(result.transferred_iva, Decimal("150.00"))

    def test_deferred_tax_calculator_layered_impact(self):
        calc = DeferredTaxCalculator(tax_rate=Decimal("0.30"))
        result = calc.calculate_nif_d4_impact(Decimal("150.00"), Decimal("100.00"))
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.type, "DTL")
        self.assertEqual(result.deferred_tax, Decimal("15.00"))
        self.assertEqual(result.ledger_target, "IFRS_ADJUSTMENTS")

    def test_inpc_tax_deduction(self):
        deduction = TaxAssetEngine.calculate_tax_deduction(
            moi=Decimal("1000000"),
            inpc_acquisition=Decimal("120.0"),
            inpc_current=Decimal("132.0"),
            rate=Decimal("0.10"),
        )
        self.assertEqual(deduction, Decimal("110000.00"))

    def test_dta_from_tax_losses_requires_probability(self):
        losses = [TaxLossCarryforward(2024, 500000), TaxLossCarryforward(2025, 300000)]
        dta = compute_dta_from_tax_losses(losses, isr_rate=0.30, probable_future_profit=True)
        self.assertEqual(dta, 240000.0)
        dta_blocked = compute_dta_from_tax_losses(losses, isr_rate=0.30, probable_future_profit=False)
        self.assertEqual(dta_blocked, 0.0)


if __name__ == "__main__":
    unittest.main()
