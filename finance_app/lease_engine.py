from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from .transactions import PolicyLine, TransactionManager


RateType = Literal["implicit", "IBR", "risk_free"]
LedgerCode = Literal["LOCAL", "IFRS"]


@dataclass
class LeaseDiscountRate:
    rate_type: RateType
    currency: str
    term_months: int
    annual_rate: float
    source: str
    effective_date: str
    locked_period: str | None = None


@dataclass
class LeasePaymentSchedule:
    payment_date: str
    amount: float
    currency: str
    fixed_in_substance_flag: bool = True
    variable_flag: bool = False
    index_type: str = "none"
    index_base_value: float = 0.0


@dataclass
class LeaseContract:
    contract_id: str
    company: str
    ledger_policy_ids: list[LedgerCode]
    counterparty: str
    asset_class: str
    commencement_date: str
    end_date: str
    short_term_exemption: bool = False
    low_value_exemption: bool = False
    purchase_option_reasonably_certain: bool = False
    initial_direct_costs: float = 0.0
    incentives: float = 0.0
    prepayments: float = 0.0
    restoration_provision: float = 0.0
    payments: list[LeasePaymentSchedule] = field(default_factory=list)


@dataclass
class LeaseMeasurementSnapshot:
    contract_id: str
    at_date: str
    lease_liability_pv: float
    rou_asset: float
    remeasurement_reason: str
    assumptions_hash: str


@dataclass
class LeaseAmortizationLine:
    period: str
    opening_liability: float
    interest: float
    payment: float
    closing_liability: float
    depreciation: float
    rou_closing: float


@dataclass
class LeasePostingBatch:
    contract_id: str
    ledger: LedgerCode
    posting_period: str
    status: str
    audit_log: list[str] = field(default_factory=list)


class LeaseEngine:
    def __init__(self, manager: TransactionManager):
        self.manager = manager

    def validate_contract(self, contract: LeaseContract, rate: LeaseDiscountRate):
        if not contract.payments:
            raise ValueError("Contrato sin calendario de pagos")
        if rate.annual_rate <= 0:
            raise ValueError("Contrato sin tasa aprobada")
        if contract.short_term_exemption or contract.low_value_exemption:
            return
        for payment in contract.payments:
            if payment.amount <= 0:
                raise ValueError("Pago inválido en calendario")
            if payment.currency != rate.currency:
                raise ValueError("Moneda de pago no cuadra con moneda de tasa")

    def initial_measurement(
        self,
        contract: LeaseContract,
        rate: LeaseDiscountRate,
        at_date: str,
        reason: str = "day1",
    ) -> LeaseMeasurementSnapshot:
        self.validate_contract(contract, rate)
        included_payments = [p.amount for p in contract.payments if not p.variable_flag]
        monthly_rate = rate.annual_rate / 12
        pv = 0.0
        for i, amount in enumerate(included_payments, start=1):
            pv += amount / ((1 + monthly_rate) ** i)

        rou = pv + contract.prepayments + contract.initial_direct_costs - contract.incentives + contract.restoration_provision
        assumptions_hash = (
            f"{contract.contract_id}|{rate.rate_type}|{rate.annual_rate}|{len(contract.payments)}|"
            f"{contract.short_term_exemption}|{contract.low_value_exemption}"
        )
        return LeaseMeasurementSnapshot(
            contract_id=contract.contract_id,
            at_date=at_date,
            lease_liability_pv=round(pv, 2),
            rou_asset=round(rou, 2),
            remeasurement_reason=reason,
            assumptions_hash=assumptions_hash,
        )

    def amortization_schedule(
        self,
        contract: LeaseContract,
        snapshot: LeaseMeasurementSnapshot,
        rate: LeaseDiscountRate,
    ) -> list[LeaseAmortizationLine]:
        periods = len(contract.payments)
        if periods == 0:
            return []

        monthly_rate = rate.annual_rate / 12
        depreciation = snapshot.rou_asset / periods
        liability = snapshot.lease_liability_pv
        rou_balance = snapshot.rou_asset
        lines: list[LeaseAmortizationLine] = []

        for idx, payment in enumerate(contract.payments, start=1):
            interest = liability * monthly_rate
            closing = liability + interest - payment.amount
            rou_balance = max(rou_balance - depreciation, 0)
            lines.append(LeaseAmortizationLine(
                period=f"P{idx:03d}",
                opening_liability=round(liability, 2),
                interest=round(interest, 2),
                payment=round(payment.amount, 2),
                closing_liability=round(closing, 2),
                depreciation=round(depreciation, 2),
                rou_closing=round(rou_balance, 2),
            ))
            liability = closing
        return lines

    def post_period(
        self,
        contract: LeaseContract,
        line: LeaseAmortizationLine,
        ledger: LedgerCode,
    ) -> LeasePostingBatch:
        policy_id = f"LEASE-{contract.contract_id}-{ledger}-{line.period}"
        self.manager.post_policy_lines([
            PolicyLine(policy_id, contract.commencement_date, "Interés arrendamiento", "5200", line.interest, 0, f"ledger_{ledger.lower()}"),
            PolicyLine(policy_id, contract.commencement_date, "Pasivo arrendamiento", "2105", 0, line.interest, f"ledger_{ledger.lower()}"),
            PolicyLine(policy_id, contract.commencement_date, "Depreciación ROU", "6105", line.depreciation, 0, f"ledger_{ledger.lower()}"),
            PolicyLine(policy_id, contract.commencement_date, "ROU acumulada", "1805", 0, line.depreciation, f"ledger_{ledger.lower()}"),
            PolicyLine(policy_id, contract.commencement_date, "Pago arrendamiento", "2105", line.payment, 0, f"ledger_{ledger.lower()}"),
            PolicyLine(policy_id, contract.commencement_date, "Bancos", "1010", 0, line.payment, f"ledger_{ledger.lower()}"),
        ])
        return LeasePostingBatch(
            contract_id=contract.contract_id,
            ledger=ledger,
            posting_period=line.period,
            status="posted",
            audit_log=[
                f"Contrato {contract.contract_id}",
                f"Ledger {ledger}",
                f"Interés {line.interest}",
                f"Depreciación {line.depreciation}",
                f"Pago {line.payment}",
            ],
        )


@dataclass
class LeaseModification:
    contract_id: str
    reason: str
    effective_date: str
    new_payments: list[LeasePaymentSchedule]


def remeasure_contract(
    engine: LeaseEngine,
    contract: LeaseContract,
    rate: LeaseDiscountRate,
    modification: LeaseModification,
) -> LeaseMeasurementSnapshot:
    updated = LeaseContract(**{**contract.__dict__, "payments": modification.new_payments})
    return engine.initial_measurement(updated, rate, modification.effective_date, reason=modification.reason)
