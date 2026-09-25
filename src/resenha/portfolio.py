"""Portfolio reader from Google Sheets."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore[import-untyped]


@dataclass
class Asset:
    """A single portfolio position."""

    ticker: str
    sector: str
    target_pct: float
    qty: int
    avg_price: float
    current_price: float
    invested: float
    value: float
    pnl: float
    return_pct: float
    weight_pct: float
    distance_meta: str
    status: str


def _parse_number(val: str) -> float:
    """Parse Brazilian-formatted currency or percentage strings."""
    if not val or not isinstance(val, str):
        return 0.0
    cleaned = val.replace("R$ ", "").replace("%", "").strip()
    # Brazilian format: dots are thousands, commas are decimals
    cleaned = cleaned.replace(".", "").replace(",", ".")
    return float(cleaned)


def read_portfolio(
    sheet_id: str, tab_name: str, token_path: Path | None = None
) -> list[Asset]:
    """Fetch portfolio data from a Google Sheet tab."""
    resolved = token_path or (Path.home() / ".hermes" / "google_token.json")
    creds = Credentials.from_authorized_user_file(str(resolved))
    service = build("sheets", "v4", credentials=creds)

    range_name = f"{tab_name}!A1:M20"
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=range_name)
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return []

    headers = values[0]
    # Build a header -> index map for robust parsing
    header_map = {h.strip(): idx for idx, h in enumerate(headers)}

    assets: list[Asset] = []
    for row in values[1:]:
        # Skip empty or totals rows
        ticker = row[header_map["Ativo"]] if "Ativo" in header_map and len(row) > header_map["Ativo"] else ""
        if not ticker or ticker.strip() == "":
            continue

        def get(col: str) -> str:
            idx = header_map.get(col)
            if idx is None or idx >= len(row):
                return ""
            return cast(str, row[idx]).strip()

        assets.append(
            Asset(
                ticker=get("Ativo"),
                sector=get("Setor / Classe"),
                target_pct=_parse_number(get("Meta (%)")),
                qty=int(_parse_number(get("Qtd Atual"))) if get("Qtd Atual") else 0,
                avg_price=_parse_number(get("Preço Médio (R$)")),
                current_price=_parse_number(get("Preço Tela (R$)")),
                invested=_parse_number(get("Total Investido (R$)")),
                value=_parse_number(get("Valor Total (R$)")),
                pnl=_parse_number(get("Lucro / Prejuízo (R$)")),
                return_pct=_parse_number(get("Rentabilidade (%)")),
                weight_pct=_parse_number(get("Peso Atual (%)")),
                distance_meta=get("Distância da Meta"),
                status=get("Status de Aporte"),
            )
        )

    return assets
