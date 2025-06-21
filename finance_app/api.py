"""Integration with external APIs (stub implementation)."""

import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

BANXICO_SERIES = "SF43718"  # USD to MXN exchange rate
BANXICO_INFLATION_SERIES = "SP1"  # fictional code for demonstration
BANXICO_URL = (
    "https://www.banxico.org.mx/SieAPIRest/service/v1/series/" +
    f"{BANXICO_SERIES}/datos/oportuno"
)
BANXICO_INFL_URL = (
    "https://www.banxico.org.mx/SieAPIRest/service/v1/series/" +
    f"{BANXICO_INFLATION_SERIES}/datos/oportuno"
)


def get_exchange_rate() -> float:
    """Fetch the latest USD to MXN exchange rate from Banxico."""
    try:
        with urlopen(BANXICO_URL, timeout=5) as resp:
            data = json.load(resp)
        serie = data.get("bmx", {}).get("series", [])[0].get("datos", [])[0]
        return float(serie.get("dato"))
    except (URLError, HTTPError, ValueError, IndexError, KeyError):
        # Return a default value if the API call fails
        return 0.0


def get_inflation_rate() -> float:
    """Fetch the latest inflation rate from Banxico (stub)."""
    try:
        with urlopen(BANXICO_INFL_URL, timeout=5) as resp:
            data = json.load(resp)
        serie = data.get("bmx", {}).get("series", [])[0].get("datos", [])[0]
        return float(serie.get("dato"))
    except (URLError, HTTPError, ValueError, IndexError, KeyError):
        return 0.0
