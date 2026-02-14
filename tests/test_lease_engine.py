import unittest

from finance_app.lease_engine import (
    LeaseContract,
    LeaseDiscountRate,
    LeaseEngine,
    LeaseRemeasurementResult,
    LeaseModification,
    LeasePaymentSchedule,
    remeasure_contract,
)
from finance_app.transactions import TransactionManager


class LeaseEngineTests(unittest.TestCase):
    def test_initial_measurement_schedule_and_posting(self):
        manager = TransactionManager()
        engine = LeaseEngine(manager)

        contract = LeaseContract(
            contract_id="LEASE-001",
            company="MX01",
            ledger_policy_ids=["LOCAL", "IFRS"],
            counterparty="ARRENDADORA SA",
            asset_class="vehiculos",
            commencement_date="2026-01-01",
            end_date="2026-12-31",
            payments=[
                LeasePaymentSchedule("2026-01-31", 1000, "MXN"),
                LeasePaymentSchedule("2026-02-28", 1000, "MXN"),
                LeasePaymentSchedule("2026-03-31", 1000, "MXN"),
            ],
        )
        rate = LeaseDiscountRate("IBR", "MXN", 12, 0.12, "treasury", "2026-01-01")

        snap = engine.initial_measurement(contract, rate, "2026-01-01")
        schedule = engine.amortization_schedule(contract, snap, rate)
        engine.validate_schedule_consistency(snap, schedule)
        batch = engine.post_period(contract, schedule[0], "IFRS")

        self.assertGreater(snap.lease_liability_pv, 0)
        self.assertEqual(len(schedule), 3)
        self.assertEqual(batch.status, "posted")
        self.assertGreater(len(manager.transactions), 0)

    def test_remeasurement(self):
        manager = TransactionManager()
        engine = LeaseEngine(manager)

        contract = LeaseContract(
            contract_id="LEASE-002",
            company="MX01",
            ledger_policy_ids=["IFRS"],
            counterparty="ARRENDADORA SA",
            asset_class="inmuebles",
            commencement_date="2026-01-01",
            end_date="2026-12-31",
            payments=[
                LeasePaymentSchedule("2026-01-31", 3000, "MXN"),
                LeasePaymentSchedule("2026-02-28", 3000, "MXN"),
            ],
        )
        rate = LeaseDiscountRate("IBR", "MXN", 24, 0.10, "treasury", "2026-01-01")
        mod = LeaseModification(
            contract_id="LEASE-002",
            reason="index_change",
            effective_date="2026-03-01",
            new_payments=[
                LeasePaymentSchedule("2026-03-31", 3300, "MXN"),
                LeasePaymentSchedule("2026-04-30", 3300, "MXN"),
            ],
        )

        new_snap = remeasure_contract(engine, contract, rate, mod)
        self.assertEqual(new_snap.remeasurement_reason, "index_change")
        self.assertGreater(new_snap.lease_liability_pv, 0)

    def test_schedule_consistency_detects_mismatch(self):
        manager = TransactionManager()
        engine = LeaseEngine(manager)

        contract = LeaseContract(
            contract_id="LEASE-003",
            company="MX01",
            ledger_policy_ids=["IFRS"],
            counterparty="ARRENDADORA SA",
            asset_class="equipo",
            commencement_date="2026-01-01",
            end_date="2026-12-31",
            payments=[
                LeasePaymentSchedule("2026-01-31", 1000, "MXN"),
                LeasePaymentSchedule("2026-02-28", 1000, "MXN"),
            ],
        )
        rate = LeaseDiscountRate("IBR", "MXN", 12, 0.12, "treasury", "2026-01-01")

        snap = engine.initial_measurement(contract, rate, "2026-01-01")
        schedule = engine.amortization_schedule(contract, snap, rate)
        # Introduce a manual corruption.
        schedule[-1].closing_liability += 100

        with self.assertRaises(ValueError):
            engine.validate_schedule_consistency(snap, schedule)

    def test_remeasurement_with_history(self):
        manager = TransactionManager()
        engine = LeaseEngine(manager)

        contract = LeaseContract(
            contract_id="LEASE-004",
            company="MX01",
            ledger_policy_ids=["IFRS"],
            counterparty="ARRENDADORA SA",
            asset_class="inmuebles",
            commencement_date="2026-01-01",
            end_date="2026-12-31",
            initial_direct_costs=150,
            payments=[
                LeasePaymentSchedule("2026-01-31", 2500, "MXN"),
                LeasePaymentSchedule("2026-02-28", 2500, "MXN"),
            ],
        )
        rate = LeaseDiscountRate("IBR", "MXN", 12, 0.10, "treasury", "2026-01-01")
        previous = engine.initial_measurement(contract, rate, "2026-01-01")
        mod = LeaseModification(
            contract_id="LEASE-004",
            reason="extension",
            effective_date="2026-03-01",
            new_payments=[
                LeasePaymentSchedule("2026-03-31", 2700, "MXN"),
                LeasePaymentSchedule("2026-04-30", 2700, "MXN"),
                LeasePaymentSchedule("2026-05-31", 2700, "MXN"),
            ],
        )

        result = engine.remeasure_with_history(contract, previous, rate, mod)
        self.assertIsInstance(result, LeaseRemeasurementResult)
        self.assertEqual(result.previous_snapshot.contract_id, "LEASE-004")
        self.assertNotEqual(result.delta_liability, 0.0)


if __name__ == "__main__":
    unittest.main()
