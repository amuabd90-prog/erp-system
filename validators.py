from datetime import datetime, date
from flask import flash
from models import (
    AfterSale, AuditLog, Expenses, Inventory, InventoryIn, 
    Sales, Stock, StockIn, StockOut, db
)
from sqlalchemy.exc import IntegrityError
import csv
import io
from flask import make_response


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class DuplicateError(Exception):
    """Custom exception for duplicate entry errors"""
    pass


class SyncError(Exception):
    """Custom exception for cross-module sync errors"""
    pass


def validate_positive_number(value, field_name):
    """Validate that a value is a positive number"""
    try:
        num = float(value)
        if num <= 0:
            raise ValidationError(f"{field_name} must be a positive number")
        return round(num, 2)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number")


def validate_positive_integer(value, field_name):
    """Validate that a value is a positive integer"""
    try:
        num = int(value)
        if num <= 0:
            raise ValidationError(f"{field_name} must be a positive integer")
        return num
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer")


def check_duplicate_stock_in(inventory_no):
    """Check for duplicate inventory_no in StockIn"""
    if StockIn.query.get(inventory_no):
        raise DuplicateError(f"Inventory No '{inventory_no}' already exists in Stock In")
    if Stock.query.get(inventory_no):
        raise DuplicateError(f"Inventory No '{inventory_no}' already exists in Stock")


def check_duplicate_stock_out(inventory_no):
    """Check for duplicate inventory_no in StockOut"""
    if StockOut.query.filter_by(inventory_no=inventory_no).first():
        raise DuplicateError(f"Inventory No '{inventory_no}' has already been stocked out")


def check_duplicate_sales(product_id):
    """Check for duplicate Product ID in Sales"""
    if Sales.query.get(product_id):
        raise DuplicateError(f"Product ID '{product_id}' already exists in Sales")


def check_duplicate_expenses(exp_date, amount, reference_no):
    """Check for duplicate expense entries"""
    existing = Expenses.query.filter_by(
        date=exp_date, 
        amount=amount, 
        reference_no=reference_no
    ).first()
    if existing:
        raise DuplicateError(f"Duplicate expense entry found for {exp_date} - {amount} - {reference_no}")


def check_inventory_availability(inventory_no):
    """Check if item exists in Stock with status 'No'"""
    stock = Stock.query.get(inventory_no)
    if not stock:
        raise ValidationError(f"Inventory No '{inventory_no}' not found in Stock")
    if stock.status == "Yes":
        raise ValidationError(f"Inventory No '{inventory_no}' has already been stocked out")
    return stock


def check_after_sale_availability(product_id):
    """Check if item was already sold"""
    after_sale = AfterSale.query.filter_by(inv_no=product_id).first()
    if after_sale:
        raise ValidationError(f"This item was already sold on {after_sale.date}. Cannot sell again.")


def validate_bank_account_match(account_number):
    """Validate bank account against non-receipt accounts"""
    NON_RECEIPT_ACCOUNTS = {
        "1000084206087", "57861258", "1014657935101", "08804884936001",
        "0001883620101", "1000564090001", "5038523396011", "01320927866200",
        "01320927862269", "0911190064"
    }
    
    if account_number and account_number in NON_RECEIPT_ACCOUNTS:
        flash(f"Warning: Account {account_number} is marked as non-receipt account", "warning")


def log_audit_action(user_id, username, action, module, target_id, details=None):
    """Log audit trail entry"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            module=module,
            target_id=str(target_id),
            details=details,
            timestamp=datetime.utcnow()
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to log audit action: {str(e)}", "error")


def safe_transaction(operations, error_message="Transaction failed"):
    """Execute multiple operations with rollback on failure"""
    try:
        results = []
        for op in operations:
            if callable(op):
                results.append(op())
            else:
                db.session.add(op)
                results.append(op)
        
        db.session.commit()
        return results
    except Exception as e:
        db.session.rollback()
        raise SyncError(f"{error_message}: {str(e)}")


def validate_required_fields(data, required_fields):
    """Validate that all required fields are present and not empty"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == "":
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")


def export_to_csv(data, headers, filename_prefix):
    """Export data to CSV with headers"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(headers)
    
    # Write data
    for row in data:
        writer.writerow(row)
    
    output.seek(0)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={filename_prefix}_{date.today().strftime('%Y-%m-%d')}.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response


def check_delete_dependencies(model_class, record_id, related_models):
    """Check if record has dependencies before deletion"""
    for related_model, foreign_key in related_models:
        if hasattr(related_model, 'query'):
            dependencies = related_model.query.filter_by(**{foreign_key: record_id}).count()
            if dependencies > 0:
                raise ValidationError(f"Cannot delete: {dependencies} dependent records found in {related_model.__name__}")


def format_currency(value):
    """Format currency to 2 decimal places"""
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00


def validate_date_range(start_date, end_date):
    """Validate date range"""
    if start_date and end_date and start_date > end_date:
        raise ValidationError("Start date cannot be after end date")


def flash_validation_errors(form):
    """Flash form validation errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", "error")
