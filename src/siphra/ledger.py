from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from siphra.account import Account, AccountBalance
from siphra.exceptions import (
    AccountNotFoundError,
    ImmutableTransactionError,
    TransactionNotFoundError,
)
from siphra.transaction import Transaction, TransactionBuilder
from siphra.types import (
    AccountId,
    AccountType,
    BalanceType,
    Metadata,
    TransactionId,
    TransactionStatus,
)

if TYPE_CHECKING:
    from siphra.storage.base import StorageBackend


class Ledger:
    def __init__(self, storage: StorageBackend, *, default_currency: str = "USD") -> None:
        self._storage = storage
        self._default_currency = default_currency

    @property
    def storage(self) -> StorageBackend:
        return self._storage

    async def create_account(
        self,
        code: str,
        name: str,
        account_type: AccountType,
        *,
        currency_code: str | None = None,
        description: str = "",
        parent_id: AccountId | None = None,
        metadata: Metadata | None = None,
    ) -> Account:
        account = Account(
            id=AccountId(uuid4()),
            code=code,
            name=name,
            account_type=account_type,
            currency_code=currency_code or self._default_currency,
            description=description,
            parent_id=parent_id,
            metadata=metadata or {},
        )
        await self._storage.save_account(account)
        return account

    async def get_account(self, account_id: AccountId) -> Account:
        account = await self._storage.get_account(account_id)
        if account is None:
            raise AccountNotFoundError(account_id)
        return account

    async def get_account_by_code(self, code: str) -> Account:
        account = await self._storage.get_account_by_code(code)
        if account is None:
            raise AccountNotFoundError(AccountId(uuid4()))
        return account

    async def list_accounts(
        self, *, is_active: bool | None = None, currency_code: str | None = None
    ) -> list[Account]:
        return await self._storage.list_accounts(is_active=is_active, currency_code=currency_code)

    async def update_account(
        self,
        account_id: AccountId,
        *,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        metadata: Metadata | None = None,
    ) -> Account:
        account = await self.get_account(account_id)
        updated = account.with_updates(
            name=name, description=description, is_active=is_active, metadata=metadata
        )
        await self._storage.update_account(updated)
        return updated

    async def record_transaction(
        self,
        description: str,
        debits: list[tuple[AccountId, Decimal]],
        credits: list[tuple[AccountId, Decimal]],
        *,
        currency_code: str | None = None,
        reference: str = "",
        effective_date: datetime | None = None,
        metadata: Metadata | None = None,
        auto_post: bool = True,
    ) -> Transaction:
        currency = currency_code or self._default_currency

        for account_id, _ in debits + credits:
            await self.get_account(account_id)

        builder = TransactionBuilder(description, reference)
        for account_id, amount in debits:
            builder.debit(account_id, amount, currency)
        for account_id, amount in credits:
            builder.credit(account_id, amount, currency)

        if effective_date:
            builder.effective(effective_date)
        if metadata:
            for key, value in metadata.items():
                builder.meta(key, value)

        transaction = builder.build()
        if auto_post:
            transaction = transaction.post()

        await self._storage.save_transaction(transaction)
        return transaction

    async def get_transaction(self, transaction_id: TransactionId) -> Transaction:
        transaction = await self._storage.get_transaction(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError(transaction_id)
        return transaction

    async def list_transactions(
        self,
        *,
        account_id: AccountId | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        return await self._storage.list_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

    async def void_transaction(
        self, transaction_id: TransactionId, reason: str = ""
    ) -> Transaction:
        original = await self.get_transaction(transaction_id)

        if original.status != TransactionStatus.POSTED:
            raise ImmutableTransactionError(transaction_id)

        reversal = original.reverse(
            description=f"Void: {original.description}" + (f" - {reason}" if reason else "")
        )
        reversal = reversal.post()

        # Keep original POSTED so both count in balance (netting to zero)
        marked_original = original.model_copy(
            update={
                "metadata": {
                    **original.metadata,
                    "voided": True,
                    "voided_by": str(reversal.id),
                    "void_reason": reason,
                },
            }
        )

        await self._storage.save_transaction(marked_original)
        await self._storage.save_transaction(reversal)
        return reversal

    async def get_balance(self, account_id: AccountId, as_of: datetime | None = None) -> Decimal:
        account = await self.get_account(account_id)
        balance_info = await self._storage.get_account_balance(account_id, as_of)

        if account.normal_balance == BalanceType.DEBIT:
            return balance_info.debit_total - balance_info.credit_total
        return balance_info.credit_total - balance_info.debit_total

    async def get_balance_details(
        self, account_id: AccountId, as_of: datetime | None = None
    ) -> AccountBalance:
        return await self._storage.get_account_balance(account_id, as_of)

    async def __aenter__(self) -> Ledger:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._storage.close()
