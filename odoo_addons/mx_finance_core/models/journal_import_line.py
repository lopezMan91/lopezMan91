from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MxJournalImportLine(models.Model):
    _name = "mx.journal.import.line"
    _description = "Journal Import Staging Line"

    batch_id = fields.Many2one("mx.journal.import.batch", required=True, ondelete="cascade")
    line_no = fields.Integer(required=True)
    account_code = fields.Char(required=True)
    partner_ref = fields.Char()
    debit = fields.Float(default=0.0)
    credit = fields.Float(default=0.0)
    currency_id = fields.Many2one("res.currency")
    amount_currency = fields.Float(default=0.0)
    dimension_code = fields.Char()
    memo = fields.Char()

    @api.constrains("debit", "credit")
    def _check_signs(self):
        for rec in self:
            if rec.debit < 0 or rec.credit < 0:
                raise ValidationError("Debit/Credit cannot be negative")
            if rec.debit and rec.credit:
                raise ValidationError("Line cannot carry debit and credit at the same time")
