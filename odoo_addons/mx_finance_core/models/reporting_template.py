from odoo import fields, models


class MxReportingTemplate(models.Model):
    _name = "mx.reporting.template"
    _description = "Financial Statement Template"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    statement_type = fields.Selection([
        ("balance", "Balance Sheet"),
        ("pl", "P&L"),
        ("cashflow", "Cash Flow"),
        ("equity", "Changes in Equity"),
    ], required=True)
    version = fields.Char(required=True)
    active = fields.Boolean(default=True)
    line_ids = fields.One2many("mx.reporting.template.line", "template_id")


class MxReportingTemplateLine(models.Model):
    _name = "mx.reporting.template.line"
    _description = "Financial Statement Template Line"

    template_id = fields.Many2one("mx.reporting.template", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    account_prefix = fields.Char(required=True)
    sign = fields.Selection([("normal", "Normal"), ("invert", "Invert")], default="normal")
