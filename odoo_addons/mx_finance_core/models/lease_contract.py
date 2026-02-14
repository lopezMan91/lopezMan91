from odoo import fields, models


class MxLeaseContract(models.Model):
    _name = "mx.lease.contract"
    _description = "Lease Contract IFRS16/NIF D-5"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    counterparty = fields.Char(required=True)
    asset_class = fields.Char(required=True)
    commencement_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    short_term_exemption = fields.Boolean()
    low_value_exemption = fields.Boolean()
    currency_id = fields.Many2one("res.currency", required=True)
    rate_type = fields.Selection([
        ("implicit", "Implicit"),
        ("ibr", "IBR"),
        ("risk_free", "Risk-free"),
    ], default="ibr", required=True)
    annual_rate = fields.Float(required=True)
    payment_line_ids = fields.One2many("mx.lease.payment", "contract_id")


class MxLeasePayment(models.Model):
    _name = "mx.lease.payment"
    _description = "Lease Payment Line"

    contract_id = fields.Many2one("mx.lease.contract", required=True, ondelete="cascade")
    payment_date = fields.Date(required=True)
    amount = fields.Float(required=True)
    variable_flag = fields.Boolean(default=False)
