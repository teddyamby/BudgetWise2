from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Transaction
from app import db
from datetime import datetime
from sqlalchemy import extract

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    transactions = Transaction.query.order_by(Transaction.date.desc()).limit(5).all()
    balance = calculate_balance()
    return render_template('index.html', transactions=transactions, balance=balance)

@main_bp.route('/transactions', methods=['GET', 'POST'])
def transactions():
    if request.method == 'POST':
        # Gestion de l'ajout de transaction
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

    # GET request - affichage des transactions avec filtres
    transaction_type = request.args.get('type', 'all')
    category = request.args.get('category', 'all')
    year = request.args.get('year', 'all')
    month = request.args.get('month', 'all')
    sort = request.args.get('sort', 'desc')

    query = Transaction.query

    if transaction_type != 'all':
        query = query.filter(Transaction.type == transaction_type)
    if category != 'all':
        query = query.filter(Transaction.category == category)
    if year != 'all':
        query = query.filter(extract('year', Transaction.date) == year)
    if month != 'all':
        query = query.filter(extract('month', Transaction.date) == month)

    if sort == 'asc':
        query = query.order_by(Transaction.date.asc())
    else:
        query = query.order_by(Transaction.date.desc())

    transactions = query.all()
    categories = get_unique_categories()
    years = get_unique_years()

    return render_template('transactions.html', 
                         transactions=transactions,
                         categories=categories,
                         years=years,
                         current_type=transaction_type,
                         current_category=category,
                         current_year=year,
                         current_month=month,
                         current_sort=sort)

@main_bp.route('/delete_transaction/<int:id>')
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('main.transactions'))

@main_bp.route('/analytics')
def analytics():
    year = request.args.get('year', 'all')
    month = request.args.get('month', 'all')

    expense_query = Transaction.query.filter_by(type='expense')
    income_query = Transaction.query.filter_by(type='income')

    if year != 'all':
        expense_query = expense_query.filter(extract('year', Transaction.date) == year)
        income_query = income_query.filter(extract('year', Transaction.date) == year)
    if month != 'all':
        expense_query = expense_query.filter(extract('month', Transaction.date) == month)
        income_query = income_query.filter(extract('month', Transaction.date) == month)

    expenses = expense_query.all()
    incomes = income_query.all()

    expense_categories = {}
    income_categories = {}
    
    for expense in expenses:
        if expense.category in expense_categories:
            expense_categories[expense.category] += expense.amount
        else:
            expense_categories[expense.category] = expense.amount
    
    for income in incomes:
        if income.category in income_categories:
            income_categories[income.category] += income.amount
        else:
            income_categories[income.category] = income.amount

    years = get_unique_years()

    return render_template('analytics.html', 
                         expense_categories=expense_categories,
                         income_categories=income_categories,
                         total_expenses=sum([e.amount for e in expenses]),
                         total_incomes=sum([i.amount for i in incomes]),
                         years=years,
                         current_year=year,
                         current_month=month)

def calculate_balance():
    incomes = Transaction.query.filter_by(type='income').all()
    expenses = Transaction.query.filter_by(type='expense').all()
    return sum([i.amount for i in incomes]) - sum([e.amount for e in expenses])

def get_unique_categories():
    income_categories = [t[0] for t in db.session.query(Transaction.category).filter_by(type='income').distinct().all()]
    expense_categories = [t[0] for t in db.session.query(Transaction.category).filter_by(type='expense').distinct().all()]
    return sorted(list(set(income_categories + expense_categories)))

def get_unique_years():
    years = [t[0] for t in db.session.query(extract('year', Transaction.date)).distinct().all()]
    return sorted([int(y) for y in years if y is not None], reverse=True)