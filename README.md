# Siphra

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A modern Python SDK for double-entry ledgering.**

Siphra provides a type-safe, async-first API for implementing double-entry bookkeeping in Python applications. It enforces accounting principles at the type level and supports multiple storage backends. This project was started to power upcoming projects, as the current SDKs on the market were unmaintained and not easily modifyable.

## Features

- **Type-Safe**: Full type hints with Pydantic models ensure data integrity
- **Async-First**: Built for modern async Python applications
- **Double-Entry Enforcement**: Transactions automatically validate that debits equal credits
- **Multi-Currency**: Native support for fiat and cryptocurrency with configurable precision
- **Pluggable Storage**: Memory, SQLite, and PostgreSQL backends (extensible)
- **Immutable Audit Trail**: Posted transactions cannot be modified, only voided with reversals
- **Modern Python**: Requires Python 3.12+, uses latest language features

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

Or with uv (recommended):

```bash
uv add siphra
```

## Quick Start

```python
import asyncio
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

    # Record a sale - debits must equal credits (enforced!)
    tx = await ledger.record_transaction(
        description="Product sale",
        debits=[(cash.id, Decimal("99.99"))],
        credits=[(revenue.id, Decimal("99.99"))],
    )

    # Check balances
    cash_balance = await ledger.get_balance(cash.id)
    print(f"Cash: ${cash_balance}")  # Cash: $99.99


if __name__ == "__main__":
    asyncio.run(main())
```

## Documentation

Full documentation is available at [https://nathanyearout.github.io/siphra](https://nathanyearout.github.io/siphra)

## Development

```bash
# Clone the repository
git clone https://github.com/nathanyearout/siphra.git
cd siphra

# Install dependencies with uv
uv sync --all-extras --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check src tests

# Run type checking
uv run mypy src

# Build documentation locally
uv run mkdocs serve
```
