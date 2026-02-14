from odoo import fields, models


class MxControlLibrary(models.Model):
    _name = "mx.control.library"
    _description = "Internal Control Library"

    name = fields.Char(required=True)
    control_type = fields.Selection([
        ("preventive", "Preventive"),
        ("detective", "Detective"),
    ], required=True)
    owner_id = fields.Many2one("res.users")
    frequency = fields.Selection([
        ("daily", "Daily"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
    ], required=True)
    severity = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ], required=True)
    evidence_required = fields.Boolean(default=True)


class MxSodRule(models.Model):
    _name = "mx.sod.rule"
    _description = "Segregation of Duties Rule"

    name = fields.Char(required=True)
    role_a = fields.Char(required=True)
    role_b = fields.Char(required=True)
    active = fields.Boolean(default=True)


class MxCcmAlert(models.Model):
    _name = "mx.ccm.alert"
    _description = "Continuous Controls Monitoring Alert"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company")
    alert_type = fields.Selection([
        ("uuid_missing", "UUID Missing"),
        ("uuid_duplicate", "UUID Duplicate"),
        ("sod_conflict", "SoD Conflict"),
        ("manual_adjustment_close", "Manual Adjustment Near Close"),
        ("fx_pending", "FX Revaluation Pending"),
    ], required=True)
    severity = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ], required=True)
    status = fields.Selection([
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ], default="open")
    evidence_pointer = fields.Char()
