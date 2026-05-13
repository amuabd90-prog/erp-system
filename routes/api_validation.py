from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import StockIn, Stock, Sales, Expenses, StockOut, AfterSale
from validators import check_delete_dependencies
import re

api_validation_bp = Blueprint("api_validation", __name__)


@api_validation_bp.route("/check-duplicate/stock-in/<inventory_no>")
@login_required
def check_duplicate_stock_in_api(inventory_no):
    """Check if inventory_no exists in StockIn or Stock"""
    exists = StockIn.query.get(inventory_no) is not None or Stock.query.get(inventory_no) is not None
    return jsonify(exists)


@api_validation_bp.route("/check-duplicate/stock-out/<inventory_no>")
@login_required
def check_duplicate_stock_out_api(inventory_no):
    """Check if inventory_no exists in StockOut"""
    exists = StockOut.query.filter_by(inventory_no=inventory_no).first() is not None
    return jsonify(exists)


@api_validation_bp.route("/check-duplicate/sales/<product_id>")
@login_required
def check_duplicate_sales_api(product_id):
    """Check if product_id exists in Sales"""
    exists = Sales.query.get(product_id) is not None
    return jsonify(exists)


@api_validation_bp.route("/check-duplicate/expenses")
@login_required
def check_duplicate_expenses_api():
    """Check for duplicate expense entries"""
    exp_date = request.args.get('date')
    amount = request.args.get('amount')
    reference_no = request.args.get('reference_no', '')
    
    if not all([exp_date, amount]):
        return jsonify(False)
    
    try:
        from datetime import datetime
        exp_dt = datetime.strptime(exp_date, "%Y-%m-%d").date()
        amount_float = float(amount)
        
        existing = Expenses.query.filter_by(
            date=exp_dt, 
            amount=amount_float, 
            reference_no=reference_no
        ).first()
        
        return jsonify(existing is not None)
    except (ValueError, TypeError):
        return jsonify(False)


@api_validation_bp.route("/check-inventory/<inventory_no>")
@login_required
def check_inventory_availability_api(inventory_no):
    """Check if inventory_no exists and is available for stock out"""
    stock = Stock.query.get(inventory_no)
    if not stock:
        return jsonify({"available": False, "reason": "Inventory not found"})
    
    if stock.status == "Yes":
        return jsonify({"available": False, "reason": "Already stocked out"})
    
    return jsonify({"available": True, "item": stock.item, "brand": stock.brand})


@api_validation_bp.route("/check-after-sale/<product_id>")
@login_required
def check_after_sale_availability_api(product_id):
    """Check if product_id exists in AfterSale (already sold)"""
    after_sale = AfterSale.query.filter_by(inv_no=product_id).first()
    if after_sale:
        return jsonify({
            "sold": True, 
            "date": after_sale.date.strftime("%Y-%m-%d") if after_sale.date else None
        })
    
    return jsonify({"sold": False})


@api_validation_bp.route("/check-dependencies")
@login_required
def check_dependencies_api():
    """Check for dependencies before deletion"""
    delete_url = request.args.get('url')
    
    # Extract model and ID from URL
    # This is a simplified version - you may need to adjust based on your URL patterns
    try:
        if '/stockout/' in delete_url:
            stockout_id = int(delete_url.split('/stockout/')[1].split('/delete')[0])
            # Check if this stockout has dependencies in Sales or AfterSale
            stockout = StockOut.query.get(stockout_id)
            if stockout:
                sales_dep = Sales.query.filter_by(product_id=stockout.inventory_no).first()
                after_sale_dep = AfterSale.query.filter_by(inv_no=stockout.inventory_no).first()
                return jsonify(sales_dep is not None or after_sale_dep is not None)
        
        elif '/stockin/' in delete_url:
            inventory_no = delete_url.split('/stockin/')[1].split('/delete')[0]
            # Check if this stock in has dependencies
            stockout_dep = StockOut.query.filter_by(inventory_no=inventory_no).first()
            sales_dep = Sales.query.filter_by(product_id=inventory_no).first()
            return jsonify(stockout_dep is not None or sales_dep is not None)
        
        elif '/sales/' in delete_url:
            product_id = delete_url.split('/sales/')[1].split('/delete')[0]
            # Check if this sale has dependencies in BankReconSales
            from models import BankReconSales
            bank_recon_dep = BankReconSales.query.filter_by(product_id=product_id).first()
            return jsonify(bank_recon_dep is not None)
        
        elif '/expenses/' in delete_url:
            expense_id = int(delete_url.split('/expenses/')[1].split('/delete')[0])
            # Check if this expense has dependencies in BankReconExpenses
            from models import BankReconExpenses
            bank_recon_dep = BankReconExpenses.query.filter_by(id=expense_id).first()
            return jsonify(bank_recon_dep is not None)
        
    except (ValueError, IndexError, AttributeError):
        pass
    
    return jsonify(False)


@api_validation_bp.route("/validate-bank-account/<account_number>")
@login_required
def validate_bank_account_api(account_number):
    """Validate bank account against non-receipt accounts"""
    NON_RECEIPT_ACCOUNTS = {
        "1000084206087", "57861258", "1014657935101", "08804884936001",
        "0001883620101", "1000564090001", "5038523396011", "01320927866200",
        "01320927862269", "0911190064"
    }
    
    is_non_receipt = account_number in NON_RECEIPT_ACCOUNTS
    return jsonify({
        "valid": True,
        "is_non_receipt": is_non_receipt,
        "warning": "Non-receipt account" if is_non_receipt else None
    })


@api_validation_bp.route("/validate-format/<field_type>/<value>")
@login_required
def validate_format_api(field_type, value):
    """Validate field formats"""
    try:
        if field_type == "number":
            num = float(value)
            return jsonify({
                "valid": True,
                "formatted": round(num, 2),
                "error": None
            })
        
        elif field_type == "integer":
            num = int(value)
            if num <= 0:
                return jsonify({
                    "valid": False,
                    "error": "Must be positive integer"
                })
            return jsonify({
                "valid": True,
                "formatted": num,
                "error": None
            })
        
        elif field_type == "price":
            num = float(value)
            if num < 0:
                return jsonify({
                    "valid": False,
                    "error": "Price cannot be negative"
                })
            return jsonify({
                "valid": True,
                "formatted": round(num, 2),
                "error": None
            })
        
        else:
            return jsonify({"valid": True, "error": None})
    
    except (ValueError, TypeError):
        return jsonify({
            "valid": False,
            "error": f"Invalid {field_type} format"
        })
