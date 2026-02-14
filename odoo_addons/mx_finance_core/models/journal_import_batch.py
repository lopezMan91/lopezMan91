from odoo import fields, models


class MxJournalImportBatch(models.Model):
    _name = "mx.journal.import.batch"
    _description = "Journal Import Staging Batch"

    name = fields.Char(required=True)
    import_uid = fields.Char(required=True, index=True)
    company_id = fields.Many2one("res.company", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    file_hash = fields.Char(required=True)
    file_binary = fields.Binary(required=True)
    filename = fields.Char()
    preview_json = fields.Text()
    error_log = fields.Text()
    state = fields.Selection([
        ("loaded", "Loaded"),
        ("validated", "Validated"),
        ("approved", "Approved"),
        ("posted", "Posted"),
        ("error", "Error"),
    ], default="loaded")
    posting_run_id = fields.Many2one("mx.posting.run")
