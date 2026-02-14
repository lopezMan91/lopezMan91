from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Literal
from decimal import Decimal, ROUND_HALF_UP

from .policy_import import _read_xlsx_rows
from .transactions import PolicyLine, TransactionManager


@dataclass
class JournalImportRow:
    batch_id: str
    company: str
    ledger: str
    journal: str
    posting_date: str
    document_date: str
    ref: str
    memo: str
    currency: str
    fx_rate_type: str
    supporting_doc_id: str
    line_no: int
    account_code: str
    partner: str
    debit: Decimal
    credit: Decimal
    amount_currency: Decimal
    analytic_account: str
    tags: str
    tax_code: str
    due_date: str
    description: str


@dataclass
class JournalValidationError:
    row_number: int
    message: str


@dataclass
class JournalImportStaging:
    import_id: str
    file_hash: str
    rows: list[JournalImportRow]
    errors: list[JournalValidationError] = field(default_factory=list)
    approved: bool = False
    posted: bool = False

    def preview(self) -> dict[str, dict[str, Decimal | int]]:
        grouped: dict[str, dict[str, Decimal | int]] = {}
        for row in self.rows:
            key = f"{row.batch_id}|{row.ref}|{row.posting_date}"
            bucket = grouped.setdefault(key, {"debit": Decimal("0.00"), "credit": Decimal("0.00"), "lines": 0})
            bucket["debit"] += row.debit
            bucket["credit"] += row.credit
            bucket["lines"] += 1
        return grouped


class JournalTemplateImporter:
    def __init__(self, parse_workers: int = 1, idempotency_cache_size: int = 10_000):
        self.parse_workers = max(1, parse_workers)
        self.idempotency_cache_size = max(1, idempotency_cache_size)
        # Bounded cache avoids unbounded memory growth in long-running processes.
        self._idempotency_keys: OrderedDict[str, None] = OrderedDict()

    def load_file(self, path: str) -> JournalImportStaging:
        ext = Path(path).suffix.lower()
        if ext == ".csv":
            rows = self._read_csv_rows(path)
        elif ext == ".xlsx":
            rows = _read_xlsx_rows(path)
        else:
            raise ValueError("Formato no soportado para importación de pólizas")

        parsed: list[JournalImportRow] = []
        errors: list[JournalValidationError] = []
        indexed_rows = list(enumerate(rows, start=2))
        if self.parse_workers == 1:
            for i, row in indexed_rows:
                try:
                    parsed.append(self._parse_row(row))
                except Exception as exc:
                    errors.append(JournalValidationError(i, str(exc)))
        else:
            # CPU-light but high-volume parsing can benefit from thread fan-out.
            with ThreadPoolExecutor(max_workers=self.parse_workers) as executor:
                for i, result, err in executor.map(self._parse_row_safe, indexed_rows):
                    if err:
                        errors.append(JournalValidationError(i, err))
                    elif result is not None:
                        parsed.append(result)

        file_hash = self._calculate_file_hash(path)
        staging = JournalImportStaging(import_id=f"IMP-{file_hash[:12]}", file_hash=file_hash, rows=parsed, errors=errors)
        staging.errors.extend(self._validate(parsed))
        return staging

    def approve(self, staging: JournalImportStaging):
        if staging.errors:
            raise ValueError("No se puede aprobar staging con errores")
        staging.approved = True

    def post(self, staging: JournalImportStaging, manager: TransactionManager):
        if not staging.approved:
            raise ValueError("Staging no aprobado")
        if staging.posted:
            raise ValueError("Staging ya posteado")

        lines: list[PolicyLine] = []
        grouped: dict[str, list[JournalImportRow]] = {}
        for row in staging.rows:
            key = f"{row.batch_id}|{row.ref}|{row.posting_date}|{row.ledger}"
            grouped.setdefault(key, []).append(row)

        for key, rows in grouped.items():
            if key in self._idempotency_keys:
                continue
            first = rows[0]
            policy_id = f"{first.batch_id}-{first.ref}-{first.posting_date}-{first.ledger}"
            for row in rows:
                lines.append(PolicyLine(
                    policy_id=policy_id,
                    date=row.posting_date,
                    description=row.description or row.memo,
                    account=row.account_code,
                    debit=row.debit,
                    credit=row.credit,
                    category=f"ledger_{row.ledger.lower()}:{row.account_code}",
                ))
            self._remember_idempotency_key(key)

        if not lines:
            raise ValueError("No hay líneas nuevas para postear")
        manager.post_policy_lines(lines)
        staging.posted = True

    def _remember_idempotency_key(self, key: str):
        self._idempotency_keys[key] = None
        self._idempotency_keys.move_to_end(key)
        while len(self._idempotency_keys) > self.idempotency_cache_size:
            self._idempotency_keys.popitem(last=False)

    def _validate(self, rows: list[JournalImportRow]) -> list[JournalValidationError]:
        errors: list[JournalValidationError] = []
        grouped: dict[str, tuple[Decimal, Decimal, str]] = {}
        valid_ledgers = {"LOCAL", "IFRS", "CONSOLIDATION", "ELIMINATIONS"}

        for i, row in enumerate(rows, start=2):
            if row.ledger not in valid_ledgers:
                errors.append(JournalValidationError(i, f"Ledger inválido: {row.ledger}"))
            if not row.account_code:
                errors.append(JournalValidationError(i, "Cuenta contable vacía"))
            if row.account_code.startswith("21") and not row.partner:
                errors.append(JournalValidationError(i, "Partner obligatorio para cuentas 21xx"))
            if row.currency and row.currency != "MXN" and not row.fx_rate_type:
                errors.append(JournalValidationError(i, "Tipo de cambio faltante"))

            key = f"{row.batch_id}|{row.ref}|{row.posting_date}|{row.ledger}"
            debit, credit, first_row = grouped.get(key, (Decimal("0.00"), Decimal("0.00"), str(i)))
            grouped[key] = (debit + row.debit, credit + row.credit, first_row)

        for key, (debit, credit, first_row) in grouped.items():
            if (debit - credit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) != Decimal("0.00"):
                errors.append(JournalValidationError(int(first_row), f"Póliza desbalanceada {key}: {debit} vs {credit}"))

        return errors

    def _parse_row(self, row: dict[str, str]) -> JournalImportRow:
        def req(field: str) -> str:
            value = str(row.get(field, "")).strip()
            if not value:
                raise ValueError(f"Campo obligatorio vacío: {field}")
            return value

        def opt(field: str, default: str = "") -> str:
            return str(row.get(field, default)).strip()

        return JournalImportRow(
            batch_id=req("batch_id"),
            company=req("company"),
            ledger=req("ledger").upper(),
            journal=req("journal"),
            posting_date=req("posting_date"),
            document_date=opt("document_date", req("posting_date")),
            ref=req("ref"),
            memo=opt("memo"),
            currency=opt("currency", "MXN").upper(),
            fx_rate_type=opt("fx_rate_type"),
            supporting_doc_id=opt("supporting_doc_id"),
            line_no=int(opt("line_no", "1")),
            account_code=req("account_code"),
            partner=opt("partner"),
            debit=_money(opt("debit", "0")),
            credit=_money(opt("credit", "0")),
            amount_currency=_money(opt("amount_currency", "0")),
            analytic_account=opt("analytic_account"),
            tags=opt("tags"),
            tax_code=opt("tax_code"),
            due_date=opt("due_date"),
            description=opt("description", opt("memo")),
        )

    def _parse_row_safe(self, indexed_row: tuple[int, dict[str, str]]) -> tuple[int, JournalImportRow | None, str | None]:
        row_number, row = indexed_row
        try:
            return row_number, self._parse_row(row), None
        except Exception as exc:
            return row_number, None, str(exc)

    def _read_csv_rows(self, path: str) -> list[dict[str, str]]:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            return [{(k or "").strip(): (v or "") for k, v in row.items()} for row in reader]

    def _calculate_file_hash(self, path: str) -> str:
        digest = sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()


def _money(value: str | Decimal) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
