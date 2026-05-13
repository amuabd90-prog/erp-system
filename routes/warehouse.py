from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from auth import has_role, log_action
from forms import StockInForm, StockOutForm
from models import Inventory, InventoryIn, Stock, StockIn, StockOut, db
from utils import safe_commit
from validators import (
    ValidationError, DuplicateError, SyncError, check_duplicate_stock_in,
    check_duplicate_stock_out, check_inventory_availability,
    safe_transaction, log_audit_action, flash_validation_errors,
    validate_positive_number, validate_positive_integer
)
from export_utils import (
    export_stock_in_csv, export_stock_csv, export_stock_out_csv
)


warehouse_bp = Blueprint("warehouse", __name__)


@warehouse_bp.route("/")
@login_required
@has_role("Store Keeper", "Admin")
def index():
    return render_template(
        "warehouse/index.html",
        stock_in=StockIn.query.order_by(StockIn.date_added.desc()).all(),
        stock=Stock.query.order_by(Stock.date_added.desc()).all(),
        stock_out=StockOut.query.order_by(StockOut.date.desc()).all(),
        form_in=StockInForm(),
        form_out=StockOutForm(),
    )


@warehouse_bp.route("/stockin/create", methods=["POST"])
@login_required
@has_role("Store Keeper")
def create_stockin():
    form = StockInForm()
    if form.validate_on_submit():
        try:
            # Validate inputs
            inventory_no = form.inventory_no.data.strip()
            pieces = validate_positive_integer(form.pieces.data, "Pieces")
            price = validate_positive_number(form.price.data, "Price")
            
            # Check for duplicates
            check_duplicate_stock_in(inventory_no)
            
            # Create records with transaction safety
            def create_stock_records():
                stock_in = StockIn(
                    inventory_no=inventory_no,
                    item=form.item.data,
                    brand=form.brand.data,
                    color=form.color.data,
                    description=form.description.data,
                    size=form.size.data,
                    pieces=pieces,
                    price=price,
                    delivered_by=form.delivered_by.data,
                    received_by=form.received_by.data,
                    date_added=form.date_added.data,
                )
                stock = Stock(
                    inventory_no=inventory_no,
                    item=form.item.data,
                    brand=form.brand.data,
                    color=form.color.data,
                    description=form.description.data,
                    size=form.size.data,
                    pieces=pieces,
                    price=price,
                    received_by=form.received_by.data,
                    status="No",
                    date_added=form.date_added.data,
                )
                return [stock_in, stock]
            
            records = safe_transaction(create_stock_records, "Failed to create stock in records")
            flash("Stock in recorded successfully.", "success")
            
            # Log audit trail
            log_audit_action(
                current_user.id, current_user.username,
                "CREATE", "WAREHOUSE", inventory_no,
                f"Created stock in: {form.item.data} - {form.brand.data}"
            )
            
        except (ValidationError, DuplicateError, SyncError) as e:
            flash(str(e), "error")
            if "inventory_no" in str(e).lower():
                # Highlight duplicate field error
                flash("Please check the highlighted Inventory No field.", "warning")
        except Exception as e:
            flash(f"Unexpected error: {str(e)}", "error")
    else:
        flash_validation_errors(form)
    
    return redirect(url_for("warehouse.index"))


@warehouse_bp.route("/stockout/create", methods=["POST"])
@login_required
@has_role("Store Keeper")
def create_stockout():
    form = StockOutForm()
    if form.validate_on_submit():
        try:
            inventory_no = form.inventory_no.data.strip()
            
            # Validate inventory availability
            stock = check_inventory_availability(inventory_no)
            
            # Check for duplicates
            check_duplicate_stock_out(inventory_no)
            
            # Create records with transaction safety
            def create_stockout_records():
                stock_out = StockOut(
                    date=form.date.data,
                    inventory_no=stock.inventory_no,
                    item=stock.item,
                    brand=stock.brand,
                    color=stock.color,
                    description=stock.description,
                    size=stock.size,
                    pieces=stock.pieces,
                    price=stock.price,
                    delivered_by=form.delivered_by.data,
                    received_by=form.received_by.data,
                    status="Yes",
                )
                
                # Update stock status
                stock.status = "Yes"
                
                # Create inventory records
                inv_in = InventoryIn(
                    inv_no=stock.inventory_no,
                    item=stock.item,
                    brand=stock.brand,
                    color=stock.color,
                    description=stock.description,
                    size=stock.size,
                    pieces=stock.pieces,
                    price=stock.price,
                    received_by=stock.received_by,
                    date=form.date.data,
                )
                
                inventory = Inventory(
                    inv_no=stock.inventory_no,
                    item=stock.item,
                    brand=stock.brand,
                    color=stock.color,
                    description=stock.description,
                    size=stock.size,
                    pieces=stock.pieces,
                    price=stock.price,
                    received_by=stock.received_by,
                    status="No",
                )
                
                return [stock_out, inv_in, inventory]
            
            records = safe_transaction(create_stockout_records, "Failed to stock out item")
            flash("Stock moved to showroom inventory successfully.", "success")
            
            # Log audit trail
            log_audit_action(
                current_user.id, current_user.username,
                "CREATE", "WAREHOUSE", inventory_no,
                f"Stocked out: {stock.item} - {stock.brand}"
            )
            
        except (ValidationError, DuplicateError, SyncError) as e:
            flash(str(e), "error")
            if "inventory_no" in str(e).lower():
                flash("Please check the highlighted Inventory No field.", "warning")
        except Exception as e:
            flash(f"Unexpected error: {str(e)}", "error")
    else:
        flash_validation_errors(form)
    
    return redirect(url_for("warehouse.index"))


@warehouse_bp.route("/stockout/<int:stockout_id>/delete", methods=["POST"])
@login_required
@has_role("Store Keeper")
def delete_stockout(stockout_id: int):
    try:
        row = StockOut.query.get_or_404(stockout_id)
        
        # Check dependencies before deletion
        check_delete_dependencies(
            StockOut, stockout_id,
            [(Sales, 'product_id'), (AfterSale, 'inv_no')]
        )
        
        # Restore stock status
        stock = Stock.query.get(row.inventory_no)
        if stock:
            stock.status = "No"
        
        # Remove related inventory records
        InventoryIn.query.filter_by(inv_no=row.inventory_no).delete()
        Inventory.query.filter_by(inv_no=row.inventory_no).delete()
        
        # Delete stock out record
        db.session.delete(row)
        db.session.commit()
        
        flash("Stock out reversed and stock restored successfully.", "success")
        
        # Log audit trail
        log_audit_action(
            current_user.id, current_user.username,
            "DELETE", "WAREHOUSE", str(stockout_id),
            f"Reverted stock out: {row.item} - {row.brand}"
        )
        
    except ValidationError as e:
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete stock out: {str(e)}", "error")
    
    return redirect(url_for("warehouse.index"))


@warehouse_bp.route("/stockin/<inventory_no>/delete", methods=["POST"])
@login_required
@has_role("Store Keeper")
def delete_stockin(inventory_no: str):
    try:
        # Check dependencies before deletion
        stock_in = StockIn.query.get_or_404(inventory_no)
        
        # Check if this item has been stocked out
        if StockOut.query.filter_by(inventory_no=inventory_no).first():
            raise ValidationError("Cannot delete: This item has been stocked out. Delete the stock out first.")
        
        # Check if this item is in sales
        if Sales.query.filter_by(product_id=inventory_no).first():
            raise ValidationError("Cannot delete: This item has been sold.")
        
        # Delete all related records
        Stock.query.filter_by(inventory_no=inventory_no).delete()
        StockIn.query.filter_by(inventory_no=inventory_no).delete()
        
        db.session.commit()
        flash("Stock entry removed successfully.", "success")
        
        # Log audit trail
        log_audit_action(
            current_user.id, current_user.username,
            "DELETE", "WAREHOUSE", inventory_no,
            f"Deleted stock records: {stock_in.item} - {stock_in.brand}"
        )
        
    except ValidationError as e:
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete stock entry: {str(e)}", "error")
    
    return redirect(url_for("warehouse.index"))


@warehouse_bp.route("/export/stock-in")
@login_required
@has_role("Store Keeper", "Admin")
def export_stock_in():
    return export_stock_in_csv()


@warehouse_bp.route("/export/stock")
@login_required
@has_role("Store Keeper", "Admin")
def export_stock():
    return export_stock_csv()


@warehouse_bp.route("/export/stock-out")
@login_required
@has_role("Store Keeper", "Admin")
def export_stock_out():
    return export_stock_out_csv()
