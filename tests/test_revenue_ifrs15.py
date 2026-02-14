import unittest

from finance_app.revenue_ifrs15 import PerformanceObligation, RevenueContract, RevenueEngineIFRS15


class RevenueIFRS15Tests(unittest.TestCase):
    def setUp(self):
        self.engine = RevenueEngineIFRS15()

    def test_allocation_and_recognition_principal_vs_agent(self):
        pob1 = PerformanceObligation(
            pob_id="POB-1",
            description="Licencia",
            standalone_selling_price=700,
            recognition_pattern="point_in_time",
            role="principal",
        )
        pob2 = PerformanceObligation(
            pob_id="POB-2",
            description="Implementación third-party",
            standalone_selling_price=300,
            recognition_pattern="over_time",
            role="agent",
        )
        contract = RevenueContract(
            contract_id="CTR-001",
            customer="Cliente A",
            transaction_price=1000,
            pobs=[pob1, pob2],
            variable_consideration_estimate=100,
            variable_consideration_constraint=20,
        )

        alloc = self.engine.allocate_transaction_price(contract)
        self.assertEqual(alloc["POB-1"], 756.0)
        self.assertEqual(alloc["POB-2"], 324.0)

        lines = self.engine.recognize_revenue(
            contract,
            progress_by_pob={"POB-1": 1.0, "POB-2": 0.5},
            agent_commission_rate=0.2,
        )
        by_id = {l.pob_id: l for l in lines}

        self.assertEqual(by_id["POB-1"].recognized_gross, 756.0)
        self.assertEqual(by_id["POB-1"].recognized_net, 756.0)
        self.assertEqual(by_id["POB-2"].recognized_gross, 162.0)
        self.assertEqual(by_id["POB-2"].recognized_net, 32.4)

    def test_contract_rollforward_and_classifications(self):
        roll = self.engine.compute_contract_rollforward(
            opening_contract_asset=50,
            opening_contract_liability=10,
            billed_amount=80,
            recognized_revenue=20,
        )
        self.assertEqual(roll.closing_contract_asset, 0.0)
        self.assertEqual(roll.closing_contract_liability, 20.0)

        self.assertEqual(self.engine.classify_warranty(True), "service_type_pob")
        self.assertEqual(self.engine.classify_warranty(False), "assurance")
        self.assertEqual(self.engine.classify_license(True), "right_to_access")
        self.assertEqual(self.engine.classify_license(False), "right_to_use")


if __name__ == "__main__":
    unittest.main()
