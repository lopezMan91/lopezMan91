from odoo import fields, models


class MxIfrs18Taxonomy(models.Model):
    _name = "mx.ifrs18.taxonomy"
    _description = "IFRS 18 Taxonomy Layer"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    statement_line = fields.Char(required=True)
    category = fields.Selection([
        ("operating", "Operating"),
        ("investing", "Investing"),
        ("financing", "Financing"),
    ], required=True)
    effective_from = fields.Date(required=True)
    effective_to = fields.Date()


class MxIfrs18Mpm(models.Model):
    _name = "mx.ifrs18.mpm"
    _description = "IFRS 18 MPM"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    formula = fields.Text(required=True)
    adjustments = fields.Text()
    ifrs_subtotal_target = fields.Char(required=True)
    version = fields.Char(required=True)
    approved_by = fields.Many2one("res.users")
    approved_at = fields.Datetime()
