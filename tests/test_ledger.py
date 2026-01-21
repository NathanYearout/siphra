"""Tests for the Ledger class."""

from decimal import Decimal

import pytest

from siphra import AccountType, BalanceError, Ledger


class TestLedgerAccounts:
    """Tests for account operations."""

    async def test_create_account(self, ledger: Ledger):
        """Test creating a basic account."""
        account = await ledger.create_account(
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET,
        )

        assert account.code == "1000"
        assert account.name == "Cash"
        assert account.account_type == AccountType.ASSET
        assert account.currency_code == "USD"
        assert account.is_active is True

    async def test_get_account_by_code(self, ledger: Ledger):
        """Test retrieving account by code."""
        created = await ledger.create_account(
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET,
        )

        retrieved = await ledger.get_account_by_code("1000")
        assert retrieved.id == created.id

    async def test_list_accounts(self, ledger: Ledger):
        """Test listing accounts with filters."""
        await ledger.create_account("1000", "Cash", AccountType.ASSET)
        await ledger.create_account("2000", "Payables", AccountType.LIABILITY)

        all_accounts = await ledger.list_accounts()
        assert len(all_accounts) == 2

        active_accounts = await ledger.list_accounts(is_active=True)
        assert len(active_accounts) == 2


class TestLedgerTransactions:
    """Tests for transaction operations."""

    async def test_record_balanced_transaction(self, ledger: Ledger):
        """Test recording a properly balanced transaction."""
        cash = await ledger.create_account("1000", "Cash", AccountType.ASSET)
        revenue = await ledger.create_account("4000", "Revenue", AccountType.REVENUE)

        tx = await ledger.record_transaction(
            description="Test sale",
            debits=[(cash.id, Decimal("100.00"))],
            credits=[(revenue.id, Decimal("100.00"))],
        )

        assert tx.is_posted
        assert tx.amount == Decimal("100.00")
        assert tx.description == "Test sale"

    async def test_unbalanced_transaction_fails(self, ledger: Ledger):
        """Test that unbalanced transactions are rejected."""
        cash = await ledger.create_account("1000", "Cash", AccountType.ASSET)
        revenue = await ledger.create_account("4000", "Revenue", AccountType.REVENUE)

        with pytest.raises(BalanceError):
            await ledger.record_transaction(
                description="Unbalanced",
                debits=[(cash.id, Decimal("100.00"))],
                credits=[(revenue.id, Decimal("50.00"))],
            )

    async def test_multi_entry_transaction(self, ledger: Ledger):
        """Test transaction with multiple debits and credits."""
        cash = await ledger.create_account("1000", "Cash", AccountType.ASSET)
        ar = await ledger.create_account("1100", "Receivables", AccountType.ASSET)
        revenue = await ledger.create_account("4000", "Revenue", AccountType.REVENUE)

        tx = await ledger.record_transaction(
            description="Mixed payment",
            debits=[
                (cash.id, Decimal("50.00")),
                (ar.id, Decimal("50.00")),
            ],
            credits=[
                (revenue.id, Decimal("100.00")),
            ],
        )

        assert tx.amount == Decimal("100.00")
        assert len(tx.entries) == 3


class TestLedgerBalances:
    """Tests for balance calculations."""

    async def test_asset_balance(self, ledger: Ledger):
        """Test balance calculation for asset account."""
        cash = await ledger.create_account("1000", "Cash", AccountType.ASSET)
        revenue = await ledger.create_account("4000", "Revenue", AccountType.REVENUE)

        await ledger.record_transaction(
            description="Sale",
            debits=[(cash.id, Decimal("100.00"))],
            credits=[(revenue.id, Decimal("100.00"))],
        )

        balance = await ledger.get_balance(cash.id)
        assert balance == Decimal("100.00")

    async def test_revenue_balance(self, ledger: Ledger):
        """Test balance calculation for revenue account."""
        cash = await ledger.create_account("1000", "Cash", AccountType.ASSET)
        revenue = await ledger.create_account("4000", "Revenue", AccountType.REVENUE)

        await ledger.record_transaction(
            description="Sale",
            debits=[(cash.id, Decimal("100.00"))],
            credits=[(revenue.id, Decimal("100.00"))],
        )

        balance = await ledger.get_balance(revenue.id)
        assert balance == Decimal("100.00")

    async def test_void_transaction(self, ledger: Ledger):
        """Test voiding a transaction creates proper reversal."""
        cash = await ledger.create_account("1000", "Cash", AccountType.ASSET)
        revenue = await ledger.create_account("4000", "Revenue", AccountType.REVENUE)

        tx = await ledger.record_transaction(
            description="Sale",
            debits=[(cash.id, Decimal("100.00"))],
            credits=[(revenue.id, Decimal("100.00"))],
        )

        reversal = await ledger.void_transaction(tx.id, reason="Customer refund")

        # Balances should be zero after voiding
        cash_balance = await ledger.get_balance(cash.id)
        revenue_balance = await ledger.get_balance(revenue.id)

        assert cash_balance == Decimal("0")
        assert revenue_balance == Decimal("0")
        assert reversal.description.startswith("Void:")
