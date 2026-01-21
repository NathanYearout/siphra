from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, NewType
from uuid import UUID

from pydantic import Field

AccountId = NewType("AccountId", UUID)
TransactionId = NewType("TransactionId", UUID)
EntryId = NewType("EntryId", UUID)
LedgerId = NewType("LedgerId", UUID)

MoneyAmount = Annotated[Decimal, Field(decimal_places=8)]


class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class EntryType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    POSTED = "posted"
    VOIDED = "voided"


class BalanceType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


Timestamp = Annotated[datetime, Field()]
Metadata = dict[str, str | int | float | bool | None]
