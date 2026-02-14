import hashlib
import json

from odoo import fields, models


class MxPostingRun(models.Model):
    _name = "mx.posting.run"
    _description = "Posting Engine Run"

    name = fields.Char(required=True)
    event_id = fields.Many2one("mx.accounting.event", required=True)
    company_id = fields.Many2one("res.company", related="event_id.company_id", store=True)
    rule_version = fields.Char(required=True)
    run_at = fields.Datetime(default=fields.Datetime.now)
    ledger_id = fields.Many2one("mx.finance.ledger", required=True)
    move_ids = fields.Many2many("account.move")
    preview_payload = fields.Text(help="JSON summary of posting preview for governance and approvals.")
    input_hash = fields.Char(index=True)
    log = fields.Text()
    state = fields.Selection([
        ("draft", "Draft"),
        ("previewed", "Previewed"),
        ("done", "Done"),
        ("error", "Error"),
    ], default="draft")

    _sql_constraints = [
        (
            "mx_posting_run_event_ledger_rule_uniq",
            "unique(event_id, ledger_id, rule_version)",
            "Posting run already exists for this event/ledger/rule version.",
        ),
        (
            "mx_posting_run_event_ledger_input_hash_uniq",
            "unique(event_id, ledger_id, input_hash)",
            "Posting run already exists for this event/ledger/input hash.",
        )
    ]

    def action_preview(self):
        for rec in self:
            preview = {
                "event": rec.event_id.name,
                "event_type": rec.event_id.event_type,
                "ledger": rec.ledger_id.code,
                "rule_version": rec.rule_version,
                "source": f"{rec.event_id.source_model}:{rec.event_id.source_id}",
                "amount_total": rec.event_id.amount_total,
                "state": "previewed",
            }
            rec.preview_payload = json.dumps(preview, ensure_ascii=False)
            rec.input_hash = hashlib.sha256(rec.preview_payload.encode("utf-8")).hexdigest()
            rec.state = "previewed"
