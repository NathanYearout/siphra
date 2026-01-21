"""Pytest configuration and fixtures for Siphra tests."""

import pytest

from siphra import Ledger
from siphra.storage import MemoryStorage


@pytest.fixture
def memory_storage() -> MemoryStorage:
    """Create a fresh in-memory storage for each test."""
    return MemoryStorage()


@pytest.fixture
def ledger(memory_storage: MemoryStorage) -> Ledger:
    """Create a ledger with in-memory storage."""
    return Ledger(memory_storage, default_currency="USD")
