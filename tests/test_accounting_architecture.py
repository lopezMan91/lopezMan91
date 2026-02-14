import unittest

from finance_app.accounting_core import AccountingEngine, AccountingPolicy, BusinessEvent, verify_entry_integrity
from finance_app.control_framework import default_control_library
from finance_app.fiscal_compliance import FiscalDocument, FiscalVault
from finance_app.reconciliation import ReconciliationItem, ReconciliationWorkflow
from finance_app.report_builder import FinancialStatementBuilder, default_templates
from finance_app.transactions import TransactionManager


class AccountingArchitectureTests(unittest.TestCase):
    def test_event_to_multiledger_posting(self):
        manager = TransactionManager()
        engine = AccountingEngine(manager)

        event = BusinessEvent(
            event_id="EV-001",
            event_type="supplier_invoice",
            source_ref="INV-7788",
            company="MX01",
            currency="MXN",
            occurred_at="2026-03-01",
            payload={"base": 1000, "vat": 160, "total": 1160},
        )
        policies = [
            AccountingPolicy(
                version="v1",
                event_type="supplier_invoice",
                ledger_code="LOCAL",
                line_rules=[
                    {"account": "6000", "debit": "payload.base", "credit": "0", "description": "Gasto"},
                    {"account": "1180", "debit": "payload.vat", "credit": "0", "description": "IVA acreditable"},
                    {"account": "2010", "debit": "0", "credit": "payload.total", "description": "CxP"},
                ],
            ),
            AccountingPolicy(
                version="v1",
                event_type="supplier_invoice",
                ledger_code="IFRS",
                line_rules=[
                    {"account": "6100", "debit": "payload.base", "credit": "0", "description": "Expense IFRS"},
                    {"account": "2100", "debit": "0", "credit": "payload.base", "description": "AP IFRS"},
                ],
            ),
        ]

        run = engine.post_event(event, policies)

        self.assertEqual(run.event_id, "EV-001")
        self.assertEqual(len(engine.entries), 2)
        self.assertTrue(all(verify_entry_integrity(entry) for entry in engine.entries))
        self.assertEqual(len(manager.transactions), 5)

        # Tamper detection check.
        engine.entries[0].lines[0].debit += 1
        self.assertFalse(verify_entry_integrity(engine.entries[0]))

    def test_fiscal_vault_gates(self):
        vault = FiscalVault()
        vault.ingest_document(FiscalDocument(
            uuid="UUID-1",
            rfc_emisor="AAA010101AAA",
            rfc_receptor="BBB010101BBB",
            total=1160,
            xml_content="<cfdi>ok</cfdi>",
            sat_status="vigente",
        ))
        vault.link_policy_uuid("EV-001-LOCAL", "UUID-1", "EV-001")
        self.assertEqual(vault.verify_closing_gates(), [])

    def test_fiscal_vault_lco_efos_gates(self):
        vault = FiscalVault()
        vault.ingest_document(FiscalDocument(
            uuid="UUID-2",
            rfc_emisor="CCC010101CCC",
            rfc_receptor="DDD010101DDD",
            total=100,
            xml_content="<cfdi>risk</cfdi>",
            sat_status="vigente",
            listed_in_lco=False,
            listed_in_efos=True,
        ))
        vault.link_policy_uuid("EV-009-LOCAL", "UUID-2", "EV-009")
        issues = vault.verify_closing_gates()
        self.assertTrue(any("LCO" in issue for issue in issues))
        self.assertTrue(any("EFOS" in issue for issue in issues))

    def test_reporting_and_controls_and_reconciliation(self):
        manager = TransactionManager()
        engine = AccountingEngine(manager)
        event = BusinessEvent(
            event_id="EV-002",
            event_type="sale",
            source_ref="INV-900",
            company="MX01",
            currency="MXN",
            occurred_at="2026-03-05",
            payload={"amount": 500},
        )
        policies = [
            AccountingPolicy(
                version="v1",
                event_type="sale",
                ledger_code="IFRS",
                line_rules=[
                    {"account": "4001", "debit": "0", "credit": "payload.amount", "description": "Revenue"},
                    {"account": "1101", "debit": "payload.amount", "credit": "0", "description": "AR"},
                ],
            ),
        ]
        engine.post_event(event, policies)

        builder = FinancialStatementBuilder(default_templates())
        report = builder.build("PL_IFRS", manager.transactions)
        self.assertIn("Ingresos", report.sections)

        lib = default_control_library()
        sod_issues = lib.evaluate_user_roles(["vendor_create", "payment_approve"])
        self.assertEqual(len(sod_issues), 1)

        wf = ReconciliationWorkflow("prep", "rev", "app")
        wf.add_item(ReconciliationItem("AP", 1000, 1000))
        wf.add_item(ReconciliationItem("AR", 500, 480))
        issues = wf.run()
        self.assertEqual(len(issues), 1)


if __name__ == "__main__":
    unittest.main()
