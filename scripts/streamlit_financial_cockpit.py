"""Minimal Streamlit cockpit prototype for reconciliation/compliance view.

Run:
    streamlit run scripts/streamlit_financial_cockpit.py
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from decimal import Decimal

from finance_app.gaap_router import AccountingStandard, AssetRevaluationRouter, LedgerContext

try:
    import streamlit as st
except Exception as exc:  # pragma: no cover - optional dependency in CI
    raise SystemExit(
        "Streamlit no está instalado en este entorno. Instala con: pip install streamlit"
    ) from exc


def main() -> None:
    st.set_page_config(page_title="Financial Cockpit", layout="wide")
    st.title("Financial Cockpit (MVP)")

    col1, col2, col3 = st.columns(3)
    col1.metric("Integridad pólizas", "98.4%")
    col2.metric("CFDI riesgo (LCO/EFOS)", "3")
    col3.metric("Ghost transactions", "5")

    st.subheader("Conciliación Contable-Fiscal")
    df = pd.DataFrame(
        [
            ["Utilidad contable", 1_250_000],
            ["Diferencias permanentes", 120_000],
            ["Diferencias temporales", 80_000],
            ["Utilidad fiscal", 1_450_000],
        ],
        columns=["Concepto", "Monto"],
    )
    st.dataframe(df, use_container_width=True)

    st.subheader("Alertas de Cierre")
    alerts = pd.DataFrame(
        [
            ["IFRS", "Revaluación FX pendiente", "Alta"],
            ["LOCAL", "CFDI cancelado sin ajuste", "Alta"],
            ["LOCAL", "Póliza sin UUID", "Media"],
        ],
        columns=["Ledger", "Alerta", "Severidad"],
    )
    st.dataframe(alerts, use_container_width=True)

    st.subheader("Matriz de Valuación (Semáforo Normativo)")
    router = AssetRevaluationRouter()
    ledgers = [
        LedgerContext("L01", "NIF MX", AccountingStandard.NIF_MX),
        LedgerContext("L02", "IFRS", AccountingStandard.IFRS),
        LedgerContext("L03", "US GAAP", AccountingStandard.US_GAAP),
    ]
    impacts = router.process_revaluation(
        ledgers=ledgers,
        current_book_values={"L01": Decimal("10000000"), "L02": Decimal("10000000"), "L03": Decimal("10000000")},
        new_fair_value=Decimal("12000000"),
        tax_basis_by_ledger={"L02": Decimal("10000000")},
    )
    valuation_df = pd.DataFrame([
        {
            "Ledger": i.ledger_name,
            "Norma": i.standard.value,
            "Acción": i.action,
            "Valor Libro Actual": float(i.book_value_before),
            "Ajuste": float(i.revaluation_adjustment),
            "Nuevo Valor Libro": float(i.book_value_after),
            "OCI": float(i.oci_surplus),
            "Impuesto Diferido": float(i.deferred_tax.deferred_tax_amount) if i.deferred_tax else 0.0,
        }
        for i in impacts
    ])
    st.dataframe(valuation_df, use_container_width=True)


if __name__ == "__main__":
    main()
