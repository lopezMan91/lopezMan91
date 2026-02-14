from odoo import fields, models


class MxGroupEntity(models.Model):
    _name = "mx.group.entity"
    _description = "Group Structure Entity"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    parent_id = fields.Many2one("mx.group.entity")
    child_ids = fields.One2many("mx.group.entity", "parent_id")
    ownership_pct = fields.Float(required=True, default=100.0)
    control_pct = fields.Float(required=True, default=100.0)
    consolidation_method = fields.Selection([
        ("full", "Full"),
        ("proportional", "Proportional"),
        ("equity", "Equity Method"),
    ], default="full", required=True)
    functional_currency_id = fields.Many2one("res.currency", required=True)
    group_currency_id = fields.Many2one("res.currency", required=True)
