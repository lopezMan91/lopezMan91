from odoo import fields, models


class MxCloseCockpit(models.Model):
    _name = "mx.close.cockpit"
    _description = "Close Cockpit"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    period_key = fields.Char(required=True)
    status = fields.Selection([
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
    ], default="open")
    item_ids = fields.One2many("mx.close.cockpit.item", "cockpit_id")


class MxCloseCockpitItem(models.Model):
    _name = "mx.close.cockpit.item"
    _description = "Close Cockpit Item"

    cockpit_id = fields.Many2one("mx.close.cockpit", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    run_type = fields.Selection([
        ("fx_revaluation", "FX Revaluation"),
        ("depreciation", "Depreciation"),
        ("ifrs16", "IFRS16"),
        ("diot", "DIOT"),
        ("sat_export", "SAT Export"),
        ("consolidation", "Consolidation"),
    ], required=True)
    responsible_id = fields.Many2one("res.users")
    evidence_pointer = fields.Char()
    state = fields.Selection([
        ("pending", "Pending"),
        ("running", "Running"),
        ("done", "Done"),
        ("blocked", "Blocked"),
    ], default="pending")
