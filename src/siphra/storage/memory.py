from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from siphra.account import Account, AccountBalance
from siphra.exceptions import AccountNotFoundError, DuplicateAccountError
from siphra.storage.base import StorageBackend
from siphra.transaction import Transaction
from siphra.types import AccountId, TransactionId, TransactionStatus


class MemoryStorage(StorageBackend):
    def __init__(self) -> None:
        self._accounts: dict[AccountId, Account] = {}
        self._accounts_by_code: dict[str, AccountId] = {}
        self._transactions: dict[TransactionId, Transaction] = {}

    async def save_account(self, account: Account) -> None:
        if account.id in self._accounts:
            raise DuplicateAccountError(account.id)
        if account.code in self._accounts_by_code:
            raise DuplicateAccountError(self._accounts_by_code[account.code])

        self._accounts[account.id] = account
        self._accounts_by_code[account.code] = account.id

    async def get_account(self, account_id: AccountId) -> Account | None:
        return self._accounts.get(account_id)

    async def get_account_by_code(self, code: str) -> Account | None:
        account_id = self._accounts_by_code.get(code)
        return self._accounts.get(account_id) if account_id else None

    async def list_accounts(
        self, *, is_active: bool | None = None, currency_code: str | None = None
    ) -> list[Account]:
        accounts = list(self._accounts.values())
        if is_active is not None:
            accounts = [a for a in accounts if a.is_active == is_active]
        if currency_code is not None:
            accounts = [a for a in accounts if a.currency_code == currency_code]
        return sorted(accounts, key=lambda a: a.code)

    async def update_account(self, account: Account) -> None:
        if account.id not in self._accounts:
            raise AccountNotFoundError(account.id)

        old_account = self._accounts[account.id]
        if old_account.code != account.code:
            del self._accounts_by_code[old_account.code]
            self._accounts_by_code[account.code] = account.id

        self._accounts[account.id] = account

    async def save_transaction(self, transaction: Transaction) -> None:
        self._transactions[transaction.id] = transaction

    async def get_transaction(self, transaction_id: TransactionId) -> Transaction | None:
        return self._transactions.get(transaction_id)

    async def list_transactions(
        self,
        *,
        account_id: AccountId | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        txs = list(self._transactions.values())

        if account_id is not None:
            txs = [t for t in txs if any(e.account_id == account_id for e in t.entries)]
        if start_date is not None:
            txs = [t for t in txs if t.effective_date >= start_date]
        if end_date is not None:
            txs = [t for t in txs if t.effective_date <= end_date]

        txs.sort(key=lambda t: t.effective_date, reverse=True)
        return txs[offset : offset + limit]

    async def get_account_balance(
        self, account_id: AccountId, as_of: datetime | None = None
    ) -> AccountBalance:
        account = self._accounts.get(account_id)
        if account is None:
            raise AccountNotFoundError(account_id)

        as_of = as_of or datetime.now(UTC)
        debit_total = Decimal("0")
        credit_total = Decimal("0")

        for tx in self._transactions.values():
            if tx.status != TransactionStatus.POSTED or tx.effective_date > as_of:
                continue
            for entry in tx.entries:
                if entry.account_id == account_id:
                    if entry.is_debit:
                        debit_total += entry.amount
                    else:
                        credit_total += entry.amount

        return AccountBalance(
            account_id=account_id,
            debit_total=debit_total,
            credit_total=credit_total,
            currency_code=account.currency_code,
            as_of=as_of,
        )

    async def close(self) -> None:
        pass

    def clear(self) -> None:
        self._accounts.clear()
        self._accounts_by_code.clear()
        self._transactions.clear()
