from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MxAccountPeriodLock(models.Model):
    _name = "mx.account.period.lock"
    _description = "Account Period Lock"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    state = fields.Selection([
        ("open", "Open"),
        ("locked", "Locked"),
        ("reopen_requested", "Reopen Requested"),
    ], default="open", required=True)
    reason = fields.Text()
    approved_by = fields.Many2one("res.users")
    approved_date = fields.Datetime()

    @api.constrains("date_from", "date_to")
    def _check_date_range(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError("date_to cannot be earlier than date_from.")

    @api.constrains("company_id", "ledger_id", "date_from", "date_to", "state")
    def _check_no_overlap(self):
        for rec in self:
            overlap = self.search([
                ("id", "!=", rec.id),
                ("company_id", "=", rec.company_id.id),
                ("ledger_id", "=", rec.ledger_id.id),
                ("state", "in", ["locked", "reopen_requested"]),
                ("date_from", "<=", rec.date_to),
                ("date_to", ">=", rec.date_from),
            ], limit=1)
            if overlap:
                raise ValidationError("Overlapping period locks are not allowed for the same company and ledger.")
