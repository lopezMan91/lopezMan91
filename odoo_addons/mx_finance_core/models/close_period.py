from odoo import fields, models


class MxClosePeriod(models.Model):
    _name = "mx.close.period"
    _description = "Close Period Governance"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    period_key = fields.Char(required=True, help="YYYY-MM")
    state = fields.Selection([
        ("open", "Open"),
        ("soft_closed", "Soft Closed"),
        ("hard_closed", "Hard Closed"),
    ], default="open", required=True)
    reopen_log_ids = fields.One2many("mx.close.reopen.log", "close_period_id")

    _sql_constraints = [
        (
            "mx_close_period_company_ledger_period_uniq",
            "unique(company_id, ledger_id, period_key)",
            "A close period already exists for this company/ledger/period.",
        )
    ]


class MxCloseReopenLog(models.Model):
    _name = "mx.close.reopen.log"
    _description = "Period Reopen Audit Log"

    close_period_id = fields.Many2one("mx.close.period", required=True, ondelete="cascade")
    requested_by = fields.Many2one("res.users", required=True)
    approved_by = fields.Many2one("res.users", required=True)
    reason = fields.Text(required=True)
    created_at = fields.Datetime(default=fields.Datetime.now)
