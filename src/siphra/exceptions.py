from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from siphra.types import AccountId, TransactionId


class SiphraError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ValidationError(SiphraError):
    pass


class BalanceError(SiphraError):
    def __init__(self, message: str, debit_total: Decimal, credit_total: Decimal) -> None:
        self.debit_total = debit_total
        self.credit_total = credit_total
        super().__init__(message)


class AccountNotFoundError(SiphraError):
    def __init__(self, account_id: AccountId) -> None:
        self.account_id = account_id
        super().__init__(f"Account not found: {account_id}")


class TransactionNotFoundError(SiphraError):
    def __init__(self, transaction_id: TransactionId) -> None:
        self.transaction_id = transaction_id
        super().__init__(f"Transaction not found: {transaction_id}")


class DuplicateAccountError(SiphraError):
    def __init__(self, account_id: AccountId) -> None:
        self.account_id = account_id
        super().__init__(f"Account already exists: {account_id}")


class InsufficientFundsError(SiphraError):
    def __init__(self, account_id: AccountId, available: Decimal, requested: Decimal) -> None:
        self.account_id = account_id
        self.available = available
        self.requested = requested
        super().__init__(f"Insufficient funds: {available} available, {requested} requested")


class CurrencyMismatchError(SiphraError):
    def __init__(self, expected: str, actual: str) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"Currency mismatch: expected {expected}, got {actual}")


class ImmutableTransactionError(SiphraError):
    def __init__(self, transaction_id: TransactionId) -> None:
        self.transaction_id = transaction_id
        super().__init__(f"Cannot modify posted transaction {transaction_id}")


class StorageError(SiphraError):
    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        self.original_error = original_error
        super().__init__(message)
