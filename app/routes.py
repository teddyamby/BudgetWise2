from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Transaction
from app import db
from datetime import datetime, timedelta
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    transactions = Transaction.query.order_by(Transaction.date.desc()).limit(5).all()
    balance = calculate_balance()
    return render_template('index.html', transactions=transactions, balance=balance)

@main_bp.route('/transactions', methods=['GET', 'POST'])
def transactions():
    # Filtres par défaut
    transaction_type = request.args.get('type', 'all')
    category = request.args.get('category', 'all')
    sort = request.args.get('sort', 'date_desc')
    date_range = request.args.get('date_range', 'all_time')
    
    # Construction de la requête de base
    query = Transaction.query
    
    # Filtrage par type
    if transaction_type != 'all':
        query = query.filter(Transaction.type == transaction_type)
    
    # Filtrage par catégorie
    if category != 'all':
        query = query.filter(Transaction.category == category)
    
    # Filtrage par date
    if date_range != 'all_time':
        today = datetime.utcnow()
        if date_range == 'today':
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Transaction.date >= start_date)
        elif date_range == 'this_week':
            start_date = today - timedelta(days=today.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Transaction.date >= start_date)
        elif date_range == 'this_month':
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Transaction.date >= start_date)
        elif date_range == 'last_month':
            first_day_current_month = today.replace(day=1)
            last_day_previous_month = first_day_current_month - timedelta(days=1)
            first_day_previous_month = last_day_previous_month.replace(day=1)
            query = query.filter(Transaction.date >= first_day_previous_month,
                                Transaction.date <= last_day_previous_month)
    
    # Tri des résultats
    if sort == 'date_asc':
        query = query.order_by(Transaction.date.asc())
    elif sort == 'date_desc':
        query = query.order_by(Transaction.date.desc())
    elif sort == 'amount_asc':
        query = query.order_by(Transaction.amount.asc())
    elif sort == 'amount_desc':
        query = query.order_by(Transaction.amount.desc())
    
    transactions = query.all()
    
    # Récupération des catégories uniques pour les filtres
    income_categories = db.session.query(Transaction.category)\
        .filter(Transaction.type == 'income')\
        .distinct().all()
    income_categories = [cat[0] for cat in income_categories]
    
    expense_categories = db.session.query(Transaction.category)\
        .filter(Transaction.type == 'expense')\
        .distinct().all()
    expense_categories = [cat[0] for cat in expense_categories]
    
    all_categories = list(set(income_categories + expense_categories))
    
    return render_template('transactions.html', 
                         transactions=transactions,
                         income_categories=income_categories,
                         expense_categories=expense_categories,
                         all_categories=all_categories,
                         current_filters={
                             'type': transaction_type,
                             'category': category,
                             'sort': sort,
                             'date_range': date_range
                         })

@main_bp.route('/analytics')
def analytics():
    # Simple analytics - in a real app you'd use more complex queries
    expenses = Transaction.query.filter_by(type='expense').all()
    incomes = Transaction.query.filter_by(type='income').all()
    
    # Group by category for expenses
    expense_categories = {}
    for expense in expenses:
        if expense.category in expense_categories:
            expense_categories[expense.category] += expense.amount
        else:
            expense_categories[expense.category] = expense.amount
    
    # Group by category for incomes
    income_categories = {}
    for income in incomes:
        if income.category in income_categories:
            income_categories[income.category] += income.amount
        else:
            income_categories[income.category] = income.amount
    
    return render_template('analytics.html', 
                         expense_categories=expense_categories,
                         income_categories=income_categories,
                         total_expenses=sum([e.amount for e in expenses]),
                         total_incomes=sum([i.amount for i in incomes]))

@main_bp.route('/add_transaction', methods=['POST'])
def add_transaction():
    type = request.form.get('type')
    amount = float(request.form.get('amount'))
    category = request.form.get('category')
    description = request.form.get('description')
    tags = request.form.get('tags')
    
    transaction = Transaction(
        type=type,
        amount=amount,
        category=category,
        description=description,
        tags=tags,
        date=datetime.utcnow()
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    flash('Transaction added successfully!', 'success')
    return redirect(url_for('main.transactions'))

@main_bp.route('/delete_transaction/<int:id>')
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('main.transactions'))

def calculate_balance():
    incomes = Transaction.query.filter_by(type='income').all()
    expenses = Transaction.query.filter_by(type='expense').all()
    
    total_income = sum([i.amount for i in incomes])
    total_expense = sum([e.amount for e in expenses])
    
    return total_income - total_expense