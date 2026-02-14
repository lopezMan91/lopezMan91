from odoo import fields, models


class MxDimension(models.Model):
    _name = "mx.dimension"
    _description = "Accounting Dimension"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    dimension_type = fields.Selection([
        ("profit_center", "Profit Center"),
        ("cost_center", "Cost Center"),
        ("segment", "Segment"),
        ("project", "Project"),
        ("plant", "Plant"),
        ("channel", "Channel"),
    ], required=True)
    company_id = fields.Many2one("res.company")
    active = fields.Boolean(default=True)


class MxAccountRule(models.Model):
    _name = "mx.account.rule"
    _description = "Account Control Rule"

    account_id = fields.Many2one("account.account", required=True)
    require_partner = fields.Boolean(default=False)
    require_uuid = fields.Boolean(default=False)
    require_dimension = fields.Boolean(default=False)
    allowed_currency_ids = fields.Many2many("res.currency")
