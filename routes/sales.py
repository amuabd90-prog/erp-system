from datetime import date, datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from auth import has_role, log_action
from forms import SalesForm
from models import AfterSale, Inventory, InventoryIn, Sales, StockOut, db
from utils import recompute_reports, safe_commit
from validators import (
    ValidationError, DuplicateError, SyncError, check_duplicate_sales,
    check_after_sale_availability, safe_transaction, log_audit_action,
    flash_validation_errors, validate_positive_number, validate_positive_integer,
    validate_bank_account_match, check_delete_dependencies
)
from export_utils import (
    export_inventory_in_csv, export_inventory_csv, export_sales_csv, export_after_sale_csv
)


sales_bp = Blueprint("sales", __name__)


def sync_inventory_in_from_stockout() -> None:
    for row in StockOut.query.all():
        if InventoryIn.query.filter_by(inv_no=row.inventory_no).first() is None:
            db.session.add(
                InventoryIn(
                    inv_no=row.inventory_no,
                    item=row.item,
                    brand=row.brand,
                    color=row.color,
                    description=row.description,
                    size=row.size,
                    pieces=row.pieces,
                    price=row.price,
                    received_by=row.received_by,
                    date=row.date,
                )
            )
    db.session.commit()


def _restore_inventory_from_sale(sale: Sales) -> None:
    if Inventory.query.get(sale.product_id) is None:
        db.session.add(
            Inventory(
                inv_no=sale.product_id,
                item=sale.item_type,
                brand=sale.brand,
                color=sale.color,
                description=sale.description,
                size=sale.size,
                pieces=sale.quantity,
                price=sale.price,
                received_by=sale.sales_rep,
                status="No",
            )
        )
    AfterSale.query.filter_by(inv_no=sale.product_id).delete()


def _consume_inventory_to_sale(sale: Sales, inventory: Inventory) -> None:
    sale.item_type = inventory.item
    sale.brand = inventory.brand
    sale.color = inventory.color
    sale.size = inventory.size
    if not sale.description:
        sale.description = inventory.description
    if not sale.quantity:
        sale.quantity = inventory.pieces
    if not sale.price:
        sale.price = inventory.price

    db.session.add(
        AfterSale(
            date=sale.date,
            inv_no=inventory.inv_no,
            item=inventory.item,
            brand=inventory.brand,
            color=inventory.color,
            description=inventory.description,
            size=inventory.size,
            pieces=sale.quantity,
            price=sale.price,
            sold_by=sale.sales_rep,
            status="Yes" if sale.status == "Yes" else "No",
        )
    )
    db.session.delete(inventory)


@sales_bp.route("/")
@login_required
@has_role("Sales Person", "Admin")
def index():
    return redirect(url_for("sales.sales_page"))


@sales_bp.route("/inventory-in")
@login_required
@has_role("Sales Person", "Admin")
def inventory_in_page():
    sync_inventory_in_from_stockout()
    rows = InventoryIn.query.order_by(InventoryIn.date.desc(), InventoryIn.created_at.desc()).all()
    return render_template("sales/inventory_in.html", rows=rows)


@sales_bp.route("/inventory-in/create", methods=["POST"])
@login_required
@has_role("Sales Person", "Admin")
def create_inventory_in():
    inv_no = (request.form.get("inv_no") or "").strip()
    try:
        if not inv_no:
            raise ValidationError("Inventory In requires Inv No.")
        
        if InventoryIn.query.filter_by(inv_no=inv_no).first():
            raise DuplicateError(f"Inv No '{inv_no}' already exists in Inventory In.")
        
        # Validate inputs
        pieces = validate_positive_integer(request.form.get("pieces") or 1, "Pieces")
        price = validate_positive_number(request.form.get("price") or 0, "Price")
        
        row = InventoryIn(
            inv_no=inv_no,
            item=request.form.get("item"),
            brand=request.form.get("brand"),
            color=request.form.get("color"),
            description=request.form.get("description"),
            size=request.form.get("size"),
            pieces=pieces,
            price=price,
            received_by=request.form.get("received_by"),
            date=datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()
            if request.form.get("date")
            else date.today(),
        )
        
        db.session.add(row)
        db.session.commit()
        flash("Inventory In created successfully.", "success")
        
        # Log audit trail
        log_audit_action(
            current_user.id, current_user.username,
            "CREATE", "SALES", inv_no,
            f"Inventory In created: {row.item} - {row.brand}"
        )
        
    except (ValidationError, DuplicateError) as e:
        flash(str(e), "error")
        if "inv_no" in str(e).lower():
            flash("Please check the highlighted Inv No field.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to create Inventory In: {str(e)}", "error")
    
    return redirect(url_for("sales.inventory_in_page"))


@sales_bp.route("/inventory-in/<int:row_id>/update", methods=["POST"])
@login_required
@has_role("Sales Person")
def update_inventory_in(row_id: int):
    row = InventoryIn.query.get_or_404(row_id)
    row.item = request.form.get("item")
    row.brand = request.form.get("brand")
    row.color = request.form.get("color")
    row.description = request.form.get("description")
    row.size = request.form.get("size")
    row.pieces = int(request.form.get("pieces") or 1)
    row.price = float(request.form.get("price") or 0)
    row.received_by = request.form.get("received_by")
    if request.form.get("date"):
        row.date = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()
    safe_commit("Inventory In updated.")
    log_action("UPDATE", "SALES", str(row_id), "Inventory In updated")
    return redirect(url_for("sales.inventory_in_page"))


@sales_bp.route("/inventory-in/<int:row_id>/delete", methods=["POST"])
@login_required
@has_role("Sales Person")
def delete_inventory_in(row_id: int):
    try:
        row = InventoryIn.query.get_or_404(row_id)
        
        # Check if this item has been moved to inventory
        if Inventory.query.get(row.inv_no):
            raise ValidationError("Cannot delete: This item has been moved to inventory. Delete from inventory first.")
        
        # Check if this item has been sold
        if Sales.query.filter_by(product_id=row.inv_no).first():
            raise ValidationError("Cannot delete: This item has been sold.")
        
        db.session.delete(row)
        db.session.commit()
        flash("Inventory In row deleted successfully.", "success")
        
        # Log audit trail
        log_audit_action(
            current_user.id, current_user.username,
            "DELETE", "SALES", str(row_id),
            f"Inventory In deleted: {row.item} - {row.brand}"
        )
        
    except ValidationError as e:
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete Inventory In: {str(e)}", "error")
    
    return redirect(url_for("sales.inventory_in_page"))


@sales_bp.route("/inventory")
@login_required
@has_role("Sales Person", "Admin")
def inventory_page():
    query = Inventory.query
    item = (request.args.get("item") or "").strip()
    brand = (request.args.get("brand") or "").strip()
    status = (request.args.get("status") or "").strip()
    if item:
        query = query.filter(Inventory.item.ilike(f"%{item}%"))
    if brand:
        query = query.filter(Inventory.brand.ilike(f"%{brand}%"))
    if status:
        query = query.filter(Inventory.status == status)
    rows = query.order_by(Inventory.created_at.desc()).all()
    return render_template("sales/inventory.html", rows=rows, item=item, brand=brand, status=status)


@sales_bp.route("/sales")
@login_required
@has_role("Sales Person", "Admin")
def sales_page():
    return render_template(
        "sales/index.html",
        sales_rows=Sales.query.order_by(Sales.date.desc()).all(),
        form=SalesForm(date=date.today()),
        editing=None,
    )


@sales_bp.route("/sales/<product_id>/edit")
@login_required
@has_role("Sales Person", "Admin")
def edit_sale_page(product_id: str):
    sale = Sales.query.get_or_404(product_id)
    form = SalesForm(obj=sale)
    return render_template(
        "sales/index.html",
        sales_rows=Sales.query.order_by(Sales.date.desc()).all(),
        form=form,
        editing=sale,
    )


@sales_bp.route("/create", methods=["POST"])
@login_required
@has_role("Sales Person", "Admin")
def create_sale():
    form = SalesForm()
    if form.validate_on_submit():
        try:
            product_id = form.product_id.data.strip()
            
            # Check for duplicates
            check_duplicate_sales(product_id)
            
            # Check if already sold
            check_after_sale_availability(product_id)
            
            # Validate inventory availability
            inventory = Inventory.query.get(product_id)
            if inventory is None:
                raise ValidationError(f"Product ID '{product_id}' not found in showroom inventory.")
            
            # Validate inputs
            quantity = validate_positive_integer(form.quantity.data or inventory.pieces, "Quantity")
            price = validate_positive_number(form.price.data or inventory.price, "Price")
            deduction = validate_positive_number(form.deduction.data or 0.0, "Deduction")
            
            # Validate bank account
            validate_bank_account_match(form.deposited_account_number.data)
            
            # Create sale with transaction safety
            def create_sale_records():
                sale = Sales(
                    product_id=product_id,
                    date=form.date.data,
                    item_type=inventory.item,
                    brand=inventory.brand,
                    color=inventory.color,
                    size=inventory.size,
                    quantity=quantity,
                    price=price,
                    bank_invoice_no=form.bank_invoice_no.data,
                    invoice_image=form.invoice_image.data,
                    sales_rep=form.sales_rep.data,
                    deduction=deduction,
                    description=form.description.data or inventory.description,
                    status=form.status.data,
                    ha_receipt_number=form.ha_receipt_number.data,
                    deposited_account_number=form.deposited_account_number.data,
                )
                
                # Create after sale record
                after_sale = AfterSale(
                    date=form.date.data,
                    inv_no=inventory.inv_no,
                    item=inventory.item,
                    brand=inventory.brand,
                    color=inventory.color,
                    description=inventory.description,
                    size=inventory.size,
                    pieces=quantity,
                    price=price,
                    sold_by=form.sales_rep.data,
                    status="Yes" if form.status.data == "Yes" else "No",
                )
                
                # Remove from inventory
                db.session.delete(inventory)
                
                return [sale, after_sale]
            
            records = safe_transaction(create_sale_records, "Failed to create sale")
            flash("Sale saved and inventory reduced successfully.", "success")
            
            # Recompute reports
            recompute_reports()
            
            # Log audit trail
            log_audit_action(
                current_user.id, current_user.username,
                "CREATE", "SALES", product_id,
                f"Sale created: {inventory.item} - {inventory.brand}"
            )
            
        except (ValidationError, DuplicateError, SyncError) as e:
            flash(str(e), "error")
            if "product_id" in str(e).lower():
                flash("Please check the highlighted Product ID field.", "warning")
        except Exception as e:
            flash(f"Unexpected error: {str(e)}", "error")
    else:
        flash_validation_errors(form)
    
    return redirect(url_for("sales.sales_page"))


@sales_bp.route("/<product_id>/update", methods=["POST"])
@login_required
@has_role("Sales Person", "Admin")
def update_sale(product_id: str):
    existing = Sales.query.get_or_404(product_id)
    form = SalesForm()
    if not form.validate_on_submit():
        return redirect(url_for("sales.edit_sale_page", product_id=product_id))

    new_product_id = form.product_id.data.strip()
    if new_product_id != existing.product_id and Sales.query.get(new_product_id):
        flash("New Product ID already exists in sales.", "warning")
        return redirect(url_for("sales.edit_sale_page", product_id=product_id))

    if new_product_id != existing.product_id:
        _restore_inventory_from_sale(existing)
        target_inventory = Inventory.query.get(new_product_id)
        if target_inventory is None:
            flash("Replacement Product ID does not exist in inventory.", "warning")
            db.session.rollback()
            return redirect(url_for("sales.edit_sale_page", product_id=product_id))
        existing.product_id = new_product_id
        _consume_inventory_to_sale(existing, target_inventory)
    else:
        after_sale = AfterSale.query.filter_by(inv_no=existing.product_id).first()
        if after_sale:
            after_sale.status = "Yes" if form.status.data == "Yes" else "No"
            after_sale.sold_by = form.sales_rep.data
            after_sale.date = form.date.data

    existing.date = form.date.data
    existing.quantity = form.quantity.data
    existing.price = form.price.data
    existing.bank_invoice_no = form.bank_invoice_no.data
    existing.invoice_image = form.invoice_image.data
    existing.sales_rep = form.sales_rep.data
    existing.deduction = form.deduction.data or 0.0
    existing.description = form.description.data
    existing.status = form.status.data
    existing.ha_receipt_number = form.ha_receipt_number.data
    existing.deposited_account_number = form.deposited_account_number.data
    safe_commit("Sale updated.")
    recompute_reports()
    log_action("UPDATE", "SALES", existing.product_id, "Sale updated")
    return redirect(url_for("sales.sales_page"))


@sales_bp.route("/<product_id>/delete", methods=["POST"])
@login_required
@has_role("Sales Person", "Admin")
def delete_sale(product_id: str):
    try:
        sale = Sales.query.get_or_404(product_id)
        
        # Check dependencies before deletion
        check_delete_dependencies(
            Sales, product_id,
            [(BankReconSales, 'product_id')]
        )
        
        # Restore inventory
        if Inventory.query.get(product_id) is None:
            inventory = Inventory(
                inv_no=product_id,
                item=sale.item_type,
                brand=sale.brand,
                color=sale.color,
                description=sale.description,
                size=sale.size,
                pieces=sale.quantity,
                price=sale.price,
                received_by=sale.sales_rep,
                status="No",
            )
            db.session.add(inventory)
        
        # Remove after sale record
        AfterSale.query.filter_by(inv_no=product_id).delete()
        
        # Delete sale
        db.session.delete(sale)
        db.session.commit()
        
        flash("Sale removed and inventory restored successfully.", "success")
        
        # Recompute reports
        recompute_reports()
        
        # Log audit trail
        log_audit_action(
            current_user.id, current_user.username,
            "DELETE", "SALES", product_id,
            f"Sale removed: {sale.item_type} - {sale.brand}"
        )
        
    except ValidationError as e:
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete sale: {str(e)}", "error")
    
    return redirect(url_for("sales.sales_page"))


@sales_bp.route("/after-sale")
@login_required
@has_role("Sales Person", "Admin")
def after_sale_page():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    query = AfterSale.query
    if from_date:
        query = query.filter(AfterSale.date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        query = query.filter(AfterSale.date <= datetime.strptime(to_date, "%Y-%m-%d").date())
    rows = query.order_by(AfterSale.date.desc(), AfterSale.created_at.desc()).all()
    return render_template("sales/after_sale.html", rows=rows, from_date=from_date, to_date=to_date)


@sales_bp.route("/export/inventory-in")
@login_required
@has_role("Sales Person", "Admin")
def export_inventory_in():
    return export_inventory_in_csv()


@sales_bp.route("/export/inventory")
@login_required
@has_role("Sales Person", "Admin")
def export_inventory():
    return export_inventory_csv()


@sales_bp.route("/export/sales")
@login_required
@has_role("Sales Person", "Admin")
def export_sales():
    return export_sales_csv()


@sales_bp.route("/export/after-sale")
@login_required
@has_role("Sales Person", "Admin")
def export_after_sale():
    return export_after_sale_csv()
