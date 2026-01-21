from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from siphra.types import AccountId, AccountType, BalanceType, Metadata, Timestamp


class Account(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: AccountId = Field(default_factory=lambda: AccountId(uuid4()))
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    account_type: AccountType
    currency_code: str = Field(min_length=3, max_length=4)
    description: str = Field(default="", max_length=1000)
    parent_id: AccountId | None = None
    is_active: bool = True
    metadata: Metadata = Field(default_factory=dict)
    created_at: Timestamp = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Timestamp = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def normal_balance(self) -> BalanceType:
        if self.account_type in (AccountType.ASSET, AccountType.EXPENSE):
            return BalanceType.DEBIT
        return BalanceType.CREDIT

    def with_updates(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        metadata: Metadata | None = None,
    ) -> Self:
        return self.model_copy(
            update={
                k: v
                for k, v in {
                    "name": name,
                    "description": description,
                    "is_active": is_active,
                    "metadata": metadata,
                    "updated_at": datetime.now(UTC),
                }.items()
                if v is not None
            }
        )


class AccountBalance(BaseModel):
    model_config = ConfigDict(frozen=True)

    account_id: AccountId
    debit_total: Decimal = Decimal("0")
    credit_total: Decimal = Decimal("0")
    currency_code: str
    as_of: Timestamp = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def balance(self) -> Decimal:
        return self.debit_total - self.credit_total
