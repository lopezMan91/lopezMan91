from hashlib import sha256

from odoo import api, fields, models
from odoo.exceptions import ValidationError


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
    hard_lock_key_hash = fields.Char(readonly=True)
    reopen_log_ids = fields.One2many("mx.close.reopen.log", "close_period_id")

    _sql_constraints = [
        (
            "mx_close_period_company_ledger_period_uniq",
            "unique(company_id, ledger_id, period_key)",
            "A close period already exists for this company/ledger/period.",
        )
    ]

    def action_hard_close(self, hard_lock_key: str | None = None):
        for rec in self:
            effective_key = hard_lock_key or f"DF-{rec.company_id.id}-{rec.ledger_id.id}-{rec.period_key}"
            rec.write({
                "state": "hard_closed",
                "hard_lock_key_hash": sha256(effective_key.encode("utf-8")).hexdigest(),
            })

    def action_reopen_with_key(self, unlock_key: str, reason: str):
        for rec in self:
            if rec.state != "hard_closed":
                rec.state = "open"
                continue
            if not unlock_key:
                raise ValidationError("Unlock key requerida para hard close")
            if sha256(unlock_key.encode("utf-8")).hexdigest() != rec.hard_lock_key_hash:
                raise ValidationError("Unlock key inválida")
            rec.state = "open"
            self.env["mx.close.reopen.log"].create({
                "close_period_id": rec.id,
                "requested_by": self.env.user.id,
                "approved_by": self.env.user.id,
                "reason": reason or "Reapertura con unlock key",
            })


class MxCloseReopenLog(models.Model):
    _name = "mx.close.reopen.log"
    _description = "Period Reopen Audit Log"

    close_period_id = fields.Many2one("mx.close.period", required=True, ondelete="cascade")
    requested_by = fields.Many2one("res.users", required=True)
    approved_by = fields.Many2one("res.users", required=True)
    reason = fields.Text(required=True)
    created_at = fields.Datetime(default=fields.Datetime.now)
