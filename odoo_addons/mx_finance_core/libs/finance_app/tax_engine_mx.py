from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from .transactions import PolicyLine

IVA_16 = Decimal('0.16')
IVA_0 = Decimal('0.00')
IvaRate = Literal["16", "0"]
IvaKind = Literal["16", "0", "exento", "no_objeto"]


@dataclass
class TaxEvidencePack:
    xml_attached: bool = False
    pdf_attached: bool = False
    payment_proof_attached: bool = False
    contract_attached: bool = False

    def is_complete(self) -> bool:
        return self.xml_attached and self.pdf_attached and self.payment_proof_attached


@dataclass
class TaxLineAttributes:
    deductible: bool = True
    non_deductible_reason: str = ""
    deductible_percent: float = 100.0
    iva_kind: IvaKind = "16"
    iva_creditable: bool = True
    iva_non_creditable_reason: str = ""
    withheld_iva_rate: float = 0.0
    withheld_isr_rate: float = 0.0
    cfdi_uuid: str = ""
    cfdi_rfc_issuer: str = ""
    cfdi_usage: str = ""
    payment_method: str = ""
    payment_form: str = ""
    evidence: TaxEvidencePack = field(default_factory=TaxEvidencePack)

    def __post_init__(self):
        if not 0 <= self.deductible_percent <= 100:
            raise ValueError("deductible_percent debe estar entre 0 y 100")
        if self.iva_kind not in {"16", "0", "exento", "no_objeto"}:
            raise ValueError(f"iva_kind inválido: {self.iva_kind}")
        for rate in (self.withheld_iva_rate, self.withheld_isr_rate):
            if not 0 <= rate <= 1:
                raise ValueError("Las tasas de retención deben estar entre 0 y 1")

    def iva_rate(self) -> Decimal:
        return IVA_16 if self.iva_kind == "16" else IVA_0


@dataclass
class FiscalLine:
    line_id: str
    vendor_rfc: str
    concept: str
    base_amount: Decimal
    attrs: TaxLineAttributes

    def __post_init__(self):
        self.base_amount = Decimal(str(self.base_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if self.base_amount < 0:
            raise ValueError("base_amount no puede ser negativo")
        if not self.line_id:
            raise ValueError("line_id es obligatorio")


@dataclass
class TemporaryDifference:
    code: str
    carrying_amount: float
    tax_base: float
    tax_rate: float

    def __post_init__(self):
        if not 0 <= self.tax_rate <= 1:
            raise ValueError("tax_rate debe estar entre 0 y 1")

    def difference(self) -> float:
        return self.carrying_amount - self.tax_base

    def deferred_tax(self) -> float:
        return self.difference() * self.tax_rate


@dataclass
class ISRReconciliationResult:
    accounting_profit: Decimal
    permanent_add_backs: Decimal
    permanent_deductions: Decimal
    temporary_add_backs: Decimal
    temporary_deductions: Decimal
    taxable_profit: Decimal


@dataclass
class IVASummaryResult:
    transferred_iva: Decimal
    creditable_iva: Decimal
    non_creditable_iva: Decimal
    withheld_iva: Decimal
    withheld_isr: Decimal
    diot_by_vendor: dict[str, Decimal]
    blocked_lines: list[str]




@dataclass(frozen=True)
class TaxRateProvider:
    """Configurable rates provider (can be backed by Odoo tables)."""

    rates: dict[str, Decimal] | None = None

    def get_rate(self, code: str, as_of: str | None = None) -> Decimal:
        _ = as_of
        configured = self.rates or {}
        if code not in configured:
            raise ValueError(f"Tasa de impuesto no configurada: {code}")
        return Decimal(str(configured[code]))


class TaxEngineMX:
    def __init__(self, rate_provider: TaxRateProvider | None = None):
        self.rate_provider = rate_provider or TaxRateProvider()

    def compute_iva_summary(self, lines: list[FiscalLine]) -> IVASummaryResult:
        transferred = Decimal('0.00')
        creditable = Decimal('0.00')
        non_creditable = Decimal('0.00')
        withheld_iva = Decimal('0.00')
        withheld_isr = Decimal('0.00')
        diot: dict[str, Decimal] = {}
        blocked: list[str] = []

        for line in lines:
            attrs = line.attrs
            if attrs.iva_kind == "16":
                rate = self.rate_provider.get_rate("IVA_GENERAL")
            else:
                rate = attrs.iva_rate()
            line_iva = line.base_amount * rate

            transferred += line_iva
            withheld_iva += line.base_amount * Decimal(str(attrs.withheld_iva_rate))
            withheld_isr += line.base_amount * Decimal(str(attrs.withheld_isr_rate))

            if attrs.iva_creditable and attrs.evidence.is_complete():
                creditable += line_iva
                diot[line.vendor_rfc] = diot.get(line.vendor_rfc, Decimal('0.00')) + line.base_amount
            else:
                non_creditable += line_iva
                blocked.append(line.line_id)

        return IVASummaryResult(
            transferred_iva=transferred.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            creditable_iva=creditable.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            non_creditable_iva=non_creditable.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            withheld_iva=withheld_iva.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            withheld_isr=withheld_isr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            diot_by_vendor={k: v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for k, v in diot.items()},
            blocked_lines=blocked,
        )

    def compute_isr_reconciliation(
        self,
        accounting_profit: float,
        permanent_add_backs: float = 0.0,
        permanent_deductions: float = 0.0,
        temporary_add_backs: float = 0.0,
        temporary_deductions: float = 0.0,
    ) -> ISRReconciliationResult:
        accounting_profit_d = Decimal(str(accounting_profit))
        permanent_add_backs_d = Decimal(str(permanent_add_backs))
        permanent_deductions_d = Decimal(str(permanent_deductions))
        temporary_add_backs_d = Decimal(str(temporary_add_backs))
        temporary_deductions_d = Decimal(str(temporary_deductions))
        taxable = (
            accounting_profit_d
            + permanent_add_backs_d
            - permanent_deductions_d
            + temporary_add_backs_d
            - temporary_deductions_d
        )
        return ISRReconciliationResult(
            accounting_profit=accounting_profit_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            permanent_add_backs=permanent_add_backs_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            permanent_deductions=permanent_deductions_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            temporary_add_backs=temporary_add_backs_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            temporary_deductions=temporary_deductions_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            taxable_profit=taxable.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        )

    def compute_ptu_legal_cap(self, monthly_salary: float, avg_ptu_last_3_years: float) -> Decimal:
        if monthly_salary < 0 or avg_ptu_last_3_years < 0:
            raise ValueError("Parámetros PTU no pueden ser negativos")
        three_months = Decimal(str(monthly_salary)) * self.rate_provider.get_rate("PTU_MONTHS_CAP")
        return max(three_months, Decimal(str(avg_ptu_last_3_years))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def compute_ptu_legal_for_employee(
        self,
        proportional_amount: float,
        monthly_salary: float,
        avg_ptu_last_3_years: float,
    ) -> Decimal:
        cap = self.compute_ptu_legal_cap(monthly_salary, avg_ptu_last_3_years)
        return min(Decimal(str(proportional_amount)), cap).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def compute_deferred_tax_totals(self, differences: list[TemporaryDifference]) -> dict[str, float]:
        dta = 0.0
        dtl = 0.0
        movement_by_code: dict[str, float] = {}

        for diff in differences:
            amount = round(diff.deferred_tax(), 2)
            movement_by_code[diff.code] = amount
            if amount >= 0:
                dtl += amount
            else:
                dta += abs(amount)

        return {
            "dta_total": round(dta, 2),
            "dtl_total": round(dtl, 2),
            "net_deferred_tax": round(dtl - dta, 2),
            "movement_count": len(differences),
            "movement_by_code": movement_by_code,
        }

    def build_deferred_tax_policy_lines(
        self,
        policy_id: str,
        posting_date: str,
        differences: list[TemporaryDifference],
        ledger_tag: str = "ledger_ifrs",
        dta_account: str = "1705",
        dtl_account: str = "2705",
        p_and_l_account: str = "7301",
    ) -> list[PolicyLine]:
        """Generate automatic deferred tax entry lines (NIF D-4 / IAS 12)."""
        totals = self.compute_deferred_tax_totals(differences)
        net = totals["net_deferred_tax"]
        if round(net, 2) == 0:
            return []

        if net > 0:
            return [
                PolicyLine(policy_id, posting_date, "Gasto por impuesto diferido", p_and_l_account, net, 0, ledger_tag),
                PolicyLine(policy_id, posting_date, "Pasivo por impuesto diferido", dtl_account, 0, net, ledger_tag),
            ]

        amount = abs(net)
        return [
            PolicyLine(policy_id, posting_date, "Activo por impuesto diferido", dta_account, amount, 0, ledger_tag),
            PolicyLine(policy_id, posting_date, "Ingreso por impuesto diferido", p_and_l_account, 0, amount, ledger_tag),
        ]


class TaxAssetEngine:
    """Tax bridge for fixed assets (MOI + INPC updates) without touching book layer."""

    @staticmethod
    def calculate_tax_deduction(moi: Decimal, inpc_acquisition: Decimal, inpc_current: Decimal, rate: Decimal) -> Decimal:
        if any(v <= 0 for v in (moi, inpc_acquisition, inpc_current)):
            raise ValueError("MOI e índices INPC deben ser positivos")
        if not Decimal("0") <= rate <= Decimal("1"):
            raise ValueError("rate debe estar entre 0 y 1")
        factor = (inpc_current / inpc_acquisition).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        deduction_period = moi * rate * factor
        return deduction_period.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class TaxLossCarryforward:
    fiscal_year: int
    available_amount: float


def compute_dta_from_tax_losses(
    losses: list[TaxLossCarryforward],
    isr_rate: float = 0.30,
    probable_future_profit: bool = True,
) -> float:
    if not probable_future_profit:
        return 0.0
    if not 0 <= isr_rate <= 1:
        raise ValueError("isr_rate debe estar entre 0 y 1")
    total_loss = sum(max(loss.available_amount, 0.0) for loss in losses)
    return round(total_loss * isr_rate, 2)


@dataclass(frozen=True)
class DeferredTaxCalculation:
    temp_difference: Decimal
    deferred_tax: Decimal
    type: str
    ledger_target: str = "IFRS_ADJUSTMENTS"


class DeferredTaxCalculator:
    """NIF D-4 / IAS 12 calculator anchored to ledger adjustment layer."""

    def __init__(self, tax_rate: Decimal | None = None, rate_provider: TaxRateProvider | None = None):
        if tax_rate is None:
            provider = rate_provider or TaxRateProvider()
            tax_rate = provider.get_rate("ISR_CORPORATE")
        if not Decimal("0") <= tax_rate <= Decimal("1"):
            raise ValueError("tax_rate debe estar entre 0 y 1")
        self.tax_rate = tax_rate

    def calculate_nif_d4_impact(self, book_value: Decimal, tax_basis: Decimal) -> DeferredTaxCalculation | None:
        difference = (book_value - tax_basis).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if difference == Decimal('0.00'):
            return None

        deferred_tax = (abs(difference) * self.tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        impact_type = "DTL" if difference > 0 else "DTA"
        return DeferredTaxCalculation(
            temp_difference=difference,
            deferred_tax=deferred_tax,
            type=impact_type,
        )
