from odoo import fields, models


class MxSatExportRun(models.Model):
    _name = "mx.sat.export.run"
    _description = "SAT Compliance Export Run"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    period_key = fields.Char(required=True)
    export_type = fields.Selection([
        ("catalog", "Catalog"),
        ("trial_balance", "Trial Balance"),
        ("journal_entries", "Journal Entries"),
        ("auxiliary", "Auxiliary"),
        ("diot", "DIOT"),
    ], required=True)
    xml_file = fields.Binary()
    xml_filename = fields.Char()
    checksum = fields.Char()
    state = fields.Selection([
        ("draft", "Draft"),
        ("validated", "Validated"),
        ("exported", "Exported"),
        ("error", "Error"),
    ], default="draft")
    log = fields.Text()
