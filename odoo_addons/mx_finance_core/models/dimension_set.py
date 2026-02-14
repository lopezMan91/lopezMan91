import hashlib

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MxDimensionType(models.Model):
    _name = "mx.dimension.type"
    _description = "MX Dimension Type"

    code = fields.Char(required=True)
    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company")
    is_required_default = fields.Boolean(default=False)

    _sql_constraints = [
        (
            "mx_dimension_type_company_code_uniq",
            "unique(company_id, code)",
            "Dimension type code must be unique per company.",
        )
    ]


class MxDimensionValue(models.Model):
    _name = "mx.dimension.value"
    _description = "MX Dimension Value"

    type_id = fields.Many2one("mx.dimension.type", required=True)
    company_id = fields.Many2one("res.company", related="type_id.company_id", store=True)
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    parent_id = fields.Many2one("mx.dimension.value")

    _sql_constraints = [
        (
            "mx_dimension_value_type_code_uniq",
            "unique(type_id, code)",
            "Dimension value code must be unique per type.",
        )
    ]


class MxDimensionSet(models.Model):
    _name = "mx.dimension.set"
    _description = "MX Dimension Set"

    company_id = fields.Many2one("res.company")
    name = fields.Char(required=True)
    value_ids = fields.Many2many("mx.dimension.value")
    hash_key = fields.Char(index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("mx_dimension_set_company_hash_uniq", "unique(company_id, hash_key)", "Dimension set already exists."),
    ]

    @api.onchange("value_ids")
    def _onchange_values(self):
        for rec in self:
            rec.hash_key = rec._compute_hash_key()

    def _compute_hash_key(self):
        self.ensure_one()
        sorted_codes = sorted(self.value_ids.mapped(lambda v: f"{v.type_id.code}:{v.code}"))
        raw = "|".join(sorted_codes)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.hash_key = rec._compute_hash_key()
        return records

    def write(self, vals):
        result = super().write(vals)
        if "value_ids" in vals:
            for rec in self:
                rec.hash_key = rec._compute_hash_key()
        return result


class MxDimensionRule(models.Model):
    _name = "mx.dimension.rule"
    _description = "MX Dimension Rule"

    company_id = fields.Many2one("res.company", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger")
    account_id = fields.Many2one("account.account")
    journal_id = fields.Many2one("account.journal")
    event_type = fields.Char()
    dimension_type_id = fields.Many2one("mx.dimension.type", required=True)
    required = fields.Boolean(default=True)
    default_value_id = fields.Many2one("mx.dimension.value")
    domain_condition = fields.Char(help="Optional domain condition expression for custom matching.")

    @api.constrains("default_value_id", "dimension_type_id")
    def _check_default_value_type(self):
        for rec in self:
            if rec.default_value_id and rec.default_value_id.type_id != rec.dimension_type_id:
                raise ValidationError("Default dimension value must belong to selected dimension type.")
