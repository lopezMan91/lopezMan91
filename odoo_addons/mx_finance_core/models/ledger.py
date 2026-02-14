from odoo import fields, models


class MxFinanceLedger(models.Model):
    _name = "mx.finance.ledger"
    _description = "Finance Ledger"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    principle = fields.Selection([
        ("nif_sat", "NIF/SAT"),
        ("ifrs", "IFRS"),
        ("fiscal", "Fiscal"),
        ("consol", "Consolidation"),
        ("elim", "Eliminations"),
        ("topside", "Top-side"),
    ], required=True)
    company_id = fields.Many2one("res.company")
    sequence_prefix = fields.Char(help="Optional sequence prefix for accounting moves in this ledger.")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("mx_finance_ledger_code_company_uniq", "unique(code, company_id)", "Ledger code must be unique per company."),
    ]
