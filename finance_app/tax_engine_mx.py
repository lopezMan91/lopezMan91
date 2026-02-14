from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

IvaRate = Literal[0.0, 0.16]
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

    def iva_rate(self) -> IvaRate:
        return 0.16 if self.iva_kind == "16" else 0.0


@dataclass
class FiscalLine:
    line_id: str
    vendor_rfc: str
    concept: str
    base_amount: float
    attrs: TaxLineAttributes

    def __post_init__(self):
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
    accounting_profit: float
    permanent_add_backs: float
    permanent_deductions: float
    temporary_add_backs: float
    temporary_deductions: float
    taxable_profit: float


@dataclass
class IVASummaryResult:
    transferred_iva: float
    creditable_iva: float
    non_creditable_iva: float
    withheld_iva: float
    withheld_isr: float
    diot_by_vendor: dict[str, float]
    blocked_lines: list[str]


class TaxEngineMX:
    def compute_iva_summary(self, lines: list[FiscalLine]) -> IVASummaryResult:
        transferred = 0.0
        creditable = 0.0
        non_creditable = 0.0
        withheld_iva = 0.0
        withheld_isr = 0.0
        diot: dict[str, float] = {}
        blocked: list[str] = []

        for line in lines:
            attrs = line.attrs
            rate = attrs.iva_rate()
            line_iva = line.base_amount * rate

            transferred += line_iva
            withheld_iva += line.base_amount * attrs.withheld_iva_rate
            withheld_isr += line.base_amount * attrs.withheld_isr_rate

            if attrs.iva_creditable and attrs.evidence.is_complete():
                creditable += line_iva
                diot[line.vendor_rfc] = diot.get(line.vendor_rfc, 0.0) + line.base_amount
            else:
                non_creditable += line_iva
                blocked.append(line.line_id)

        return IVASummaryResult(
            transferred_iva=round(transferred, 2),
            creditable_iva=round(creditable, 2),
            non_creditable_iva=round(non_creditable, 2),
            withheld_iva=round(withheld_iva, 2),
            withheld_isr=round(withheld_isr, 2),
            diot_by_vendor={k: round(v, 2) for k, v in diot.items()},
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
        taxable = (
            accounting_profit
            + permanent_add_backs
            - permanent_deductions
            + temporary_add_backs
            - temporary_deductions
        )
        return ISRReconciliationResult(
            accounting_profit=round(accounting_profit, 2),
            permanent_add_backs=round(permanent_add_backs, 2),
            permanent_deductions=round(permanent_deductions, 2),
            temporary_add_backs=round(temporary_add_backs, 2),
            temporary_deductions=round(temporary_deductions, 2),
            taxable_profit=round(taxable, 2),
        )

    def compute_ptu_legal_cap(self, monthly_salary: float, avg_ptu_last_3_years: float) -> float:
        if monthly_salary < 0 or avg_ptu_last_3_years < 0:
            raise ValueError("Parámetros PTU no pueden ser negativos")
        three_months = monthly_salary * 3
        return max(three_months, avg_ptu_last_3_years)

    def compute_ptu_legal_for_employee(
        self,
        proportional_amount: float,
        monthly_salary: float,
        avg_ptu_last_3_years: float,
    ) -> float:
        cap = self.compute_ptu_legal_cap(monthly_salary, avg_ptu_last_3_years)
        return round(min(proportional_amount, cap), 2)

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
