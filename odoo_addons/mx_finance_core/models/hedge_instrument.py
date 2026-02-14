from odoo import fields, models


class MxHedgeInstrument(models.Model):
    _name = "mx.hedge.instrument"
    _description = "IFRS9 / NIF C-10 Hedge Instrument"

    name = fields.Char(required=True)
    instrument_type = fields.Selection([
        ("forward", "FX Forward"),
        ("swap", "Swap"),
        ("option", "Option"),
        ("collar", "Collar"),
    ], required=True)
    company_id = fields.Many2one("res.company", required=True)
    currency_id = fields.Many2one("res.currency", required=True)
    notional = fields.Float(required=True)
    start_date = fields.Date(required=True)
    maturity_date = fields.Date(required=True)
    hedge_type = fields.Selection([
        ("fair_value", "Fair Value Hedge"),
        ("cash_flow", "Cash Flow Hedge"),
        ("net_investment", "Net Investment Hedge"),
    ], required=True)
    valuation_source = fields.Char()
    valuation_lock_period = fields.Char(help="YYYY-MM")
    documentation = fields.Text(help="Risk management objective and effectiveness method.")
