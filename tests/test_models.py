from app.models import Transaction
from app import db
import pytest
from datetime import datetime

def test_new_transaction():
    """
    Test creating a new transaction
    """
    transaction = Transaction(
        type='expense',
        amount=50.0,
        category='Food',
        description='Dinner with friends',
        tags='social,dining',
        date=datetime.utcnow()
    )
    
    assert transaction.type == 'expense'
    assert transaction.amount == 50.0
    assert transaction.category == 'Food'
    assert transaction.description == 'Dinner with friends'
    assert 'social' in transaction.tags
    assert transaction.date is not None

def test_transaction_repr():
    """
    Test the __repr__ method of Transaction
    """
    transaction = Transaction(
        type='income',
        amount=100.0,
        date=datetime(2023, 1, 1)
    )
    
    assert repr(transaction) == "Transaction('income', '100.0', '2023-01-01 00:00:00')"