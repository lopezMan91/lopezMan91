from odoo import fields, models


class MxFxRevaluationRun(models.Model):
    _name = "mx.fx.revaluation.run"
    _description = "FX Revaluation Run"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    period_key = fields.Char(required=True)
    rate_type = fields.Selection([
        ("closing", "Closing"),
        ("average", "Average"),
    ], default="closing", required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("preview", "Preview"),
        ("posted", "Posted"),
    ], default="draft")
    line_ids = fields.One2many("mx.fx.revaluation.line", "run_id")
    move_id = fields.Many2one("account.move")


class MxFxRevaluationLine(models.Model):
    _name = "mx.fx.revaluation.line"
    _description = "FX Revaluation Line"

    run_id = fields.Many2one("mx.fx.revaluation.run", required=True, ondelete="cascade")
    partner_id = fields.Many2one("res.partner")
    account_id = fields.Many2one("account.account")
    move_line_id = fields.Many2one("account.move.line")
    profit_center = fields.Char()
    currency_id = fields.Many2one("res.currency")
    open_amount_currency = fields.Float()
    historical_rate = fields.Float()
    closing_rate = fields.Float()
    fx_unrealized = fields.Float()
    fx_realized = fields.Float()
