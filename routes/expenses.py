from datetime import date
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from auth import has_role, log_action
from forms import ExpenseForm
from models import Expenses, Sales, WeeklyCommission, db
from utils import compute_week_range, recompute_reports, safe_commit
from validators import (
    ValidationError, DuplicateError, check_duplicate_expenses,
    validate_positive_number, log_audit_action, flash_validation_errors,
    validate_bank_account_match, check_delete_dependencies
)
from export_utils import export_expenses_csv, export_weekly_commission_csv


expenses_bp = Blueprint("expenses", __name__)


def upsert_weekly_commission(target_date: date) -> None:
    from flask_login import current_user
    
    # Skip commission creation if no company is set
    if not current_user.company_id:
        return
        
    week_start, week_end = compute_week_range(target_date)
    sales_rows = Sales.query.filter(Sales.date >= week_start, Sales.date <= week_end).all()
    total_sales = sum(s.total_amount for s in sales_rows)
    suits_sold = sum(s.quantity for s in sales_rows if "suit" in (s.item_type or "").lower())
    coats_sold = sum(s.quantity for s in sales_rows if "coat" in (s.item_type or "").lower())
    sale_bonus_1pct = total_sales * 0.01
    suit_bonus = suits_sold * 150
    coat_bonus = coats_sold * 100
    total_commission = sale_bonus_1pct + suit_bonus + coat_bonus
    row = WeeklyCommission.query.filter_by(week_start=week_start, week_end=week_end).first()
    if row is None:
        row = WeeklyCommission(week_start=week_start, week_end=week_end, company_id=current_user.company_id)
    row.total_sales = total_sales
    row.suits_sold = suits_sold
    row.coats_sold = coats_sold
    row.sale_bonus_1pct = sale_bonus_1pct
    row.suit_bonus = suit_bonus
    row.coat_bonus = coat_bonus
    row.total_commission = total_commission
    db.session.add(row)


@expenses_bp.route("/")
@login_required
@has_role("Accountant", "Admin")
def index():
    from flask_login import current_user
    
    # Only create commission if user has a company
    if current_user.company_id:
        upsert_weekly_commission(date.today())
    db.session.commit()
    return render_template(
        "expenses/index.html",
        expense_rows=Expenses.query.order_by(Expenses.date.desc()).all(),
        commission_rows=WeeklyCommission.query.order_by(WeeklyCommission.week_start.desc()).all(),
        form=ExpenseForm(date=date.today()),
        editing=None,
    )


@expenses_bp.route("/create", methods=["POST"])
@login_required
@has_role("Accountant", "Admin")
def create_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        try:
            # Validate inputs
            amount = validate_positive_number(form.amount.data, "Amount")
            
            # Check for duplicates
            check_duplicate_expenses(form.date.data, amount, form.reference_no.data or "")
            
            # Validate bank account
            validate_bank_account_match(form.account_number.data)
            
            expense = Expenses(
                date=form.date.data,
                amount=amount,
                reason=form.reason.data,
                reference_no=form.reference_no.data,
                payed_by=form.payed_by.data,
                account_number=form.account_number.data,
                status=form.status.data,
            )
            
            db.session.add(expense)
            # Only create commission if user has a company
            if current_user.company_id:
                upsert_weekly_commission(form.date.data)
            db.session.commit()
            
            flash("Expense saved successfully.", "success")
            recompute_reports()
            
            # Log audit trail
            log_audit_action(
                current_user.id, current_user.username,
                "CREATE", "EXPENSES", str(expense.id),
                f"Expense created: {form.reason.data} - {amount}"
            )
            
        except (ValidationError, DuplicateError) as e:
            flash(str(e), "error")
            if "reference_no" in str(e).lower() or "amount" in str(e).lower():
                flash("Please check the highlighted fields.", "warning")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to create expense: {str(e)}", "error")
    else:
        flash_validation_errors(form)
    
    return redirect(url_for("expenses.index"))


@expenses_bp.route("/<int:expense_id>/edit")
@login_required
@has_role("Accountant", "Admin")
def edit_expense(expense_id: int):
    row = Expenses.query.get_or_404(expense_id)
    return render_template(
        "expenses/index.html",
        expense_rows=Expenses.query.order_by(Expenses.date.desc()).all(),
        commission_rows=WeeklyCommission.query.order_by(WeeklyCommission.week_start.desc()).all(),
        form=ExpenseForm(obj=row),
        editing=row,
    )


@expenses_bp.route("/<int:expense_id>/update", methods=["POST"])
@login_required
@has_role("Accountant", "Admin")
def update_expense(expense_id: int):
    row = Expenses.query.get_or_404(expense_id)
    form = ExpenseForm()
    if form.validate_on_submit():
        try:
            # Validate inputs
            amount = validate_positive_number(form.amount.data, "Amount")
            
            # Check for duplicates (excluding current record)
            existing = Expenses.query.filter(
                Expenses.date == form.date.data,
                Expenses.amount == amount,
                Expenses.reference_no == (form.reference_no.data or ""),
                Expenses.id != expense_id
            ).first()
            
            if existing:
                raise DuplicateError(f"Duplicate expense entry found for {form.date.data} - {amount} - {form.reference_no.data or ''}")
            
            # Validate bank account
            validate_bank_account_match(form.account_number.data)
            
            row.date = form.date.data
            row.amount = amount
            row.reason = form.reason.data
            row.reference_no = form.reference_no.data
            row.payed_by = form.payed_by.data
            row.account_number = form.account_number.data
            row.status = form.status.data
            
            # Only create commission if user has a company
            if current_user.company_id:
                upsert_weekly_commission(form.date.data)
            db.session.commit()
            
            flash("Expense updated successfully.", "success")
            recompute_reports()
            
            # Log audit trail
            log_audit_action(
                current_user.id, current_user.username,
                "UPDATE", "EXPENSES", str(expense_id),
                f"Expense updated: {form.reason.data} - {amount}"
            )
            
        except (ValidationError, DuplicateError) as e:
            flash(str(e), "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update expense: {str(e)}", "error")
    else:
        flash_validation_errors(form)
    
    return redirect(url_for("expenses.index"))


@expenses_bp.route("/<int:expense_id>/delete", methods=["POST"])
@login_required
@has_role("Accountant", "Admin")
def delete_expense(expense_id: int):
    try:
        row = Expenses.query.get_or_404(expense_id)
        expense_date = row.date
        
        # Check dependencies before deletion
        check_delete_dependencies(
            Expenses, expense_id,
            [(BankReconExpenses, 'id')]
        )
        
        db.session.delete(row)
        # Only create commission if user has a company
        if current_user.company_id:
            upsert_weekly_commission(expense_date)
        db.session.commit()
        
        flash("Expense deleted successfully.", "success")
        recompute_reports()
        
        # Log audit trail
        log_audit_action(
            current_user.id, current_user.username,
            "DELETE", "EXPENSES", str(expense_id),
            f"Expense deleted: {row.reason} - {row.amount}"
        )
        
    except ValidationError as e:
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete expense: {str(e)}", "error")
    
    return redirect(url_for("expenses.index"))


@expenses_bp.route("/commission/recalculate", methods=["POST"])
@login_required
@has_role("Accountant", "Admin")
def recalculate_commission():
    # Only create commission if user has a company
    if current_user.company_id:
        upsert_weekly_commission(date.today())
        safe_commit("Weekly commission recalculated.")
        log_action("UPDATE", "EXPENSES", "", "Commission recalculated")
    return redirect(url_for("expenses.index"))


@expenses_bp.route("/export/expenses")
@login_required
@has_role("Accountant", "Admin")
def export_expenses():
    return export_expenses_csv()


@expenses_bp.route("/export/commission")
@login_required
@has_role("Accountant", "Admin")
def export_commission():
    return export_weekly_commission_csv()
