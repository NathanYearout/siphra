# Quickstart Guide

This guide will help you get started with Siphra in just a few minutes.

## Installation

```bash
pip install siphra
```

Or with uv (recommended):

```bash
uv add siphra
```

## Basic Setup

### 1. Create a Ledger

The `Ledger` is your main interface to the accounting system. It requires a storage backend:

```python
from siphra import Ledger
from siphra.storage import MemoryStorage

# Create storage (use MemoryStorage for development)
storage = MemoryStorage()

# Create ledger with default currency
ledger = Ledger(storage, default_currency="USD")
```

### 2. Create Accounts

Accounts are organized by type following standard accounting principles:

```python
from siphra import AccountType

async def setup_accounts(ledger: Ledger):
    # Asset accounts (what you own)
    cash = await ledger.create_account(
        code="1000",
        name="Cash",
        account_type=AccountType.ASSET,
    )

    receivables = await ledger.create_account(
        code="1100",
        name="Accounts Receivable",
        account_type=AccountType.ASSET,
    )

    # Liability accounts (what you owe)
    payables = await ledger.create_account(
        code="2000",
        name="Accounts Payable",
        account_type=AccountType.LIABILITY,
    )

    # Revenue accounts (income)
    revenue = await ledger.create_account(
        code="4000",
        name="Sales Revenue",
        account_type=AccountType.REVENUE,
    )

    # Expense accounts (costs)
    expenses = await ledger.create_account(
        code="5000",
        name="Operating Expenses",
        account_type=AccountType.EXPENSE,
    )

    return cash, receivables, payables, revenue, expenses
```

### 3. Record Transactions

Every transaction must have balanced debits and credits:

```python
from decimal import Decimal

async def record_sale(ledger: Ledger, cash_id, revenue_id):
    # Cash sale: debit cash (increase asset), credit revenue (increase income)
    tx = await ledger.record_transaction(
        description="Product sale - Invoice #001",
        debits=[(cash_id, Decimal("150.00"))],
        credits=[(revenue_id, Decimal("150.00"))],
        reference="INV-001",
    )
    return tx
```

### 4. Check Balances

```python
async def check_balances(ledger: Ledger, cash_id, revenue_id):
    cash_balance = await ledger.get_balance(cash_id)
    revenue_balance = await ledger.get_balance(revenue_id)

    print(f"Cash: ${cash_balance}")
    print(f"Revenue: ${revenue_balance}")
```

## Complete Example

Here's a complete working example:

```python
import asyncio
from decimal import Decimal

from siphra import Ledger, AccountType
from siphra.storage import MemoryStorage


async def main():
    # Setup
    storage = MemoryStorage()
    ledger = Ledger(storage, default_currency="USD")

    # Create chart of accounts
    cash = await ledger.create_account("1000", "Cash", AccountType.ASSET)
    ar = await ledger.create_account("1100", "Accounts Receivable", AccountType.ASSET)
    revenue = await ledger.create_account("4000", "Sales Revenue", AccountType.REVENUE)
    expenses = await ledger.create_account("5000", "Expenses", AccountType.EXPENSE)

    # Record transactions
    # 1. Cash sale
    await ledger.record_transaction(
        description="Cash sale",
        debits=[(cash.id, Decimal("100.00"))],
        credits=[(revenue.id, Decimal("100.00"))],
    )

    # 2. Credit sale (customer will pay later)
    await ledger.record_transaction(
        description="Credit sale to Customer A",
        debits=[(ar.id, Decimal("250.00"))],
        credits=[(revenue.id, Decimal("250.00"))],
    )

    # 3. Customer payment
    await ledger.record_transaction(
        description="Payment from Customer A",
        debits=[(cash.id, Decimal("250.00"))],
        credits=[(ar.id, Decimal("250.00"))],
    )

    # 4. Pay an expense
    await ledger.record_transaction(
        description="Office supplies",
        debits=[(expenses.id, Decimal("50.00"))],
        credits=[(cash.id, Decimal("50.00"))],
    )

    # Check final balances
    print("Final Balances:")
    print(f"  Cash: ${await ledger.get_balance(cash.id)}")
    print(f"  Accounts Receivable: ${await ledger.get_balance(ar.id)}")
    print(f"  Revenue: ${await ledger.get_balance(revenue.id)}")
    print(f"  Expenses: ${await ledger.get_balance(expenses.id)}")


if __name__ == "__main__":
    asyncio.run(main())
```

Expected output:

```
Final Balances:
  Cash: $300.00
  Accounts Receivable: $0.00
  Revenue: $350.00
  Expenses: $50.00
```

## Multi-Entry Transactions

Transactions can have multiple debits and credits:

```python
# Split payment between two accounts
await ledger.record_transaction(
    description="Split expense payment",
    debits=[
        (marketing_expense_id, Decimal("300.00")),
        (office_expense_id, Decimal("200.00")),
    ],
    credits=[
        (cash_id, Decimal("500.00")),
    ],
)
```

## Using the Transaction Builder

For complex transactions, use the fluent builder API:

```python
from siphra import TransactionBuilder

tx = (
    TransactionBuilder("Complex transaction")
    .debit(cash_id, Decimal("1000.00"), "USD")
    .debit(inventory_id, Decimal("500.00"), "USD")
    .credit(revenue_id, Decimal("1200.00"), "USD")
    .credit(tax_payable_id, Decimal("300.00"), "USD")
    .with_metadata("invoice_id", "INV-123")
    .build()
)
```

## Voiding Transactions

To "undo" a transaction, void it (creates reversing entries):

```python
# Void a transaction (creates automatic reversal)
reversal = await ledger.void_transaction(
    transaction_id=original_tx.id,
    reason="Customer returned product",
)
```

## Next Steps

- Explore the [API Reference](reference/) for detailed documentation
- Check out the `examples/` directory for more use cases
- Learn about different storage backends for production use
