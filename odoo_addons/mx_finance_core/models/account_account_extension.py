from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    mx_require_profit_center = fields.Boolean(
        string="Require Profit Center",
        help="If enabled, lines posted to this account must carry a Profit Center dimension.",
        default=False,
    )
    mx_require_cost_center = fields.Boolean(
        string="Require Cost Center",
        help="If enabled, lines posted to this account must carry a Cost Center dimension.",
        default=False,
    )
