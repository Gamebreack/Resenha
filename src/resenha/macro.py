"""Macroeconomic data fetching from BCB SGS API."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime

import requests

from resenha.cache import Cache

logger = logging.getLogger(__name__)


@dataclass
class MacroData:
    selic: float
    ipca: float
    dolar: float
    fetched_at: datetime


Endpoints = {
    "selic": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json",
    "ipca": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/1?formato=json",
    "dolar": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json",
}


def _parse_valor(valor_str: str) -> float:
    return float(valor_str.replace(",", "."))


def _fetch_series(url: str) -> float:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return _parse_valor(data[0]["valor"])


def fetch_macro(cache: Cache | None = None) -> MacroData | None:
    """Fetch SELIC, IPCA and Dólar from BCB. Returns cached data if available."""
    cache_key = "macro"

    if cache is not None:
        cached = cache.get(cache_key, ttl_seconds=3600)
        if cached is not None:
            return MacroData(
                selic=cached["selic"],
                ipca=cached["ipca"],
                dolar=cached["dolar"],
                fetched_at=datetime.fromisoformat(cached["fetched_at"]),
            )

    try:
        selic = _fetch_series(Endpoints["selic"])
        ipca = _fetch_series(Endpoints["ipca"])
        dolar = _fetch_series(Endpoints["dolar"])
        fetched_at = datetime.now()
    except Exception:
        logger.warning("Failed to fetch macro data from BCB", exc_info=True)
        if cache is not None:
            stale = cache._conn.execute(
                "SELECT value FROM cache WHERE key = ?", (cache_key,)
            ).fetchone()
            if stale is not None:
                cached = json.loads(stale[0])
                return MacroData(
                    selic=cached["selic"],
                    ipca=cached["ipca"],
                    dolar=cached["dolar"],
                    fetched_at=datetime.fromisoformat(cached["fetched_at"]),
                )
        return None

    result = MacroData(selic=selic, ipca=ipca, dolar=dolar, fetched_at=fetched_at)

    if cache is not None:
        cache.set(
            cache_key,
            {
                "selic": result.selic,
                "ipca": result.ipca,
                "dolar": result.dolar,
                "fetched_at": result.fetched_at.isoformat(),
            },
        )

    return result
