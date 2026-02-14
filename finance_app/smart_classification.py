from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClassificationSuggestion:
    account_code: str
    cost_center: str
    confidence: float
    rationale: str


_DEFAULT_RULES: list[tuple[list[str], str, str]] = [
    (["renta", "arrendamiento", "lease"], "6105", "CC-ADM"),
    (["luz", "electricidad", "cfe"], "6005", "CC-OPEX"),
    (["internet", "telefonia", "telmex"], "6010", "CC-IT"),
    (["nómina", "nomina", "sueldos"], "5001", "CC-HR"),
    (["gasolina", "combustible"], "6020", "CC-LOG"),
]


def suggest_account_and_cost_center(description: str) -> ClassificationSuggestion:
    text = description.lower().strip()
    if not text:
        return ClassificationSuggestion("6999", "CC-UNASSIGNED", 0.1, "Descripción vacía")

    for keywords, account, cc in _DEFAULT_RULES:
        for keyword in keywords:
            if keyword in text:
                return ClassificationSuggestion(
                    account_code=account,
                    cost_center=cc,
                    confidence=0.85,
                    rationale=f"Coincidencia por palabra clave: {keyword}",
                )

    return ClassificationSuggestion(
        account_code="6999",
        cost_center="CC-UNASSIGNED",
        confidence=0.4,
        rationale="Sin coincidencia exacta; requiere revisión humana",
    )
