from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MxAccountingEvent(models.Model):
    _name = "mx.accounting.event"
    _description = "Immutable Business Event"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True, tracking=True)
    source_model = fields.Char(required=True)
    source_id = fields.Char(required=True)
    event_type = fields.Char(required=True)
    event_date = fields.Date(default=fields.Date.context_today)
    document_date = fields.Date()
    company_id = fields.Many2one("res.company", required=True)
    partner_id = fields.Many2one("res.partner")
    currency_id = fields.Many2one("res.currency", required=True)
    amount_total = fields.Float()
    event_payload = fields.Text(help="Serialized payload for policy engine.")
    ledger_scope = fields.Selection([
        ("local", "Local/NIF"),
        ("ifrs", "IFRS"),
        ("fiscal", "Fiscal"),
        ("multi", "Multi-ledger"),
    ], default="multi", required=True)
    immutable_hash = fields.Char(readonly=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("validated", "Validated"),
        ("posted", "Posted"),
        ("locked", "Locked"),
    ], default="draft", tracking=True)
    revision_of_id = fields.Many2one("mx.accounting.event")
    revision_ids = fields.One2many("mx.accounting.event", "revision_of_id")
    posting_run_ids = fields.One2many("mx.posting.run", "event_id")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.immutable_hash = (
                f"{rec.source_model}:{rec.source_id}:{rec.company_id.id}:{rec.event_type}:{rec.ledger_scope}"
            )
        return records

    def write(self, vals):
        immutable_fields = {
            "source_model", "source_id", "event_type", "company_id", "currency_id", "amount_total", "event_payload",
            "ledger_scope",
        }
        for rec in self:
            if rec.state in ("validated", "posted", "locked") and immutable_fields.intersection(vals.keys()):
                raise ValidationError("Validated/posted events are immutable. Create a revision instead.")
        return super().write(vals)

    def action_validate(self):
        self.write({"state": "validated"})

    def action_lock(self):
        self.write({"state": "locked"})

    def action_create_revision(self):
        self.ensure_one()
        new = self.copy({
            "name": f"{self.name} (REV)",
            "revision_of_id": self.id,
            "state": "draft",
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "mx.accounting.event",
            "view_mode": "form",
            "res_id": new.id,
        }
