from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required
from auth import has_role, log_action
from models import (
    BankReconExpenses,
    BankReconSales,
    Expenses,
    NON_RECEIPT_ACCOUNTS,
    Sales,
    db,
)
from utils import safe_commit


bank_recon_bp = Blueprint("bank_recon", __name__)


@bank_recon_bp.route("/")
@login_required
@has_role("Auditor", "Accountant", "Viewer")
def index():
    sales_alerts = [
        f"{row.product_id} ({row.deposited_account_number or 'missing account'})"
        for row in BankReconSales.query.all()
        if (not row.deposited_account_number) or row.deposited_account_number in NON_RECEIPT_ACCOUNTS
    ]
    return render_template(
        "bank_recon/index.html",
        sales_rows=BankReconSales.query.order_by(BankReconSales.date.desc()).all(),
        expense_rows=BankReconExpenses.query.order_by(BankReconExpenses.date.desc()).all(),
        sales_alerts=sales_alerts,
    )


@bank_recon_bp.route("/sync", methods=["POST"])
@login_required
@has_role("Auditor", "Accountant")
def sync():
    BankReconSales.query.delete()
    BankReconExpenses.query.delete()
    validation_alerts = []
    for sale in Sales.query.filter_by(status="Yes").all():
        if (not sale.deposited_account_number) or sale.deposited_account_number in NON_RECEIPT_ACCOUNTS:
            validation_alerts.append(sale.product_id)
        db.session.add(
            BankReconSales(
                date=sale.date,
                product_id=sale.product_id,
                item=sale.item_type,
                brand=sale.brand,
                ha_receipt_number=sale.ha_receipt_number,
                bank_invoice_no=sale.bank_invoice_no,
                status=sale.status,
                deposited_account_number=sale.deposited_account_number,
            )
        )
    for exp in Expenses.query.filter_by(status="1").all():
        db.session.add(
            BankReconExpenses(
                date=exp.date,
                reasons=exp.reason,
                amount=exp.amount,
                bank_invoice_no=exp.reference_no,
                status=exp.status,
            )
        )
    safe_commit("Bank reconciliation synced.")
    if validation_alerts:
        flash(
            f"Account validation alerts for Product IDs: {', '.join(validation_alerts)}",
            "warning",
        )
    log_action("SYNC", "BANK_RECON", "", "Bank reconciliation data synced")
    return redirect(url_for("bank_recon.index"))
