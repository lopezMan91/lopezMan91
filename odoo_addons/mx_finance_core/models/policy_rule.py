from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MxAccountingPolicy(models.Model):
    _name = "mx.accounting.policy"
    _description = "Accounting Policy Rule"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    company_id = fields.Many2one("res.company", required=True)
    event_type = fields.Char(required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    active = fields.Boolean(default=True)
    version_ids = fields.One2many("mx.accounting.policy.version", "policy_id")


class MxAccountingPolicyVersion(models.Model):
    _name = "mx.accounting.policy.version"
    _description = "Accounting Policy Version"
    _order = "effective_from desc, id desc"

    policy_id = fields.Many2one("mx.accounting.policy", required=True, ondelete="cascade")
    version = fields.Char(required=True)
    effective_from = fields.Date(required=True)
    effective_to = fields.Date()
    rule_json = fields.Text(required=True, help="Policy-as-code payload used by posting engine.")
    approver_id = fields.Many2one("res.users")
    approved_at = fields.Datetime()

    @api.constrains("effective_from", "effective_to")
    def _check_dates(self):
        for rec in self:
            if rec.effective_to and rec.effective_to < rec.effective_from:
                raise ValidationError("effective_to cannot be earlier than effective_from")
