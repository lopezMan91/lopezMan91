from odoo import fields, models


class MxConsoPack(models.Model):
    _name = "mx.conso.pack"
    _description = "Consolidation Pack"

    name = fields.Char(required=True)
    group_entity_id = fields.Many2one("mx.group.entity", required=True)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    period_key = fields.Char(required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("validated", "Validated"),
        ("loaded", "Loaded"),
    ], default="draft")
    attachment_id = fields.Many2one("ir.attachment")


class MxConsoTranslationRun(models.Model):
    _name = "mx.conso.translation.run"
    _description = "Consolidation Translation Run"

    name = fields.Char(required=True)
    period_key = fields.Char(required=True)
    group_currency_id = fields.Many2one("res.currency", required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("done", "Done"),
    ], default="draft")
    lock_reference = fields.Char(help="FX lock reference used for this translation")


class MxConsoEliminationRun(models.Model):
    _name = "mx.conso.elimination.run"
    _description = "Consolidation Elimination Run"

    name = fields.Char(required=True)
    period_key = fields.Char(required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("matched", "Matched"),
        ("posted", "Posted"),
    ], default="draft")
    entry_ids = fields.One2many("mx.conso.elimination.entry", "run_id")


class MxConsoEliminationEntry(models.Model):
    _name = "mx.conso.elimination.entry"
    _description = "Consolidation Elimination Entry"

    run_id = fields.Many2one("mx.conso.elimination.run", required=True, ondelete="cascade")
    elimination_type = fields.Selection([
        ("ar_ap", "Intercompany AR/AP"),
        ("sales_cogs", "Intercompany Sales/COGS"),
        ("dividends", "Dividends"),
        ("interest", "Interest"),
        ("unrealized_profit", "Unrealized Profit"),
    ], required=True)
    company_id = fields.Many2one("res.company")
    counterparty_company_id = fields.Many2one("res.company")
    amount = fields.Float(required=True)
    evidence_pointer = fields.Char()
    move_id = fields.Many2one("account.move")
