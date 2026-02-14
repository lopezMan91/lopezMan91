from odoo import fields, models


class MxIntercompanyTag(models.Model):
    _name = "mx.intercompany.tag"
    _description = "Intercompany Transaction Tag"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True)
    counterparty_company_id = fields.Many2one("res.company", required=True)
    external_ref = fields.Char(required=True, index=True)
    move_line_ids = fields.Many2many("account.move.line")
    elimination_status = fields.Selection([
        ("open", "Open"),
        ("matched", "Matched"),
        ("eliminated", "Eliminated"),
    ], default="open")
