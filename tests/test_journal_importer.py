import csv
import tempfile
import unittest
from pathlib import Path

from finance_app.journal_importer import JournalTemplateImporter
from finance_app.transactions import TransactionManager


class JournalImporterTests(unittest.TestCase):
    def test_staging_preview_approve_post(self):
        importer = JournalTemplateImporter()
        manager = TransactionManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "journal.csv"
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=[
                        "batch_id", "company", "ledger", "journal", "posting_date", "document_date", "ref", "memo", "currency", "fx_rate_type", "supporting_doc_id", "line_no", "account_code", "partner", "debit", "credit", "amount_currency", "analytic_account", "tags", "tax_code", "due_date", "description",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "batch_id": "B001", "company": "MX01", "ledger": "LOCAL", "journal": "MISC", "posting_date": "2026-05-01", "document_date": "2026-05-01", "ref": "AJ-001", "memo": "Ajuste", "currency": "MXN", "fx_rate_type": "", "supporting_doc_id": "UUID-123", "line_no": "1", "account_code": "6000", "partner": "", "debit": "1000", "credit": "0", "amount_currency": "0", "analytic_account": "CC-01", "tags": "ifrs", "tax_code": "", "due_date": "", "description": "Gasto",
                })
                writer.writerow({
                    "batch_id": "B001", "company": "MX01", "ledger": "LOCAL", "journal": "MISC", "posting_date": "2026-05-01", "document_date": "2026-05-01", "ref": "AJ-001", "memo": "Ajuste", "currency": "MXN", "fx_rate_type": "", "supporting_doc_id": "UUID-123", "line_no": "2", "account_code": "1010", "partner": "", "debit": "0", "credit": "1000", "amount_currency": "0", "analytic_account": "CC-01", "tags": "ifrs", "tax_code": "", "due_date": "", "description": "Banco",
                })

            staging = importer.load_file(str(path))
            preview = staging.preview()
            self.assertEqual(len(staging.errors), 0)
            self.assertEqual(len(preview), 1)

            importer.approve(staging)
            importer.post(staging, manager)
            self.assertTrue(staging.posted)
            self.assertEqual(len(manager.transactions), 2)

    def test_validation_partner_required(self):
        importer = JournalTemplateImporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.csv"
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=[
                        "batch_id", "company", "ledger", "journal", "posting_date", "document_date", "ref", "memo", "currency", "fx_rate_type", "supporting_doc_id", "line_no", "account_code", "partner", "debit", "credit", "amount_currency", "analytic_account", "tags", "tax_code", "due_date", "description",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "batch_id": "B002", "company": "MX01", "ledger": "LOCAL", "journal": "MISC", "posting_date": "2026-05-02", "document_date": "2026-05-02", "ref": "AJ-002", "memo": "CxP", "currency": "MXN", "fx_rate_type": "", "supporting_doc_id": "", "line_no": "1", "account_code": "2101", "partner": "", "debit": "0", "credit": "500", "amount_currency": "0", "analytic_account": "", "tags": "", "tax_code": "", "due_date": "", "description": "CxP",
                })
                writer.writerow({
                    "batch_id": "B002", "company": "MX01", "ledger": "LOCAL", "journal": "MISC", "posting_date": "2026-05-02", "document_date": "2026-05-02", "ref": "AJ-002", "memo": "Gasto", "currency": "MXN", "fx_rate_type": "", "supporting_doc_id": "", "line_no": "2", "account_code": "6000", "partner": "", "debit": "500", "credit": "0", "amount_currency": "0", "analytic_account": "", "tags": "", "tax_code": "", "due_date": "", "description": "Gasto",
                })

            staging = importer.load_file(str(path))
            self.assertTrue(any("Partner obligatorio" in e.message for e in staging.errors))

    def test_threaded_parsing_and_bounded_idempotency_cache(self):
        importer = JournalTemplateImporter(parse_workers=2, idempotency_cache_size=1)
        manager = TransactionManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "journal_a.csv"
            path2 = Path(tmpdir) / "journal_b.csv"
            self._write_balanced_csv(path1, batch_id="BA", ref="AJ-A")
            self._write_balanced_csv(path2, batch_id="BB", ref="AJ-B")

            staging1 = importer.load_file(str(path1))
            importer.approve(staging1)
            importer.post(staging1, manager)

            staging2 = importer.load_file(str(path2))
            importer.approve(staging2)
            importer.post(staging2, manager)

        # Cache acotado para evitar crecimiento infinito en procesos de larga vida.
        self.assertLessEqual(len(importer._idempotency_keys), 1)

    def _write_balanced_csv(self, path: Path, batch_id: str, ref: str):
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "batch_id", "company", "ledger", "journal", "posting_date", "document_date", "ref", "memo", "currency", "fx_rate_type", "supporting_doc_id", "line_no", "account_code", "partner", "debit", "credit", "amount_currency", "analytic_account", "tags", "tax_code", "due_date", "description",
                ],
            )
            writer.writeheader()
            writer.writerow({
                "batch_id": batch_id, "company": "MX01", "ledger": "LOCAL", "journal": "MISC", "posting_date": "2026-05-10", "document_date": "2026-05-10", "ref": ref, "memo": "Ajuste", "currency": "MXN", "fx_rate_type": "", "supporting_doc_id": "", "line_no": "1", "account_code": "6000", "partner": "", "debit": "100", "credit": "0", "amount_currency": "0", "analytic_account": "", "tags": "", "tax_code": "", "due_date": "", "description": "Cargo",
            })
            writer.writerow({
                "batch_id": batch_id, "company": "MX01", "ledger": "LOCAL", "journal": "MISC", "posting_date": "2026-05-10", "document_date": "2026-05-10", "ref": ref, "memo": "Ajuste", "currency": "MXN", "fx_rate_type": "", "supporting_doc_id": "", "line_no": "2", "account_code": "1010", "partner": "", "debit": "0", "credit": "100", "amount_currency": "0", "analytic_account": "", "tags": "", "tax_code": "", "due_date": "", "description": "Abono",
            })


if __name__ == "__main__":
    unittest.main()
