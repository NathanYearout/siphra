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


class Entry(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: EntryId = Field(default_factory=lambda: EntryId(uuid4()))
    account_id: AccountId
    entry_type: EntryType
    amount: Decimal = Field(gt=Decimal("0"))
    currency_code: str = Field(min_length=3, max_length=4)
    description: str = Field(default="", max_length=500)

    @property
    def is_debit(self) -> bool:
        return self.entry_type == EntryType.DEBIT

    @property
    def is_credit(self) -> bool:
        return self.entry_type == EntryType.CREDIT

    @property
    def signed_amount(self) -> Decimal:
        return self.amount if self.is_debit else -self.amount


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
    def validate_balanced(self) -> Self:
        if self.debit_total != self.credit_total:
            raise BalanceError(
                f"Unbalanced: debits={self.debit_total}, credits={self.credit_total}",
                debit_total=self.debit_total,
                credit_total=self.credit_total,
            )
        return self

    @model_validator(mode="after")
    def validate_currencies(self) -> Self:
        currencies = {entry.currency_code for entry in self.entries}
        if len(currencies) > 1:
            raise ValidationError(f"Mixed currencies not allowed: {currencies}")
        return self

    @property
    def debit_total(self) -> Decimal:
        return sum((e.amount for e in self.entries if e.is_debit), start=Decimal("0"))

    @property
    def credit_total(self) -> Decimal:
        return sum((e.amount for e in self.entries if e.is_credit), start=Decimal("0"))

    @property
    def amount(self) -> Decimal:
        return self.debit_total

    @property
    def currency_code(self) -> str:
        return self.entries[0].currency_code

    @property
    def is_posted(self) -> bool:
        return self.status == TransactionStatus.POSTED

    @property
    def is_voided(self) -> bool:
        return self.status == TransactionStatus.VOIDED

    def post(self) -> Self:
        if self.status != TransactionStatus.PENDING:
            raise ValidationError(f"Cannot post transaction with status {self.status}")
        return self.model_copy(
            update={"status": TransactionStatus.POSTED, "posted_at": datetime.now(UTC)}
        )

    def create_reversal(self, description: str | None = None) -> Transaction:
        if self.status != TransactionStatus.POSTED:
            raise ValidationError("Can only reverse posted transactions")

        reversed_entries = tuple(
            Entry(
                account_id=entry.account_id,
                entry_type=EntryType.CREDIT if entry.is_debit else EntryType.DEBIT,
                amount=entry.amount,
                currency_code=entry.currency_code,
            )
            for entry in self.entries
        )

        return Transaction(
            entries=reversed_entries,
            description=description or f"Reversal of: {self.description}",
            reference=f"REV-{self.reference}" if self.reference else "",
            metadata={"reversed_transaction_id": str(self.id)},
        )


class TransactionBuilder:
    def __init__(self, description: str = "", reference: str = "") -> None:
        self._description = description
        self._reference = reference
        self._entries: list[Entry] = []
        self._metadata: Metadata = {}
        self._effective_date: datetime | None = None

    def debit(
        self, account_id: AccountId, amount: Decimal, currency_code: str, description: str = ""
    ) -> Self:
        self._entries.append(
            Entry(
                account_id=account_id,
                entry_type=EntryType.DEBIT,
                amount=amount,
                currency_code=currency_code,
                description=description,
            )
        )
        return self

    def credit(
        self, account_id: AccountId, amount: Decimal, currency_code: str, description: str = ""
    ) -> Self:
        self._entries.append(
            Entry(
                account_id=account_id,
                entry_type=EntryType.CREDIT,
                amount=amount,
                currency_code=currency_code,
                description=description,
            )
        )
        return self

    def with_metadata(self, key: str, value: str | int | float | bool | None) -> Self:
        self._metadata[key] = value
        return self

    def with_effective_date(self, date: datetime) -> Self:
        self._effective_date = date
        return self

    def build(self) -> Transaction:
        if len(self._entries) < 2:
            raise ValidationError("Transaction must have at least 2 entries")

        kwargs: dict = {
            "entries": tuple(self._entries),
            "description": self._description,
            "reference": self._reference,
            "metadata": self._metadata,
        }
        if self._effective_date:
            kwargs["effective_date"] = self._effective_date

        return Transaction(**kwargs)
