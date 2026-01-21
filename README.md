# Siphra

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for double-entry bookkeeping.

I built this because the existing ledger libraries were either abandoned or too rigid to customize. Siphra gives you type-safe, async accounting primitives that you can plug into your own projects.

## What it does

- Enforces double-entry rules (debits must equal credits)
- Handles multiple currencies including crypto
- Keeps an immutable audit trail-posted transactions can only be voided, never edited
- Works with in-memory, SQLite, or PostgreSQL storage
- Requires Python 3.12+

## Install

```bash
pip install siphra

# or with a storage backend
pip install siphra[sqlite]
pip install siphra[postgres]
pip install siphra[all]
```

Or with uv:

```bash
uv add siphra
```

## Usage

```python
import asyncio
from decimal import Decimal

from siphra import Ledger, AccountType
from siphra.storage import MemoryStorage


async def main():
    storage = MemoryStorage()
    ledger = Ledger(storage, default_currency="USD")

    # Create accounts
    cash = await ledger.create_account("1000", "Cash", AccountType.ASSET)
    revenue = await ledger.create_account("4000", "Sales Revenue", AccountType.REVENUE)

    # Record a sale
    tx = await ledger.record_transaction(
        description="Product sale",
        debits=[(cash.id, Decimal("99.99"))],
        credits=[(revenue.id, Decimal("99.99"))],
    )

    balance = await ledger.get_balance(cash.id)
    print(f"Cash: ${balance}")  # Cash: $99.99


if __name__ == "__main__":
    asyncio.run(main())
```

## Docs

[nathanyearout.github.io/siphra](https://nathanyearout.github.io/siphra)

## Development

```bash
git clone https://github.com/nathanyearout/siphra.git
cd siphra

uv sync --all-extras --dev
uv run pytest
uv run ruff check src tests
uv run mypy src
```
