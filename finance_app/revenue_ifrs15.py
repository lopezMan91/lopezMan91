from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RecognitionPattern = Literal["point_in_time", "over_time"]
RoleAssessment = Literal["principal", "agent"]


@dataclass
class PerformanceObligation:
    pob_id: str
    description: str
    standalone_selling_price: float
    recognition_pattern: RecognitionPattern
    role: RoleAssessment = "principal"
    expected_total_progress_units: float = 1.0


@dataclass
class RevenueContract:
    contract_id: str
    customer: str
    transaction_price: float
    pobs: list[PerformanceObligation]
    variable_consideration_estimate: float = 0.0
    variable_consideration_constraint: float = 0.0
    significant_financing_adjustment: float = 0.0

    def constrained_transaction_price(self) -> float:
        return round(
            self.transaction_price
            + self.variable_consideration_estimate
            - self.variable_consideration_constraint
            + self.significant_financing_adjustment,
            2,
        )


@dataclass
class RevenueRecognitionLine:
    pob_id: str
    recognized_gross: float
    recognized_net: float
    role: RoleAssessment


@dataclass
class ContractRollforward:
    opening_contract_asset: float
    opening_contract_liability: float
    billed_amount: float
    recognized_revenue: float
    closing_contract_asset: float
    closing_contract_liability: float


class RevenueEngineIFRS15:
    def estimate_variable_consideration(
        self,
        scenarios: list[tuple[float, float]],
        method: Literal["expected_value", "most_likely"] = "expected_value",
        constraint: float = 0.0,
    ) -> float:
        """Estimate variable consideration with optional constraint.

        scenarios: list of tuples (amount, probability).
        """
        if not scenarios:
            return 0.0
        if method == "expected_value":
            estimate = sum(amount * prob for amount, prob in scenarios)
        else:
            estimate = max(scenarios, key=lambda x: x[1])[0]
        return round(max(estimate - constraint, 0.0), 2)

    def split_significant_financing_component(
        self,
        cash_price: float,
        deferred_price: float,
    ) -> dict[str, float]:
        """Split revenue vs financing component for long-term settlements."""
        if cash_price < 0 or deferred_price < 0:
            raise ValueError("Precios no pueden ser negativos")
        financing = max(deferred_price - cash_price, 0.0)
        return {
            "revenue_component": round(cash_price, 2),
            "financing_component": round(financing, 2),
        }

    def allocate_transaction_price(self, contract: RevenueContract) -> dict[str, float]:
        total_ssp = sum(p.standalone_selling_price for p in contract.pobs)
        if total_ssp <= 0:
            raise ValueError("La suma de SSP debe ser mayor a cero")

        alloc_base = contract.constrained_transaction_price()
        allocations: dict[str, float] = {}
        for pob in contract.pobs:
            ratio = pob.standalone_selling_price / total_ssp
            allocations[pob.pob_id] = round(alloc_base * ratio, 2)
        return allocations

    def assess_principal_vs_agent(
        self,
        controls_before_transfer: bool,
        inventory_risk: bool = False,
        price_discretion: bool = False,
    ) -> RoleAssessment:
        if controls_before_transfer:
            return "principal"
        if inventory_risk or price_discretion:
            return "principal"
        return "agent"

    def recognize_revenue(
        self,
        contract: RevenueContract,
        progress_by_pob: dict[str, float],
        agent_commission_rate: float = 0.1,
    ) -> list[RevenueRecognitionLine]:
        if not 0 <= agent_commission_rate <= 1:
            raise ValueError("agent_commission_rate debe estar entre 0 y 1")

        allocations = self.allocate_transaction_price(contract)
        lines: list[RevenueRecognitionLine] = []

        for pob in contract.pobs:
            progress = progress_by_pob.get(pob.pob_id, 0.0)
            if pob.recognition_pattern == "point_in_time":
                progress = 1.0 if progress >= 1.0 else 0.0
            else:
                progress = min(max(progress, 0.0), 1.0)

            gross = round(allocations[pob.pob_id] * progress, 2)
            net = gross if pob.role == "principal" else round(gross * agent_commission_rate, 2)
            lines.append(
                RevenueRecognitionLine(
                    pob_id=pob.pob_id,
                    recognized_gross=gross,
                    recognized_net=net,
                    role=pob.role,
                )
            )

        return lines

    def compute_contract_rollforward(
        self,
        opening_contract_asset: float,
        opening_contract_liability: float,
        billed_amount: float,
        recognized_revenue: float,
    ) -> ContractRollforward:
        net_position = (opening_contract_asset - opening_contract_liability) + recognized_revenue - billed_amount
        closing_asset = max(net_position, 0.0)
        closing_liability = max(-net_position, 0.0)
        return ContractRollforward(
            opening_contract_asset=round(opening_contract_asset, 2),
            opening_contract_liability=round(opening_contract_liability, 2),
            billed_amount=round(billed_amount, 2),
            recognized_revenue=round(recognized_revenue, 2),
            closing_contract_asset=round(closing_asset, 2),
            closing_contract_liability=round(closing_liability, 2),
        )

    def classify_warranty(self, provides_additional_service: bool) -> str:
        return "service_type_pob" if provides_additional_service else "assurance"

    def classify_license(self, requires_ongoing_updates_or_support: bool) -> str:
        return "right_to_access" if requires_ongoing_updates_or_support else "right_to_use"

    def apply_contract_modification(
        self,
        contract: RevenueContract,
        delta_transaction_price: float,
    ) -> RevenueContract:
        return RevenueContract(
            contract_id=contract.contract_id,
            customer=contract.customer,
            transaction_price=round(contract.transaction_price + delta_transaction_price, 2),
            pobs=contract.pobs,
            variable_consideration_estimate=contract.variable_consideration_estimate,
            variable_consideration_constraint=contract.variable_consideration_constraint,
            significant_financing_adjustment=contract.significant_financing_adjustment,
        )
