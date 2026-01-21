from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class Currency(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(min_length=3, max_length=4)
    name: str
    symbol: str = ""
    decimal_places: int = Field(ge=0, le=18)

    def round_amount(self, amount: Decimal) -> Decimal:
        quantize_str = "0." + "0" * self.decimal_places if self.decimal_places > 0 else "0"
        return amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

    def format_amount(self, amount: Decimal) -> str:
        rounded = self.round_amount(amount)
        formatted = f"{rounded:,.{self.decimal_places}f}"
        return f"{self.symbol}{formatted}" if self.symbol else formatted

    def smallest_unit(self) -> Decimal:
        if self.decimal_places == 0:
            return Decimal("1")
        return Decimal(f"0.{'0' * (self.decimal_places - 1)}1")


class CurrencyRegistry:
    _currencies: ClassVar[dict[str, Currency]] = {}

    @classmethod
    def get(cls, code: str) -> Currency | None:
        return cls._currencies.get(code.upper())

    @classmethod
    def register(cls, currency: Currency) -> None:
        cls._currencies[currency.code.upper()] = currency

    @classmethod
    def all_currencies(cls) -> list[Currency]:
        return list(cls._currencies.values())


# Common currencies
_COMMON_CURRENCIES = [
    Currency(code="USD", name="US Dollar", symbol="$", decimal_places=2),
    Currency(code="EUR", name="Euro", symbol="€", decimal_places=2),
    Currency(code="GBP", name="British Pound", symbol="£", decimal_places=2),
    Currency(code="JPY", name="Japanese Yen", symbol="¥", decimal_places=0),
    Currency(code="CHF", name="Swiss Franc", symbol="CHF ", decimal_places=2),
    Currency(code="CAD", name="Canadian Dollar", symbol="C$", decimal_places=2),
    Currency(code="AUD", name="Australian Dollar", symbol="A$", decimal_places=2),
    Currency(code="BTC", name="Bitcoin", symbol="₿", decimal_places=8),
    Currency(code="ETH", name="Ethereum", symbol="Ξ", decimal_places=18),
    Currency(code="USDC", name="USD Coin", symbol="USDC ", decimal_places=6),
    Currency(code="USDT", name="Tether", symbol="USDT ", decimal_places=6),
]

for _currency in _COMMON_CURRENCIES:
    CurrencyRegistry.register(_currency)
