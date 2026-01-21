# Siphra

**A modern Python SDK for double-entry ledgering.**
Note: Siphra is pronounced "SIF-rah" and is derived from the ancient Aramaic word "book".

Siphra provides a type-safe, async-first API for implementing double-entry bookkeeping in Python applications. It enforces accounting principles at the type level and supports multiple storage backends.

## Methodology

While some SDKs allow for unbalanced transactions or mutable transaction histories, Siphra is designed to uphold the integrity of financial data by enforcing double-entry principles and immutability. This makes it suitable for applications requiring reliable accounting records, such as financial software, ERP systems, and auditing tools, but less so for casual expense tracking or personal finance apps.

## Features

- **Type-Safe**: Full type hints with Pydantic models ensure data integrity
- **Async-First**: Built for modern async Python applications
- **Double-Entry Enforcement**: Transactions automatically validate that debits equal credits
- **Multi-Currency**: Native support for fiat and cryptocurrency with configurable precision
- **Pluggable Storage**: Memory, SQLite, and PostgreSQL backends (extensible)
- **Immutable Audit Trail**: Posted transactions cannot be modified, only voided with reversals
- **Modern Python**: Requires Python 3.12+, uses latest language features

## Quick Example

```python
from decimal import Decimal
from siphra import Ledger, AccountType
from siphra.storage import MemoryStorage

async def main():
    # Initialize ledger with in-memory storage
    storage = MemoryStorage()
    ledger = Ledger(storage, default_currency="USD")

    # Create accounts
    cash = await ledger.create_account("1000", "Cash", AccountType.ASSET)
    revenue = await ledger.create_account("4000", "Sales Revenue", AccountType.REVENUE)

    # Record a sale - debits must equal credits
    tx = await ledger.record_transaction(
        description="Product sale",
        debits=[(cash.id, Decimal("99.99"))],
        credits=[(revenue.id, Decimal("99.99"))],
    )

    # Check balances
    cash_balance = await ledger.get_balance(cash.id)
    print(f"Cash: ${cash_balance}")  # Cash: $99.99
```

## Installation

```bash
# Basic installation
pip install siphra

# With SQLite support
pip install siphra[sqlite]

# With PostgreSQL support
pip install siphra[postgres]

# All storage backends
pip install siphra[all]
```

## Why Siphra?

Traditional accounting software is complex and often overkill for applications that just need reliable transaction tracking. Siphra provides:

1. **Developer-Friendly API**: Designed by developers, for developers
2. **Financial Correctness**: Double-entry bookkeeping prevents common errors
3. **Audit Compliance**: Immutable transaction history for regulatory requirements
4. **Modern Stack**: Async support, type safety, and clean architecture

## Core Concepts

### Double-Entry Bookkeeping

Every transaction affects at least two accounts with equal debits and credits:

- **Debits** increase asset and expense accounts
- **Credits** increase liability, equity, and revenue accounts

This ensures the fundamental accounting equation always holds:

> **Assets = Liabilities + Equity**

### Account Types

| Type      | Normal Balance | Examples                             |
| --------- | -------------- | ------------------------------------ |
| Asset     | Debit          | Cash, Inventory, Receivables         |
| Liability | Credit         | Payables, Loans, Deferred Revenue    |
| Equity    | Credit         | Capital, Retained Earnings           |
| Revenue   | Credit         | Sales, Service Fees, Interest Income |
| Expense   | Debit          | Salaries, Rent, Utilities            |

## Next Steps

- [Quickstart Guide](quickstart.md) - Get up and running in 5 minutes
- [API Reference](reference/) - Detailed documentation of all classes and methods
