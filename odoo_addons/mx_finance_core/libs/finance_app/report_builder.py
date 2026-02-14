from __future__ import annotations

from dataclasses import dataclass, field

from .transactions import Transaction


@dataclass
class ReportingTemplate:
    code: str
    name: str
    ledger_code: str
    mapping: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class LedgerReport:
    ledger_code: str
    sections: dict[str, float]
    drilldown: dict[str, list[Transaction]]


class FinancialStatementBuilder:
    def __init__(self, templates: list[ReportingTemplate]):
        self.templates = {t.code: t for t in templates}

    def build(self, template_code: str, transactions: list[Transaction]) -> LedgerReport:
        template = self.templates[template_code]
        scoped = [t for t in transactions if t.category.startswith(f"ledger_{template.ledger_code.lower()}")]

        sections: dict[str, float] = {}
        drilldown: dict[str, list[Transaction]] = {}

        for section, account_tokens in template.mapping.items():
            detail = [t for t in scoped if any(token in t.category for token in account_tokens)]
            drilldown[section] = detail
            sections[section] = round(sum(t.amount for t in detail), 2)

        return LedgerReport(ledger_code=template.ledger_code, sections=sections, drilldown=drilldown)


def default_templates() -> list[ReportingTemplate]:
    return [
        ReportingTemplate(
            code="BAL_LOCAL",
            name="Balance Local",
            ledger_code="LOCAL",
            mapping={
                "Activos": [":1", ":10", ":11", ":12"],
                "Pasivos": [":2", ":20", ":21", ":22"],
                "Capital": [":3", ":30", ":31"],
            },
        ),
        ReportingTemplate(
            code="PL_IFRS",
            name="Resultados IFRS",
            ledger_code="IFRS",
            mapping={
                "Ingresos": [":4", ":40", ":41"],
                "Costos/Gastos": [":5", ":50", ":51", ":60"],
            },
        ),
    ]
