import csv
import tempfile
import unittest
import zipfile
from pathlib import Path

from finance_app.policy_import import PolicyImportError, import_and_post_policies
from finance_app.transactions import TransactionManager


class PolicyImportTests(unittest.TestCase):
    def test_import_and_post_from_csv(self):
        manager = TransactionManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "polizas.csv"
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=["poliza", "fecha", "descripcion", "cuenta", "cargo", "abono", "categoria"],
                )
                writer.writeheader()
                writer.writerow({
                    "poliza": "P-001",
                    "fecha": "2026-02-01",
                    "descripcion": "Compra de papeleria",
                    "cuenta": "6000",
                    "cargo": "1000",
                    "abono": "0",
                    "categoria": "gasto",
                })
                writer.writerow({
                    "poliza": "P-001",
                    "fecha": "2026-02-01",
                    "descripcion": "Pago banco",
                    "cuenta": "1020",
                    "cargo": "0",
                    "abono": "1000",
                    "categoria": "activo",
                })

            result = import_and_post_policies(str(path), manager)

        self.assertEqual(result.policies_posted, 1)
        self.assertEqual(result.lines_posted, 2)
        self.assertEqual(len(manager.transactions), 2)
        self.assertEqual(round(manager.balance(), 2), 0.0)

    def test_import_and_post_from_xlsx(self):
        manager = TransactionManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "polizas.xlsx"
            _write_simple_xlsx(path)
            result = import_and_post_policies(str(path), manager)

        self.assertEqual(result.policies_posted, 1)
        self.assertEqual(result.lines_posted, 2)
        self.assertEqual(len(manager.transactions), 2)


    def test_import_and_post_from_sparse_xlsx(self):
        manager = TransactionManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "polizas_sparse.xlsx"
            _write_sparse_xlsx(path)
            result = import_and_post_policies(str(path), manager)

        self.assertEqual(result.policies_posted, 1)
        self.assertEqual(result.lines_posted, 2)
        self.assertEqual(len(manager.transactions), 2)

    def test_reject_unbalanced_policy(self):
        manager = TransactionManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad_polizas.csv"
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=["poliza", "fecha", "descripcion", "cuenta", "cargo", "abono", "categoria"],
                )
                writer.writeheader()
                writer.writerow({
                    "poliza": "P-002",
                    "fecha": "2026-02-02",
                    "descripcion": "Linea 1",
                    "cuenta": "6000",
                    "cargo": "1000",
                    "abono": "0",
                    "categoria": "gasto",
                })
                writer.writerow({
                    "poliza": "P-002",
                    "fecha": "2026-02-02",
                    "descripcion": "Linea 2",
                    "cuenta": "1020",
                    "cargo": "0",
                    "abono": "900",
                    "categoria": "activo",
                })

            with self.assertRaises(ValueError):
                import_and_post_policies(str(path), manager)

    def test_reject_invalid_sheet_target_path(self):
        manager = TransactionManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad_target.xlsx"
            _write_xlsx_with_invalid_target(path)

            with self.assertRaises(PolicyImportError):
                import_and_post_policies(str(path), manager)


def _write_simple_xlsx(path: Path):
    content_types = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"xml\" ContentType=\"application/xml\"/>
  <Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>
  <Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>
</Types>"""

    rels = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>
</Relationships>"""

    workbook = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">
  <sheets><sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/></sheets>
</workbook>"""

    workbook_rels = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>
</Relationships>"""

    sheet1 = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">
  <sheetData>
    <row r=\"1\">
      <c r=\"A1\" t=\"inlineStr\"><is><t>poliza</t></is></c>
      <c r=\"B1\" t=\"inlineStr\"><is><t>fecha</t></is></c>
      <c r=\"C1\" t=\"inlineStr\"><is><t>descripcion</t></is></c>
      <c r=\"D1\" t=\"inlineStr\"><is><t>cuenta</t></is></c>
      <c r=\"E1\" t=\"inlineStr\"><is><t>cargo</t></is></c>
      <c r=\"F1\" t=\"inlineStr\"><is><t>abono</t></is></c>
      <c r=\"G1\" t=\"inlineStr\"><is><t>categoria</t></is></c>
    </row>
    <row r=\"2\">
      <c r=\"A2\" t=\"inlineStr\"><is><t>P-003</t></is></c>
      <c r=\"B2\" t=\"inlineStr\"><is><t>2026-02-03</t></is></c>
      <c r=\"C2\" t=\"inlineStr\"><is><t>Equipo</t></is></c>
      <c r=\"D2\" t=\"inlineStr\"><is><t>1500</t></is></c>
      <c r=\"E2\"><v>500</v></c>
      <c r=\"F2\"><v>0</v></c>
      <c r=\"G2\" t=\"inlineStr\"><is><t>activo</t></is></c>
    </row>
    <row r=\"3\">
      <c r=\"A3\" t=\"inlineStr\"><is><t>P-003</t></is></c>
      <c r=\"B3\" t=\"inlineStr\"><is><t>2026-02-03</t></is></c>
      <c r=\"C3\" t=\"inlineStr\"><is><t>Pago banco</t></is></c>
      <c r=\"D3\" t=\"inlineStr\"><is><t>1020</t></is></c>
      <c r=\"E3\"><v>0</v></c>
      <c r=\"F3\"><v>500</v></c>
      <c r=\"G3\" t=\"inlineStr\"><is><t>activo</t></is></c>
    </row>
  </sheetData>
</worksheet>"""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet1)


def _write_sparse_xlsx(path: Path):
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

    workbook_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

    sheet1 = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>poliza</t></is></c>
      <c r="B1" t="inlineStr"><is><t>fecha</t></is></c>
      <c r="C1" t="inlineStr"><is><t>descripcion</t></is></c>
      <c r="D1" t="inlineStr"><is><t>cuenta</t></is></c>
      <c r="E1" t="inlineStr"><is><t>cargo</t></is></c>
      <c r="F1" t="inlineStr"><is><t>abono</t></is></c>
      <c r="G1" t="inlineStr"><is><t>categoria</t></is></c>
    </row>
    <row r="2">
      <c r="A2" t="inlineStr"><is><t>P-004</t></is></c>
      <c r="B2" t="inlineStr"><is><t>2026-02-04</t></is></c>
      <c r="C2" t="inlineStr"><is><t>Compra office</t></is></c>
      <c r="D2" t="inlineStr"><is><t>6000</t></is></c>
      <c r="E2"><v>250</v></c>
      <c r="G2" t="inlineStr"><is><t>gasto</t></is></c>
    </row>
    <row r="3">
      <c r="A3" t="inlineStr"><is><t>P-004</t></is></c>
      <c r="B3" t="inlineStr"><is><t>2026-02-04</t></is></c>
      <c r="C3" t="inlineStr"><is><t>Pago banco</t></is></c>
      <c r="D3" t="inlineStr"><is><t>1020</t></is></c>
      <c r="F3"><v>250</v></c>
      <c r="G3" t="inlineStr"><is><t>activo</t></is></c>
    </row>
  </sheetData>
</worksheet>"""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet1)


def _write_xlsx_with_invalid_target(path: Path):
    content_types = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"xml\" ContentType=\"application/xml\"/>
  <Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>
  <Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>
</Types>"""

    rels = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>
</Relationships>"""

    workbook = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">
  <sheets><sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/></sheets>
</workbook>"""

    workbook_rels = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"../outside.xml\"/>
</Relationships>"""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)


if __name__ == "__main__":
    unittest.main()
