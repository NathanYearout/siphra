from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from siphra.account import Account, AccountBalance
    from siphra.transaction import Transaction
    from siphra.types import AccountId, TransactionId


class StorageBackend(ABC):
    @abstractmethod
    async def save_account(self, account: Account) -> None: ...

    @abstractmethod
    async def get_account(self, account_id: AccountId) -> Account | None: ...

    @abstractmethod
    async def get_account_by_code(self, code: str) -> Account | None: ...

    @abstractmethod
    async def list_accounts(
        self, *, is_active: bool | None = None, currency_code: str | None = None
    ) -> list[Account]: ...

    @abstractmethod
    async def update_account(self, account: Account) -> None: ...

    @abstractmethod
    async def save_transaction(self, transaction: Transaction) -> None: ...

    @abstractmethod
    async def get_transaction(self, transaction_id: TransactionId) -> Transaction | None: ...

    @abstractmethod
    async def list_transactions(
        self,
        *,
        account_id: AccountId | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]: ...

    @abstractmethod
    async def get_account_balance(
        self, account_id: AccountId, as_of: datetime | None = None
    ) -> AccountBalance: ...

    async def begin_transaction(self) -> None:
        pass

    async def commit_transaction(self) -> None:
        pass

    async def rollback_transaction(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> StorageBackend:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        await self.close()
