from odoo import fields, models
from odoo.exceptions import ValidationError


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
    line_ids = fields.One2many("mx.journal.import.line", "batch_id")

    def _gaap_entry_allowed(self, line):
        """Block ghost-like lines in LOCAL when no support exists and not tagged accrual/reclass."""
        ledger_code = (self.ledger_id.code or "").upper()
        memo = (line.memo or "").lower()
        if ledger_code != "LOCAL":
            return True
        if "uuid" in memo:
            return True
        if "accrual" in memo or "reclass" in memo:
            return True
        return not (line.debit or line.credit)

    def action_post_lines(self, batch_size=1000):
        MoveLine = self.env["account.move.line"]
        for batch in self:
            if batch.state not in {"approved", "validated"}:
                raise ValidationError("El lote debe estar validado o aprobado antes de postear.")

            payload = []
            for line in batch.line_ids.sorted("line_no"):
                if not batch._gaap_entry_allowed(line):
                    continue

                payload.append({
                    "name": line.memo or f"Import {batch.name} #{line.line_no}",
                    "debit": line.debit,
                    "credit": line.credit,
                    "amount_currency": line.amount_currency,
                    "currency_id": line.currency_id.id if line.currency_id else False,
                    "company_id": batch.company_id.id,
                })
                if len(payload) >= batch_size:
                    MoveLine.create(payload)
                    payload = []

            if payload:
                MoveLine.create(payload)

            batch.state = "posted"
        return True
