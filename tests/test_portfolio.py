"""Tests for resenha.portfolio.read_portfolio."""

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest


@dataclass
class FakeAsset:
    """Mirror of Asset for assertions before real module exists."""

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


FAKE_SHEET_DATA = [
    [
        "Ativo",
        "Setor / Classe",
        "Meta (%)",
        "Qtd Atual",
        "Preço Médio (R$)",
        "Preço Tela (R$)",
        "Total Investido (R$)",
        "Valor Total (R$)",
        "Lucro / Prejuízo (R$)",
        "Rentabilidade (%)",
        "Peso Atual (%)",
        "Distância da Meta",
        "Status de Aporte",
    ],
    [
        "ITUB4",
        "Bancos",
        "10%",
        "100",
        "R$ 25,00",
        "R$ 30,00",
        "R$ 2.500,00",
        "R$ 3.000,00",
        "R$ 500,00",
        "20%",
        "12%",
        "+2%",
        "OK",
    ],
    [
        "BBDC4",
        "Bancos",
        "10%",
        "200",
        "R$ 15,00",
        "R$ 18,00",
        "R$ 3.000,00",
        "R$ 3.600,00",
        "R$ 600,00",
        "20%",
        "14%",
        "+4%",
        "OK",
    ],
    [
        "EGIE3",
        "Energia",
        "8%",
        "50",
        "R$ 40,00",
        "R$ 45,00",
        "R$ 2.000,00",
        "R$ 2.250,00",
        "R$ 250,00",
        "12,5%",
        "9%",
        "+1%",
        "COMPRAR",
    ],
    [
        "CPFE3",
        "Energia",
        "8%",
        "80",
        "R$ 30,00",
        "R$ 33,00",
        "R$ 2.400,00",
        "R$ 2.640,00",
        "R$ 240,00",
        "10%",
        "10%",
        "+2%",
        "OK",
    ],
    [
        "TAEE11",
        "Energia",
        "8%",
        "40",
        "R$ 35,00",
        "R$ 38,00",
        "R$ 1.400,00",
        "R$ 1.520,00",
        "R$ 120,00",
        "8,6%",
        "6%",
        "-2%",
        "OK",
    ],
    [
        "SBSP3",
        "Saneamento",
        "6%",
        "60",
        "R$ 50,00",
        "R$ 55,00",
        "R$ 3.000,00",
        "R$ 3.300,00",
        "R$ 300,00",
        "10%",
        "13%",
        "+7%",
        "VENDER",
    ],
    [
        "VIVT3",
        "Telecom",
        "6%",
        "70",
        "R$ 45,00",
        "R$ 48,00",
        "R$ 3.150,00",
        "R$ 3.360,00",
        "R$ 210,00",
        "6,7%",
        "13%",
        "+7%",
        "VENDER",
    ],
    [
        "PSSA3",
        "Seguradoras",
        "5%",
        "30",
        "R$ 60,00",
        "R$ 65,00",
        "R$ 1.800,00",
        "R$ 1.950,00",
        "R$ 150,00",
        "8,3%",
        "8%",
        "+3%",
        "OK",
    ],
    [
        "RURA11",
        "FIIs / Agro",
        "5%",
        "100",
        "R$ 100,00",
        "R$ 105,00",
        "R$ 10.000,00",
        "R$ 10.500,00",
        "R$ 500,00",
        "5%",
        "42%",
        "+37%",
        "VENDER",
    ],
    [
        "BRCO11",
        "FIIs / Lajes",
        "5%",
        "80",
        "R$ 80,00",
        "R$ 82,00",
        "R$ 6.400,00",
        "R$ 6.560,00",
        "R$ 160,00",
        "2,5%",
        "26%",
        "+21%",
        "VENDER",
    ],
    [
        "KNCR11",
        "FIIs / CRI",
        "5%",
        "90",
        "R$ 90,00",
        "R$ 92,00",
        "R$ 8.100,00",
        "R$ 8.280,00",
        "R$ 180,00",
        "2,2%",
        "33%",
        "+28%",
        "VENDER",
    ],
    [
        "",
        "TOTAL",
        "",
        "",
        "",
        "",
        "R$ 44.750,00",
        "R$ 48.960,00",
        "R$ 4.210,00",
        "",
        "100%",
        "",
        "",
    ],
]


EXPECTED_TICKERS = [
    "ITUB4",
    "BBDC4",
    "EGIE3",
    "CPFE3",
    "TAEE11",
    "SBSP3",
    "VIVT3",
    "PSSA3",
    "RURA11",
    "BRCO11",
    "KNCR11",
]


def _build_mock_service():
    """Return a mock Google Sheets service that returns FAKE_SHEET_DATA."""
    mock_service = MagicMock()
    mock_spreadsheets = MagicMock()
    mock_values = MagicMock()
    mock_get = MagicMock()
    mock_execute = MagicMock(return_value={"values": FAKE_SHEET_DATA})

    mock_get.execute = mock_execute
    mock_values.get = MagicMock(return_value=mock_get)
    mock_spreadsheets.values.return_value = mock_values
    mock_service.spreadsheets.return_value = mock_spreadsheets
    return mock_service


@patch("resenha.portfolio.Credentials")
@patch("resenha.portfolio.build")
def test_read_portfolio_returns_eleven_assets(
    mock_build: MagicMock,
    mock_creds_cls: MagicMock,
) -> None:
    """read_portfolio parses 11 assets and skips empty/totals rows."""
    mock_build.return_value = _build_mock_service()

    from resenha.portfolio import read_portfolio

    assets = read_portfolio("fake-sheet-id", "Consolidado")

    assert len(assets) == 11
    assert all(isinstance(a, type(assets[0])) for a in assets)
    assert [a.ticker for a in assets] == EXPECTED_TICKERS

    # Sectors
    assert assets[0].sector == "Bancos"
    assert assets[2].sector == "Energia"
    assert assets[5].sector == "Saneamento"
    assert assets[6].sector == "Telecom"
    assert assets[7].sector == "Seguradoras"
    assert assets[8].sector == "FIIs / Agro"

    # Numeric fields — percentages converted to floats, R$ stripped
    assert assets[0].target_pct == 10.0
    assert assets[0].qty == 100
    assert assets[0].avg_price == 25.0
    assert assets[0].current_price == 30.0
    assert assets[0].invested == 2500.0
    assert assets[0].value == 3000.0
    assert assets[0].pnl == 500.0
    assert assets[0].return_pct == 20.0
    assert assets[0].weight_pct == 12.0

    # Distance and status are kept as strings
    assert assets[0].distance_meta == "+2%"
    assert assets[0].status == "OK"
