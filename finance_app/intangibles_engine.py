from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal


IntangiblePhase = Literal["research", "development"]
IntangibleModel = Literal["cost", "revaluation"]


@dataclass
class IntangibleEvidence:
    technical_feasibility: bool = False
    intent_to_complete: bool = False
    ability_to_use_or_sell: bool = False
    probable_future_benefits: bool = False
    resources_available: bool = False
    costs_reliably_measurable: bool = False

    def development_gate_passed(self) -> bool:
        return all(
            [
                self.technical_feasibility,
                self.intent_to_complete,
                self.ability_to_use_or_sell,
                self.probable_future_benefits,
                self.resources_available,
                self.costs_reliably_measurable,
            ]
        )


@dataclass
class IntangibleTransaction:
    tx_id: str
    tx_date: date
    amount: float
    phase: IntangiblePhase
    description: str = ""
    approved_for_capitalization: bool = False


@dataclass
class IntangibleAsset:
    asset_id: str
    name: str
    entity: str
    profit_center: str
    project: str
    currency: str
    useful_life_months: int | None
    residual_value: float = 0.0
    model: IntangibleModel = "cost"
    has_active_market: bool = False
    in_service_date: date | None = None
    gross_carrying_amount: float = 0.0
    accumulated_amortization: float = 0.0
    accumulated_impairment: float = 0.0
    expense_locked_amount: float = 0.0
    transactions: list[IntangibleTransaction] = field(default_factory=list)

    def __post_init__(self):
        if self.useful_life_months is not None and self.useful_life_months <= 0:
            raise ValueError("useful_life_months debe ser positivo o None (vida indefinida)")
        if self.model == "revaluation" and not self.has_active_market:
            raise ValueError("Modelo de revaluación requiere mercado activo")

    @property
    def is_indefinite_life(self) -> bool:
        return self.useful_life_months is None

    @property
    def carrying_amount(self) -> float:
        return round(self.gross_carrying_amount - self.accumulated_amortization - self.accumulated_impairment, 2)


@dataclass
class IntangibleRollforward:
    opening_gross: float
    additions: float
    disposals: float
    amortization: float
    impairment: float
    closing_carrying_amount: float


class IntangiblesEngine:
    def classify_rd_cost(
        self,
        asset: IntangibleAsset,
        transaction: IntangibleTransaction,
        evidence: IntangibleEvidence,
    ) -> str:
        """Return classification: expense or capitalize, and apply anti-recapture rule."""
        if transaction.amount < 0:
            raise ValueError("transaction.amount no puede ser negativo")

        if transaction.phase == "research":
            asset.expense_locked_amount += transaction.amount
            asset.transactions.append(transaction)
            return "expense"

        if not transaction.approved_for_capitalization or not evidence.development_gate_passed():
            asset.expense_locked_amount += transaction.amount
            asset.transactions.append(transaction)
            return "expense"

        asset.gross_carrying_amount += transaction.amount
        asset.transactions.append(transaction)
        return "capitalize"

    def post_addition(self, asset: IntangibleAsset, amount: float):
        if amount < 0:
            raise ValueError("amount no puede ser negativo")
        asset.gross_carrying_amount += amount

    def post_disposal(self, asset: IntangibleAsset, amount: float):
        if amount < 0:
            raise ValueError("amount no puede ser negativo")
        asset.gross_carrying_amount -= amount
        if asset.gross_carrying_amount < 0:
            raise ValueError("Disposal excede valor bruto")

    def amortization_for_period(self, asset: IntangibleAsset) -> float:
        if asset.is_indefinite_life:
            return 0.0
        depreciable_base = max(asset.gross_carrying_amount - asset.residual_value, 0)
        monthly = depreciable_base / float(asset.useful_life_months or 1)
        return round(monthly, 2)

    def post_amortization(self, asset: IntangibleAsset, amount: float | None = None) -> float:
        amort = self.amortization_for_period(asset) if amount is None else amount
        if amort < 0:
            raise ValueError("Amortización no puede ser negativa")
        asset.accumulated_amortization += amort
        return round(amort, 2)

    def post_impairment(self, asset: IntangibleAsset, amount: float):
        if amount < 0:
            raise ValueError("Impairment no puede ser negativo")
        asset.accumulated_impairment += amount

    def simulate_amortization_schedule(self, asset: IntangibleAsset, periods: int) -> list[float]:
        if periods <= 0:
            raise ValueError("periods debe ser positivo")
        schedule: list[float] = []
        periodic = self.amortization_for_period(asset)
        if periodic == 0:
            return [0.0 for _ in range(periods)]
        remaining = asset.carrying_amount
        for _ in range(periods):
            this_period = min(periodic, max(remaining, 0))
            schedule.append(round(this_period, 2))
            remaining -= this_period
        return schedule

    def build_rollforward(
        self,
        opening_gross: float,
        additions: float,
        disposals: float,
        amortization: float,
        impairment: float,
    ) -> IntangibleRollforward:
        closing = opening_gross + additions - disposals - amortization - impairment
        return IntangibleRollforward(
            opening_gross=round(opening_gross, 2),
            additions=round(additions, 2),
            disposals=round(disposals, 2),
            amortization=round(amortization, 2),
            impairment=round(impairment, 2),
            closing_carrying_amount=round(closing, 2),
        )

    def classify_saas_or_website_cost(
        self,
        creates_controlled_resource: bool,
        purpose_marketing_only: bool,
    ) -> str:
        if purpose_marketing_only:
            return "expense"
        return "capitalize" if creates_controlled_resource else "expense"
