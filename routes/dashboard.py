from datetime import date, timedelta
from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from models import Expenses, ProfitTaxReport, Sales, WeeklyCommission


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    # Check if setup is needed
    from models import Company, User
    import os
    db_path = os.path.join(os.getcwd(), "instance", "ha_business.db")
    
    # If database doesn't exist or has no companies, show welcome page
    if not os.path.exists(db_path) or Company.query.count() == 0:
        return render_template("welcome.html")
    
    # If user is not authenticated, redirect to login
    from flask_login import current_user
    if not current_user.is_authenticated:
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))
    today = date.today()
    user_role = current_user.role
    
    # Role-based data filtering
    if user_role == "Store Keeper":
        # Store Keeper sees warehouse data only
        todays_sales = []  # No direct sales access
        todays_expenses = []  # No direct expenses access
        sales_amount = 0.0
        expense_amount = 0.0
        quick_profit = 0.0
        tax_estimate = 0.0
        commission_amount = 0.0
        
    elif user_role == "Sales Person":
        # Sales Person sees sales and inventory data
        todays_sales = Sales.query.filter_by(date=today).all()
        todays_expenses = []  # No direct expenses access
        sales_amount = sum(s.total_amount for s in todays_sales)
        expense_amount = 0.0
        quick_profit = sales_amount - expense_amount
        
        # Calculate Ethiopian VAT (15%)
        vat_amount = sales_amount * 0.15
        # Ethiopian profit tax calculation (progressive)
        if sales_amount <= 16667:
            profit_tax = 0
        elif sales_amount <= 33333:
            profit_tax = (sales_amount - 16667) * 0.10
        elif sales_amount <= 66667:
            profit_tax = 1666.70 + (sales_amount - 33333) * 0.15
        elif sales_amount <= 100000:
            profit_tax = 5000.10 + (sales_amount - 66667) * 0.20
        else:
            profit_tax = 14200.30 + (sales_amount - 100000) * 0.30
        
        tax_estimate = vat_amount + profit_tax
        commission_amount = 0.0
        
    elif user_role == "Accountant":
        # Accountant sees expenses, commission, and reports
        todays_sales = Sales.query.filter_by(date=today).all()
        todays_expenses = Expenses.query.filter_by(date=today).all()
        sales_amount = sum(s.total_amount for s in todays_sales)
        expense_amount = sum(e.amount for e in todays_expenses)
        quick_profit = sales_amount - expense_amount
        
        # Calculate Ethiopian VAT (15%)
        vat_amount = sales_amount * 0.15
        # Ethiopian profit tax calculation (progressive)
        if sales_amount <= 16667:
            profit_tax = 0
        elif sales_amount <= 33333:
            profit_tax = (sales_amount - 16667) * 0.10
        elif sales_amount <= 66667:
            profit_tax = 1666.70 + (sales_amount - 33333) * 0.15
        elif sales_amount <= 100000:
            profit_tax = 5000.10 + (sales_amount - 66667) * 0.20
        else:
            profit_tax = 14200.30 + (sales_amount - 100000) * 0.30
        
        tax_estimate = vat_amount + profit_tax
        
        # Get this week's commission
        week_start, week_end = today - timedelta(days=today.weekday()), today - timedelta(days=(6-today.weekday()))
        commission_row = WeeklyCommission.query.filter(
            WeeklyCommission.week_start >= week_start,
            WeeklyCommission.week_end <= week_end
        ).first()
        commission_amount = commission_row.total_commission if commission_row else 0.0
        
    elif user_role == "Auditor":
        # Auditor sees reconciliation and reports (read-only)
        todays_sales = Sales.query.filter_by(date=today).all()
        todays_expenses = Expenses.query.filter_by(date=today).all()
        sales_amount = sum(s.total_amount for s in todays_sales)
        expense_amount = sum(e.amount for e in todays_expenses)
        quick_profit = sales_amount - expense_amount
        
        # Calculate Ethiopian VAT (15%)
        vat_amount = sales_amount * 0.15
        # Ethiopian profit tax calculation (progressive)
        if sales_amount <= 16667:
            profit_tax = 0
        elif sales_amount <= 33333:
            profit_tax = (sales_amount - 16667) * 0.10
        elif sales_amount <= 66667:
            profit_tax = 1666.70 + (sales_amount - 33333) * 0.15
        elif sales_amount <= 100000:
            profit_tax = 5000.10 + (sales_amount - 66667) * 0.20
        else:
            profit_tax = 14200.30 + (sales_amount - 100000) * 0.30
        
        tax_estimate = vat_amount + profit_tax
        commission_amount = 0.0
        
    elif user_role == "Viewer":
        # Viewer sees dashboard only (read-only)
        todays_sales = []
        todays_expenses = []
        sales_amount = 0.0
        expense_amount = 0.0
        quick_profit = 0.0
        tax_estimate = 0.0
        commission_amount = 0.0
        
    else:  # Admin
        # Admin sees everything
        todays_sales = Sales.query.filter_by(date=today).all()
        todays_expenses = Expenses.query.filter_by(date=today).all()
        sales_amount = sum(s.total_amount for s in todays_sales)
        expense_amount = sum(e.amount for e in todays_expenses)
        quick_profit = sales_amount - expense_amount
        
        # Calculate Ethiopian VAT (15%)
        vat_amount = sales_amount * 0.15
        # Ethiopian profit tax calculation (progressive)
        if sales_amount <= 16667:
            profit_tax = 0
        elif sales_amount <= 33333:
            profit_tax = (sales_amount - 16667) * 0.10
        elif sales_amount <= 66667:
            profit_tax = 1666.70 + (sales_amount - 33333) * 0.15
        elif sales_amount <= 100000:
            profit_tax = 5000.10 + (sales_amount - 66667) * 0.20
        else:
            profit_tax = 14200.30 + (sales_amount - 100000) * 0.30
        
        tax_estimate = vat_amount + profit_tax
        
        # Get this week's commission
        week_start, week_end = today - timedelta(days=today.weekday()), today - timedelta(days=(6-today.weekday()))
        commission_row = WeeklyCommission.query.filter(
            WeeklyCommission.week_start >= week_start,
            WeeklyCommission.week_end <= week_end
        ).first()
        commission_amount = commission_row.total_commission if commission_row else 0.0
    
    # Get chart data from API endpoint
    from flask import url_for
    
    # Default chart data structure
    chart_data = {
        'sales_trend': [],
        'monthly_sales': [],
        'monthly_expenses': [],
        'tax': {
            'vat': 0,
            'profit_tax': 0,
            'net_profit': 0
        }
    }
    
    return render_template(
        "dashboard.html",
        sales_count=len(todays_sales),
        sales_amount=sales_amount,
        expense_amount=expense_amount,
        quick_profit=quick_profit,
        tax_estimate=tax_estimate,
        commission_amount=commission_amount,
        user_role=user_role,
        todays_sales=todays_sales,
        todays_expenses=todays_expenses,
        chart_data=chart_data,
    )


@dashboard_bp.route("/api/charts")
@login_required
def get_chart_data():
    today = date.today()
    user_role = current_user.role
    
    # Role-based data filtering
    if user_role == "Store Keeper":
        # Store Keeper sees warehouse data only
        sales_trend = []
        rev_item = []
        monthly_sales = []
        monthly_expenses = []
        latest_tax = None
    elif user_role == "Sales Person":
        # Sales Person sees sales and inventory data
        last_7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
        sales_trend = []
        for d in last_7:
            total = sum(s.total_amount for s in Sales.query.filter_by(date=d).all())
            sales_trend.append({"date": d.strftime("%d/%m/%Y"), "amount": total})
        rev_item = (
            Sales.query.with_entities(Sales.item_type, func.sum(Sales.price * Sales.quantity - Sales.deduction))
            .group_by(Sales.item_type)
            .all()
        )
        month_floor = today.replace(day=1) - timedelta(days=180)
        monthly_sales = (
            Sales.query.with_entities(func.strftime("%Y-%m", Sales.date), func.sum(Sales.price * Sales.quantity - Sales.deduction))
            .filter(Sales.date >= month_floor)
            .group_by(func.strftime("%Y-%m", Sales.date))
            .all()
        )
        monthly_expenses = []
        latest_tax = None
    elif user_role == "Accountant":
        # Accountant sees expenses, commission, and reports
        last_7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
        sales_trend = []
        for d in last_7:
            total = sum(s.total_amount for s in Sales.query.filter_by(date=d).all())
            sales_trend.append({"date": d.strftime("%d/%m/%Y"), "amount": total})
        rev_item = []
        month_floor = today.replace(day=1) - timedelta(days=180)
        monthly_sales = (
            Sales.query.with_entities(func.strftime("%Y-%m", Sales.date), func.sum(Sales.price * Sales.quantity - Sales.deduction))
            .filter(Sales.date >= month_floor)
            .group_by(func.strftime("%Y-%m", Sales.date))
            .all()
        )
        monthly_expenses = (
            Expenses.query.with_entities(func.strftime("%Y-%m", Expenses.date), func.sum(Expenses.amount))
            .filter(Expenses.date >= month_floor)
            .group_by(func.strftime("%Y-%m", Expenses.date))
            .all()
        )
        latest_tax = ProfitTaxReport.query.order_by(ProfitTaxReport.date.desc()).first()
    elif user_role == "Auditor":
        # Auditor sees reconciliation and reports (read-only)
        sales_trend = []
        rev_item = []
        monthly_sales = []
        monthly_expenses = []
        latest_tax = None
    elif user_role == "Viewer":
        # Viewer sees dashboard only (read-only)
        sales_trend = []
        rev_item = []
        monthly_sales = []
        monthly_expenses = []
        latest_tax = None
    else:  # Admin sees everything
        last_7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
        sales_trend = []
        for d in last_7:
            total = sum(s.total_amount for s in Sales.query.filter_by(date=d).all())
            sales_trend.append({"date": d.strftime("%d/%m/%Y"), "amount": total})
        rev_item = (
            Sales.query.with_entities(Sales.item_type, func.sum(Sales.price * Sales.quantity - Sales.deduction))
            .group_by(Sales.item_type)
            .all()
        )
        month_floor = today.replace(day=1) - timedelta(days=180)
        monthly_sales = (
            Sales.query.with_entities(func.strftime("%Y-%m", Sales.date), func.sum(Sales.price * Sales.quantity - Sales.deduction))
            .filter(Sales.date >= month_floor)
            .group_by(func.strftime("%Y-%m", Sales.date))
            .all()
        )
        monthly_expenses = (
            Expenses.query.with_entities(func.strftime("%Y-%m", Expenses.date), func.sum(Expenses.amount))
            .filter(Expenses.date >= month_floor)
            .group_by(func.strftime("%Y-%m", Expenses.date))
            .all()
        )
        latest_tax = ProfitTaxReport.query.order_by(ProfitTaxReport.date.desc()).first()
    
    return jsonify(
        {
            "sales_trend": sales_trend,
            "revenue_by_item": [{"item": i, "amount": float(a or 0)} for i, a in rev_item],
            "monthly_sales": [{"month": m, "amount": float(a or 0)} for m, a in monthly_sales],
            "monthly_expenses": [{"month": m, "amount": float(a or 0)} for m, a in monthly_expenses],
            "tax": {
                "vat": latest_tax.vat_15 if latest_tax else 0,
                "profit_tax": latest_tax.profit_tax if latest_tax else 0,
                "net_profit": latest_tax.total_profit if latest_tax else 0,
            } if latest_tax else {},
        }
    )
