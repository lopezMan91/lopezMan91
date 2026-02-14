from odoo import fields, models


class MxRateTable(models.Model):
    _name = "mx.rate.table"
    _description = "FX Rate Table"

    name = fields.Char(required=True)
    rate_type = fields.Selection([
        ("spot", "Spot"),
        ("closing", "Closing"),
        ("average", "Average"),
        ("historical", "Historical"),
    ], required=True)
    currency_id = fields.Many2one("res.currency", required=True)
    company_id = fields.Many2one("res.company", required=True)
    rate = fields.Float(required=True)
    source = fields.Char(required=True)
    loaded_at = fields.Datetime(default=fields.Datetime.now)
    locked_period = fields.Char(help="YYYY-MM period lock for closing reproducibility")
