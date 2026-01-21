from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from siphra.exceptions import BalanceError, ValidationError
from siphra.types import (
    AccountId,
    EntryId,
    EntryType,
    Metadata,
    Timestamp,
    TransactionId,
    TransactionStatus,
)

ZERO = Decimal("0")


class Entry(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: EntryId = Field(default_factory=lambda: EntryId(uuid4()))
    account_id: AccountId
    entry_type: EntryType
    amount: Decimal = Field(gt=ZERO)
    currency_code: str = Field(min_length=3, max_length=4)
    description: str = Field(default="", max_length=500)

    @property
    def signed_amount(self) -> Decimal:
        return self.amount if self.entry_type == EntryType.DEBIT else -self.amount


class Transaction(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: TransactionId = Field(default_factory=lambda: TransactionId(uuid4()))
    entries: tuple[Entry, ...] = Field(min_length=2)
    description: str = Field(default="", max_length=1000)
    reference: str = Field(default="", max_length=100)
    effective_date: Timestamp = Field(default_factory=lambda: datetime.now(UTC))
    status: TransactionStatus = TransactionStatus.PENDING
    metadata: Metadata = Field(default_factory=dict)
    created_at: Timestamp = Field(default_factory=lambda: datetime.now(UTC))
    posted_at: Timestamp | None = None

    @model_validator(mode="after")
    def _check_balance(self) -> Self:
        debits = sum((e.amount for e in self.entries if e.entry_type == EntryType.DEBIT), ZERO)
        credits = sum((e.amount for e in self.entries if e.entry_type == EntryType.CREDIT), ZERO)
        if debits != credits:
            raise BalanceError(f"Unbalanced: debits={debits}, credits={credits}", debits, credits)
        return self

    @model_validator(mode="after")
    def _check_single_currency(self) -> Self:
        currencies = {e.currency_code for e in self.entries}
        if len(currencies) > 1:
            raise ValidationError(f"Mixed currencies not allowed: {currencies}")
        return self

    @property
    def amount(self) -> Decimal:
        return sum((e.amount for e in self.entries if e.entry_type == EntryType.DEBIT), ZERO)

    @property
    def currency_code(self) -> str:
        return self.entries[0].currency_code

    @property
    def is_posted(self) -> bool:
        return self.status == TransactionStatus.POSTED

    def post(self) -> Self:
        if self.status != TransactionStatus.PENDING:
            raise ValidationError(f"Cannot post transaction with status {self.status}")
        return self.model_copy(
            update={"status": TransactionStatus.POSTED, "posted_at": datetime.now(UTC)}
        )

    def reverse(self, description: str | None = None) -> Transaction:
        if self.status != TransactionStatus.POSTED:
            raise ValidationError("Can only reverse posted transactions")

        def flip(t: EntryType) -> EntryType:
            return EntryType.CREDIT if t == EntryType.DEBIT else EntryType.DEBIT

        return Transaction(
            entries=tuple(
                Entry(
                    account_id=e.account_id,
                    entry_type=flip(e.entry_type),
                    amount=e.amount,
                    currency_code=e.currency_code,
                )
                for e in self.entries
            ),
            description=description or f"Reversal of: {self.description}",
            reference=f"REV-{self.reference}" if self.reference else "",
            metadata={"reversed_transaction_id": str(self.id)},
        )


class TransactionBuilder:
    __slots__ = ("_desc", "_effective", "_entries", "_meta", "_ref")

    def __init__(self, description: str = "", reference: str = "") -> None:
        self._desc = description
        self._ref = reference
        self._entries: list[Entry] = []
        self._meta: Metadata = {}
        self._effective: datetime | None = None

    def _add(self, kind: EntryType, account: AccountId, amount: Decimal, currency: str) -> Self:
        entry = Entry(account_id=account, entry_type=kind, amount=amount, currency_code=currency)
        self._entries.append(entry)
        return self

    def debit(self, account: AccountId, amount: Decimal, currency: str) -> Self:
        return self._add(EntryType.DEBIT, account, amount, currency)

    def credit(self, account: AccountId, amount: Decimal, currency: str) -> Self:
        return self._add(EntryType.CREDIT, account, amount, currency)

    def meta(self, key: str, value: str | int | float | bool | None) -> Self:
        self._meta[key] = value
        return self

    def effective(self, date: datetime) -> Self:
        self._effective = date
        return self

    def build(self) -> Transaction:
        kwargs: dict = {
            "entries": tuple(self._entries),
            "description": self._desc,
            "reference": self._ref,
            "metadata": self._meta,
        }
        if self._effective:
            kwargs["effective_date"] = self._effective
        return Transaction(**kwargs)
