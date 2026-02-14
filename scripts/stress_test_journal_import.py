"""Stress test for journal import pipeline.

Generates large CSV batches and benchmarks sequential vs threaded parsing.
"""

from __future__ import annotations

import argparse
import csv
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finance_app.journal_importer import JournalTemplateImporter
from finance_app.transactions import TransactionManager


def generate_csv(path: Path, entries: int) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "batch_id", "company", "ledger", "journal", "posting_date", "document_date", "ref", "memo",
                "currency", "fx_rate_type", "supporting_doc_id", "line_no", "account_code", "partner",
                "debit", "credit", "amount_currency", "analytic_account", "tags", "tax_code", "due_date", "description",
            ],
        )
        writer.writeheader()
        for idx in range(entries):
            batch = f"B{idx:06d}"
            writer.writerow(
                {
                    "batch_id": batch,
                    "company": "MX01",
                    "ledger": "LOCAL",
                    "journal": "MISC",
                    "posting_date": "2026-06-30",
                    "document_date": "2026-06-30",
                    "ref": f"AJ-{idx:06d}",
                    "memo": "Stress",
                    "currency": "MXN",
                    "fx_rate_type": "",
                    "supporting_doc_id": "",
                    "line_no": "1",
                    "account_code": "6000",
                    "partner": "",
                    "debit": "100.0",
                    "credit": "0",
                    "amount_currency": "0",
                    "analytic_account": "",
                    "tags": "",
                    "tax_code": "",
                    "due_date": "",
                    "description": "Cargo",
                }
            )
            writer.writerow(
                {
                    "batch_id": batch,
                    "company": "MX01",
                    "ledger": "LOCAL",
                    "journal": "MISC",
                    "posting_date": "2026-06-30",
                    "document_date": "2026-06-30",
                    "ref": f"AJ-{idx:06d}",
                    "memo": "Stress",
                    "currency": "MXN",
                    "fx_rate_type": "",
                    "supporting_doc_id": "",
                    "line_no": "2",
                    "account_code": "1010",
                    "partner": "",
                    "debit": "0",
                    "credit": "100.0",
                    "amount_currency": "0",
                    "analytic_account": "",
                    "tags": "",
                    "tax_code": "",
                    "due_date": "",
                    "description": "Abono",
                }
            )


def run_benchmark(path: Path, workers: int) -> tuple[float, int]:
    importer = JournalTemplateImporter(parse_workers=workers)
    manager = TransactionManager()

    t0 = time.perf_counter()
    staging = importer.load_file(str(path))
    if staging.errors:
        raise RuntimeError(f"Staging has {len(staging.errors)} validation errors")
    importer.approve(staging)
    importer.post(staging, manager)
    elapsed = time.perf_counter() - t0
    return elapsed, len(manager.transactions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test journal importer with large CSV files")
    parser.add_argument("--entries", type=int, default=50_000, help="Number of policies (each has 2 lines)")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "stress_journal.csv"
        generate_csv(path, args.entries)

        seq_time, seq_tx = run_benchmark(path, workers=1)
        thr_time, thr_tx = run_benchmark(path, workers=4)

    print(f"Entries: {args.entries:,} | Transactions: {seq_tx:,}")
    print(f"Sequential (1 worker): {seq_time:.3f}s")
    print(f"Threaded (4 workers): {thr_time:.3f}s")
    if thr_time > 0:
        print(f"Speedup: {seq_time / thr_time:.2f}x")


if __name__ == "__main__":
    main()
