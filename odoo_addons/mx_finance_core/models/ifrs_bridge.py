from __future__ import annotations

from decimal import Decimal

from odoo import api, models
from odoo.exceptions import UserError

from ..libs.finance_app.lease_engine import (
    LeaseContract,
    LeaseDiscountRate,
    LeaseEngine,
    LeasePaymentSchedule,
)
from ..libs.finance_app.transactions import TransactionManager


class IfrsBridge(models.AbstractModel):
    _name = "finance.ifrs.bridge"
    _description = "IFRS Bridge for embedded finance engines"

    @api.model
    def process_lease_schedule(self, contract_id, params):
        """Calculate IFRS16 schedule in memory and persist batched account moves."""
        contract = LeaseContract(
            contract_id=str(contract_id),
            company=params["company"],
            ledger_policy_ids=params.get("ledger_policy_ids", ["IFRS"]),
            counterparty=params["counterparty"],
            asset_class=params["asset_class"],
            commencement_date=params["commencement_date"],
            end_date=params["end_date"],
            short_term_exemption=params.get("short_term_exemption", False),
            low_value_exemption=params.get("low_value_exemption", False),
            purchase_option_reasonably_certain=params.get("purchase_option_reasonably_certain", False),
            initial_direct_costs=float(params.get("initial_direct_costs", 0)),
            incentives=float(params.get("incentives", 0)),
            prepayments=float(params.get("prepayments", 0)),
            restoration_provision=float(params.get("restoration_provision", 0)),
            payments=[
                LeasePaymentSchedule(
                    payment_date=item["payment_date"],
                    amount=float(item["amount"]),
                    currency=item["currency"],
                    fixed_in_substance_flag=item.get("fixed_in_substance_flag", True),
                    variable_flag=item.get("variable_flag", False),
                    index_type=item.get("index_type", "none"),
                    index_base_value=float(item.get("index_base_value", 0)),
                )
                for item in params["payments"]
            ],
        )
        discount_rate = LeaseDiscountRate(
            rate_type=params["rate_type"],
            currency=params["currency"],
            term_months=int(params["term_months"]),
            annual_rate=float(params["annual_rate"]),
            source=params.get("source", "odoo"),
            effective_date=params["effective_date"],
            locked_period=params.get("locked_period"),
        )

        existing_moves = self.env["account.move"].search([
            ("ref", "ilike", f"Amortización IFRS 16 - {contract_id}"),
            ("state", "!=", "cancel"),
        ], limit=1)
        if existing_moves:
            raise UserError("Ya existen asientos de amortización para este contrato. Cáncelalos antes de re-generar.")

        engine = LeaseEngine(TransactionManager())
        snapshot = engine.initial_measurement(contract, discount_rate, at_date=params["effective_date"])
        schedule = engine.amortization_schedule(contract, snapshot, discount_rate)

        move_vals = []
        for idx, line in enumerate(schedule, start=1):
            interest = Decimal(str(line.interest))
            principal = max(Decimal(str(line.payment)) - interest, Decimal("0.00"))
            total = (interest + principal).quantize(Decimal("0.01"))
            move_vals.append({
                "date": params["effective_date"],
                "ref": f"Amortización IFRS 16 - {contract_id} - {idx}",
                "journal_id": params["journal_id"],
                "line_ids": [
                    (0, 0, {
                        "account_id": params["interest_account"],
                        "name": "Gasto por Interés",
                        "debit": float(interest),
                        "credit": 0.0,
                    }),
                    (0, 0, {
                        "account_id": params["lease_liability_account"],
                        "name": "Pasivo por Arrendamiento",
                        "debit": float(principal),
                        "credit": 0.0,
                    }),
                    (0, 0, {
                        "account_id": params["offset_account"],
                        "name": "Contrapartida IFRS 16",
                        "debit": 0.0,
                        "credit": float(total),
                    }),
                ],
            })

        return self.env["account.move"].create(move_vals)
