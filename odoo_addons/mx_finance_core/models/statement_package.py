from odoo import fields, models


class MxStatementPackage(models.Model):
    _name = "mx.statement.package"
    _description = "Financial Statement Publication Package"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    period_key = fields.Char(required=True)
    status = fields.Selection([
        ("draft", "Draft"),
        ("review", "In Review"),
        ("approved", "Approved"),
        ("published", "Published"),
    ], default="draft")
    template_ids = fields.Many2many("mx.reporting.template")
    file_pdf = fields.Binary()
    file_xlsx = fields.Binary()
    checksum = fields.Char()
    approver_id = fields.Many2one("res.users")
    approved_at = fields.Datetime()
