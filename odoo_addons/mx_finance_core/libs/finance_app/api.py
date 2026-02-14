"""Integration with external APIs (stub implementation)."""

import requests

BANXICO_SERIES = "SF43718"  # example: USD to MXN exchange rate
BANXICO_URL = (
    "https://www.banxico.org.mx/SieAPIRest/service/v1/series/" +
    f"{BANXICO_SERIES}/datos/oportuno"
)


def get_exchange_rate() -> float:
    """Fetch the latest USD to MXN exchange rate from Banxico."""
    try:
        resp = requests.get(BANXICO_URL, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        serie = data.get("bmx", {}).get("series", [])[0].get("datos", [])[0]
        return float(serie.get("dato"))
    except Exception:
        # Return a default value if the API call fails
        return 0.0
