from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    mx_ledger_id = fields.Many2one("mx.finance.ledger", string="MX Ledger", index=True)
    mx_event_id = fields.Many2one("mx.accounting.event", string="Accounting Event", index=True)
    mx_policy_version_id = fields.Many2one("mx.accounting.policy.version", string="Policy Version")
    mx_uuid = fields.Char(string="CFDI UUID", index=True)
    mx_evidence_url = fields.Char(string="Evidence Pointer")
    mx_entry_nature = fields.Selection([
        ("regular", "Regular"),
        ("accrual", "Accrual"),
        ("reclass", "Reclassification"),
    ], default="regular", required=True)

    @api.model
    def _period_key_from_date(self, dt):
        if not dt:
            return ""
        # dt is date in Odoo context.
        return dt.strftime("%Y-%m")

    def _check_period_lock(self):
        ClosePeriod = self.env["mx.close.period"]
        PeriodLock = self.env["mx.account.period.lock"]
        moves = self.filtered(lambda m: m.mx_ledger_id and m.date)
        if not moves:
            return

        company_ids = moves.mapped("company_id").ids
        ledger_ids = moves.mapped("mx_ledger_id").ids
        date_values = moves.mapped("date")
        min_date = min(date_values)
        max_date = max(date_values)

        # Bulk-load lock records once to avoid N+1 queries for batched posting.
        legacy_locks = ClosePeriod.search([
            ("company_id", "in", company_ids),
            ("ledger_id", "in", ledger_ids),
            ("state", "=", "hard_closed"),
        ])
        ranged_locks = PeriodLock.search([
            ("company_id", "in", company_ids),
            ("ledger_id", "in", ledger_ids),
            ("state", "=", "locked"),
            ("date_from", "<=", max_date),
            ("date_to", ">=", min_date),
        ])

        locked_period_keys = {
            (lock.company_id.id, lock.ledger_id.id, lock.period_key)
            for lock in legacy_locks
        }

        for move in moves:
            period_key = self._period_key_from_date(move.date)
            if (move.company_id.id, move.mx_ledger_id.id, period_key) in locked_period_keys:
                raise ValidationError(
                    f"Period {period_key} for ledger {move.mx_ledger_id.code} is locked. "
                    "Use reopen workflow before posting changes."
                )

            for lock in ranged_locks:
                if (
                    lock.company_id.id == move.company_id.id
                    and lock.ledger_id.id == move.mx_ledger_id.id
                    and lock.date_from <= move.date <= lock.date_to
                ):
                    raise ValidationError(
                        f"Period {period_key} for ledger {move.mx_ledger_id.code} is locked. "
                        "Use reopen workflow before posting changes."
                    )

    def action_post(self):
        self._check_period_lock()
        return super().action_post()


    def write(self, vals):
        posted = self.filtered(lambda m: m.state == "posted")
        if posted and not self.env.context.get("mx_allow_posted_override"):
            raise ValidationError("Posted entries are immutable. Use reversal/reopen workflow.")
        return super().write(vals)

    def unlink(self):
        posted = self.filtered(lambda m: m.state == "posted")
        if posted and not self.env.context.get("mx_allow_posted_override"):
            raise ValidationError("Posted entries cannot be deleted. Create reversal entries instead.")
        return super().unlink()

    @api.model
    def find_ghost_transactions(self, company_id: int | None = None) -> list[int]:
        """Detect posted LOCAL entries without UUID and not marked as accrual/reclass."""
        domain = [
            ("state", "=", "posted"),
            ("mx_ledger_id.code", "=", "LOCAL"),
            ("mx_uuid", "=", False),
            ("mx_entry_nature", "=", "regular"),
        ]
        if company_id:
            domain.append(("company_id", "=", company_id))
        return self.search(domain).ids


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    mx_ledger_id = fields.Many2one("mx.finance.ledger", related="move_id.mx_ledger_id", store=True, index=True)
    mx_event_id = fields.Many2one("mx.accounting.event", related="move_id.mx_event_id", store=True, index=True)
    mx_uuid = fields.Char(related="move_id.mx_uuid", store=True, index=True)
    mx_evidence_url = fields.Char(related="move_id.mx_evidence_url", store=True)
    dimension_set_id = fields.Many2one("mx.dimension.set", string="Dimension Set", index=True)
    mx_profit_center_id = fields.Many2one(
        "mx.dimension.value",
        string="Profit Center",
        domain="[(\'type_id.code\', \'=\', \'PROFIT_CENTER\')]",
        index=True,
    )
    mx_cost_center_id = fields.Many2one(
        "mx.dimension.value",
        string="Cost Center",
        domain="[(\'type_id.code\', \'=\', \'COST_CENTER\')]",
        index=True,
    )

    @api.onchange("dimension_set_id")
    def _onchange_dimension_set(self):
        for line in self:
            line.mx_profit_center_id = False
            line.mx_cost_center_id = False
            if not line.dimension_set_id:
                continue
            for value in line.dimension_set_id.value_ids:
                dim_code = (value.type_id.code or "").upper()
                if dim_code == "PROFIT_CENTER":
                    line.mx_profit_center_id = value
                elif dim_code == "COST_CENTER":
                    line.mx_cost_center_id = value

    @api.constrains("account_id", "mx_profit_center_id", "mx_cost_center_id")
    def _check_dimension_requirements(self):
        for line in self:
            if line.display_type:
                continue
            if line.mx_profit_center_id and (line.mx_profit_center_id.type_id.code or "").upper() != "PROFIT_CENTER":
                raise ValidationError("Selected Profit Center value does not belong to PROFIT_CENTER dimension type.")
            if line.mx_cost_center_id and (line.mx_cost_center_id.type_id.code or "").upper() != "COST_CENTER":
                raise ValidationError("Selected Cost Center value does not belong to COST_CENTER dimension type.")
            if line.account_id.mx_require_profit_center and not line.mx_profit_center_id:
                raise ValidationError(
                    f"Profit Center is required for account {line.account_id.code} - {line.account_id.name}."
                )
            if line.account_id.mx_require_cost_center and not line.mx_cost_center_id:
                raise ValidationError(
                    f"Cost Center is required for account {line.account_id.code} - {line.account_id.name}."
                )
