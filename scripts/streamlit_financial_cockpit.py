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


if __name__ == "__main__":
    main()
