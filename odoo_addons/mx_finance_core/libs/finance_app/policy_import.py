from __future__ import annotations

import csv
import zipfile
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from .transactions import PolicyLine, TransactionManager


@dataclass
class PolicyPostResult:
    lines_read: int
    lines_posted: int
    policies_posted: int


class PolicyImportError(ValueError):
    pass


def import_and_post_policies(path: str, manager: TransactionManager) -> PolicyPostResult:
    post_summary = manager.post_policy_lines(read_policy_lines(path))
    return PolicyPostResult(
        lines_read=post_summary.lines_posted,
        lines_posted=post_summary.lines_posted,
        policies_posted=post_summary.policies_posted,
    )


def read_policy_lines(path: str) -> Iterable[PolicyLine]:
    ext = Path(path).suffix.lower()
    if ext == ".csv":
        rows = _read_csv_rows(path)
    elif ext == ".xlsx":
        rows = _read_xlsx_rows(path)
    else:
        raise PolicyImportError("Formato no soportado. Usa .xlsx o .csv")

    for row_number, row in enumerate(rows, start=2):
        try:
            yield PolicyLine(
                policy_id=_required(row, "poliza"),
                date=_required(row, "fecha"),
                description=_required(row, "descripcion"),
                account=_required(row, "cuenta"),
                debit=float(_optional(row, "cargo", "0") or 0),
                credit=float(_optional(row, "abono", "0") or 0),
                category=_optional(row, "categoria", "poliza"),
            )
        except Exception as exc:
            raise PolicyImportError(f"Error en fila {row_number}: {exc}") from exc


def _required(row: dict[str, str], field: str) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise PolicyImportError(f"Campo obligatorio vacio: {field}")
    return value


def _optional(row: dict[str, str], field: str, default: str) -> str:
    return row.get(field, default).strip() or default


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return [_normalize_row_keys(r) for r in reader]


def _read_xlsx_rows(path: str) -> list[dict[str, str]]:
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        shared_strings = _load_shared_strings(zf, ns)

        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        first_sheet = workbook.find("s:sheets/s:sheet", ns)
        if first_sheet is None:
            return []

        rel_id = first_sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels:
            if rel.attrib.get("Id") == rel_id:
                target = rel.attrib.get("Target")
                break
        if not target:
            raise PolicyImportError("No se pudo ubicar la hoja en el archivo .xlsx")
        if ".." in target or target.startswith("/"):
            raise PolicyImportError("Ruta de hoja inválida en el archivo .xlsx")

        normalized_target = target.replace("\\", "/")
        if not normalized_target.startswith("worksheets/"):
            raise PolicyImportError("La primera hoja debe estar en xl/worksheets/")

        sheet_xml = ET.fromstring(zf.read(f"xl/{normalized_target}"))
        rows = sheet_xml.findall("s:sheetData/s:row", ns)
        if not rows:
            return []

        matrix: list[list[str]] = []
        for row in rows:
            values: list[str] = []
            current_index = 0
            for cell in row.findall("s:c", ns):
                cell_ref = cell.attrib.get("r", "")
                cell_index = _xlsx_col_to_index(cell_ref)
                while current_index < cell_index:
                    values.append("")
                    current_index += 1
                values.append(_xlsx_cell_value(cell, ns, shared_strings))
                current_index += 1
            matrix.append(values)

        headers = [_slugify(h) for h in matrix[0]]
        data_rows: list[dict[str, str]] = []
        for values in matrix[1:]:
            if not any(v.strip() for v in values):
                continue
            padded = values + [""] * (len(headers) - len(values))
            data_rows.append(_normalize_row_keys(dict(zip(headers, padded))))
        return data_rows


def _load_shared_strings(zf: zipfile.ZipFile, ns: dict[str, str]) -> list[str]:
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    values: list[str] = []
    for si in root.findall("s:si", ns):
        texts = [t.text or "" for t in si.findall(".//s:t", ns)]
        values.append("".join(texts))
    return values


def _xlsx_cell_value(cell: ET.Element, ns: dict[str, str], shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value_node = cell.find("s:v", ns)
    if value_node is None:
        inline = cell.find("s:is/s:t", ns)
        return (inline.text or "") if inline is not None else ""

    raw = value_node.text or ""
    if cell_type == "s":
        try:
            idx = int(raw)
        except ValueError:
            return ""
        return shared_strings[idx] if idx < len(shared_strings) else ""
    return raw


def _xlsx_col_to_index(cell_ref: str) -> int:
    """Convert Excel-style cell references (A1, AA14) into zero-based column indexes."""
    if not cell_ref:
        return 0

    match = re.match(r"([A-Za-z]+)", cell_ref)
    if not match:
        return 0

    letters = match.group(1).upper()
    index = 0
    for char in letters:
        index = (index * 26) + (ord(char) - ord("A") + 1)
    return index - 1


def _slugify(value: str) -> str:
    return value.strip().lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


def _normalize_row_keys(row: dict[str, str]) -> dict[str, str]:
    mapping = {
        "poliza": "poliza",
        "folio_poliza": "poliza",
        "fecha": "fecha",
        "descripcion": "descripcion",
        "concepto": "descripcion",
        "cuenta": "cuenta",
        "cargo": "cargo",
        "debe": "cargo",
        "abono": "abono",
        "haber": "abono",
        "categoria": "categoria",
    }
    normalized: dict[str, str] = {}
    for key, value in row.items():
        if key is None:
            continue
        slug_key = _slugify(str(key))
        target = mapping.get(slug_key, slug_key)
        normalized[target] = str(value or "")
    return normalized
