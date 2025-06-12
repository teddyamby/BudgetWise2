from app import create_app
from app.models import Transaction, db
import pytest

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        
        # Add test data
        transaction1 = Transaction(
            type='income',
            amount=1000.0,
            category='Salary',
            description='Monthly salary',
            tags='salary,recurring'
        )
        
        transaction2 = Transaction(
            type='expense',
            amount=50.0,
            category='Food',
            description='Groceries',
            tags='food,necessary'
        )
        
        db.session.add(transaction1)
        db.session.add(transaction2)
        db.session.commit()
        
    yield app
    
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'BudgetWise' in response.data
    assert b'Solde Actuel' in response.data

def test_transactions_route(client):
    response = client.get('/transactions')
    assert response.status_code == 200
    assert b'Toutes les Transactions' in response.data
    assert b'Salary' in response.data
    assert b'Groceries' in response.data

def test_analytics_route(client):
    response = client.get('/analytics')
    assert response.status_code == 200
    assert b'Analytics' in response.data
    assert b'Total Revenus' in response.data
    assert b'Total Dépenses' in response.data