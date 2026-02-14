from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
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
class LeaseRemeasurementResult:
    previous_snapshot: LeaseMeasurementSnapshot
    new_snapshot: LeaseMeasurementSnapshot
    delta_liability: float
    delta_rou_asset: float


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
    """Lease measurement engine aligned to IFRS 16 / NIF D-5 operational flow.

    The engine keeps calculation paths deterministic and quantized to 2 decimals
    for posting output while using Decimal internally to reduce floating-point drift.
    """

    _Q = Decimal("0.01")

    def __init__(self, manager: TransactionManager):
        self.manager = manager

    @classmethod
    def _to_decimal(cls, value: float | str | Decimal) -> Decimal:
        return Decimal(str(value)).quantize(cls._Q, rounding=ROUND_HALF_UP)

    @classmethod
    def _quantize(cls, value: Decimal) -> Decimal:
        return value.quantize(cls._Q, rounding=ROUND_HALF_UP)

    def validate_contract(self, contract: LeaseContract, rate: LeaseDiscountRate):
        """Validate core lease inputs before recognition.

        Technical reference:
        - IFRS 16 initial measurement of lease liability (PV of lease payments)
        - NIF D-5 aligned operational validation for payable schedule and discount rate.
        """
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
        """Compute day-1 lease liability PV and ROU asset.

        Uses Decimal arithmetic to reduce precision drift in long schedules.
        """
        self.validate_contract(contract, rate)
        included_payments = [self._to_decimal(p.amount) for p in contract.payments if not p.variable_flag]
        monthly_rate = Decimal(str(rate.annual_rate)) / Decimal("12")
        pv = Decimal("0")
        for i, amount in enumerate(included_payments, start=1):
            pv += amount / ((Decimal("1") + monthly_rate) ** i)

        rou = (
            pv
            + Decimal(str(contract.prepayments))
            + Decimal(str(contract.initial_direct_costs))
            - Decimal(str(contract.incentives))
            + Decimal(str(contract.restoration_provision))
        )
        assumptions_hash = (
            f"{contract.contract_id}|{rate.rate_type}|{rate.annual_rate}|{len(contract.payments)}|"
            f"{contract.short_term_exemption}|{contract.low_value_exemption}"
        )
        return LeaseMeasurementSnapshot(
            contract_id=contract.contract_id,
            at_date=at_date,
            lease_liability_pv=float(self._quantize(pv)),
            rou_asset=float(self._quantize(rou)),
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

        monthly_rate = Decimal(str(rate.annual_rate)) / Decimal("12")
        depreciation = Decimal(str(snapshot.rou_asset)) / Decimal(str(periods))
        liability = Decimal(str(snapshot.lease_liability_pv))
        rou_balance = Decimal(str(snapshot.rou_asset))
        lines: list[LeaseAmortizationLine] = []

        for idx, payment in enumerate(contract.payments, start=1):
            interest = liability * monthly_rate
            closing = liability + interest - Decimal(str(payment.amount))
            rou_balance = max(rou_balance - depreciation, Decimal("0"))
            lines.append(LeaseAmortizationLine(
                period=f"P{idx:03d}",
                opening_liability=float(self._quantize(liability)),
                interest=float(self._quantize(interest)),
                payment=float(self._quantize(Decimal(str(payment.amount)))),
                closing_liability=float(self._quantize(closing)),
                depreciation=float(self._quantize(depreciation)),
                rou_closing=float(self._quantize(rou_balance)),
            ))
            liability = closing
        return lines

    def validate_schedule_consistency(
        self,
        snapshot: LeaseMeasurementSnapshot,
        schedule: list[LeaseAmortizationLine],
        tolerance: float = 0.05,
    ) -> None:
        """Ensure schedule remains consistent with day-1 measurement.

        This is a practical QA control for year-end close:
        Opening liability (day-1 PV) should reconcile against cumulative
        interest/payment movement within tolerance.
        """
        if not schedule:
            return
        start = Decimal(str(snapshot.lease_liability_pv))
        end = Decimal(str(schedule[-1].closing_liability))
        total_interest = sum(Decimal(str(l.interest)) for l in schedule)
        total_payment = sum(Decimal(str(l.payment)) for l in schedule)
        expected_end = self._quantize(start + total_interest - total_payment)
        if abs(expected_end - end) > Decimal(str(tolerance)):
            raise ValueError(
                f"Inconsistencia de tabla de amortización: cierre esperado={expected_end} cierre_observado={end}"
            )

    def remeasure_with_history(
        self,
        contract: LeaseContract,
        previous_snapshot: LeaseMeasurementSnapshot,
        rate: LeaseDiscountRate,
        modification: "LeaseModification",
    ) -> LeaseRemeasurementResult:
        """Remeasure lease while preserving historical snapshot for audit trail."""
        new_snapshot = remeasure_contract(self, contract, rate, modification)
        return LeaseRemeasurementResult(
            previous_snapshot=previous_snapshot,
            new_snapshot=new_snapshot,
            delta_liability=round(new_snapshot.lease_liability_pv - previous_snapshot.lease_liability_pv, 2),
            delta_rou_asset=round(new_snapshot.rou_asset - previous_snapshot.rou_asset, 2),
        )

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


def recalculate_lease_liability(
    engine: LeaseEngine,
    contract: LeaseContract,
    new_rate: LeaseDiscountRate,
    new_payments: list[LeasePaymentSchedule],
    effective_date: str,
    reason: str = "ifrs16_modification",
) -> LeaseMeasurementSnapshot:
    """Recalculate lease liability/ROU for IFRS16 modifications without deleting history."""
    modification = LeaseModification(
        contract_id=contract.contract_id,
        reason=reason,
        effective_date=effective_date,
        new_payments=new_payments,
    )
    return remeasure_contract(engine, contract, new_rate, modification)
