from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


class AccountingStandard(str, Enum):
    NIF_MX = "NIF_MX"
    IFRS = "IFRS"
    US_GAAP = "US_GAAP"


@dataclass(frozen=True)
class StandardCapabilities:
    standard: AccountingStandard
    allows_revaluation_to_fair_value: bool
    requires_inflation_adjustment: bool
    depreciation_method_strict: bool
    component_depreciation: bool


GAAP_RULES: dict[AccountingStandard, StandardCapabilities] = {
    AccountingStandard.NIF_MX: StandardCapabilities(
        standard=AccountingStandard.NIF_MX,
        allows_revaluation_to_fair_value=False,
        requires_inflation_adjustment=True,
        depreciation_method_strict=False,
        component_depreciation=True,
    ),
    AccountingStandard.IFRS: StandardCapabilities(
        standard=AccountingStandard.IFRS,
        allows_revaluation_to_fair_value=True,
        requires_inflation_adjustment=False,
        depreciation_method_strict=False,
        component_depreciation=True,
    ),
    AccountingStandard.US_GAAP: StandardCapabilities(
        standard=AccountingStandard.US_GAAP,
        allows_revaluation_to_fair_value=False,
        requires_inflation_adjustment=False,
        depreciation_method_strict=True,
        component_depreciation=False,
    ),
}


@dataclass(frozen=True)
class LedgerContext:
    ledger_id: str
    ledger_name: str
    standard: AccountingStandard


@dataclass(frozen=True)
class DeferredTaxImpact:
    temporary_difference: Decimal
    deferred_tax_amount: Decimal
    entry_type: str = "IFRS_ADJUSTMENT"
    account: str = "DEFERRED_TAX_LIABILITY"
    is_dirty_accounting: bool = False


@dataclass(frozen=True)
class RevaluationImpact:
    ledger_id: str
    ledger_name: str
    standard: AccountingStandard
    action: str
    book_value_before: Decimal
    revaluation_adjustment: Decimal
    book_value_after: Decimal
    oci_surplus: Decimal
    deferred_tax: DeferredTaxImpact | None = None


class DeferredTaxManager:
    def __init__(self, tax_rate: Decimal = Decimal("0.30")):
        self.tax_rate = tax_rate

    def process_asset_difference(self, book_value: Decimal, tax_basis: Decimal) -> DeferredTaxImpact:
        temp_diff = _q(book_value - tax_basis)
        deferred_tax = _q(temp_diff * self.tax_rate)
        return DeferredTaxImpact(
            temporary_difference=temp_diff,
            deferred_tax_amount=deferred_tax,
        )




class GAAPRouter:
    """Rule gate used by import/posting pipelines before writing to a ledger."""

    def __init__(self, context_ledger: AccountingStandard | str):
        self.context = context_ledger if isinstance(context_ledger, AccountingStandard) else AccountingStandard(context_ledger)

    def capabilities(self) -> StandardCapabilities:
        return GAAP_RULES[self.context]

    def can_revalue_asset(self) -> bool:
        return self.capabilities().allows_revaluation_to_fair_value

    def get_depreciation_method(self, asset_type: str = "generic") -> str:
        _ = asset_type
        caps = self.capabilities()
        if self.context == AccountingStandard.US_GAAP and caps.depreciation_method_strict:
            return "STRAIGHT_LINE_STRICT"
        if caps.component_depreciation:
            return "COMPONENT"
        return "STRAIGHT_LINE"


class AssetRevaluationRouter:
    def __init__(self, deferred_tax_manager: DeferredTaxManager | None = None):
        self.deferred_tax_manager = deferred_tax_manager or DeferredTaxManager()

    def process_revaluation(
        self,
        ledgers: list[LedgerContext],
        current_book_values: dict[str, Decimal],
        new_fair_value: Decimal,
        tax_basis_by_ledger: dict[str, Decimal] | None = None,
    ) -> list[RevaluationImpact]:
        tax_basis_by_ledger = tax_basis_by_ledger or {}
        impacts: list[RevaluationImpact] = []

        for ledger in ledgers:
            capabilities = GAAP_RULES[ledger.standard]
            before = _q(current_book_values.get(ledger.ledger_id, Decimal("0")))

            if not capabilities.allows_revaluation_to_fair_value:
                impacts.append(
                    RevaluationImpact(
                        ledger_id=ledger.ledger_id,
                        ledger_name=ledger.ledger_name,
                        standard=ledger.standard,
                        action="SKIPPED_RULE_VIOLATION",
                        book_value_before=before,
                        revaluation_adjustment=Decimal("0.00"),
                        book_value_after=before,
                        oci_surplus=Decimal("0.00"),
                    )
                )
                continue

            surplus = _q(new_fair_value - before)
            after = _q(before + surplus)
            deferred_tax = None
            if surplus > 0:
                tax_basis = _q(tax_basis_by_ledger.get(ledger.ledger_id, before))
                deferred_tax = self.deferred_tax_manager.process_asset_difference(after, tax_basis)

            impacts.append(
                RevaluationImpact(
                    ledger_id=ledger.ledger_id,
                    ledger_name=ledger.ledger_name,
                    standard=ledger.standard,
                    action="SUCCESS" if surplus > 0 else "NO_UPLIFT",
                    book_value_before=before,
                    revaluation_adjustment=surplus,
                    book_value_after=after,
                    oci_surplus=surplus if surplus > 0 else Decimal("0.00"),
                    deferred_tax=deferred_tax,
                )
            )

        return impacts


def run_monthly_depreciation_by_ledger(base_value_by_ledger: dict[str, Decimal], remaining_life_months: int) -> dict[str, Decimal]:
    if remaining_life_months <= 0:
        raise ValueError("remaining_life_months debe ser mayor a cero")
    return {ledger_id: _q(value / Decimal(str(remaining_life_months))) for ledger_id, value in base_value_by_ledger.items()}


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
