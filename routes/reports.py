from datetime import date
from io import BytesIO
import pandas as pd
from flask import Blueprint, redirect, render_template, send_file, url_for
from flask_login import login_required
from reportlab.pdfgen import canvas
from auth import has_role, log_action
from forms import CostOfGoodsForm
from models import CostOfGoods, ExpenseReport, ProfitTaxReport, SalesReport, db
from utils import compute_tax_snapshot, safe_commit


reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/")
@login_required
@has_role("Accountant", "Auditor", "Viewer")
def index():
    return render_template(
        "reports/index.html",
        sales_rows=SalesReport.query.order_by(SalesReport.date.desc()).all(),
        expense_rows=ExpenseReport.query.order_by(ExpenseReport.date.desc()).all(),
        cogs_rows=CostOfGoods.query.order_by(CostOfGoods.date.desc()).all(),
        tax_rows=ProfitTaxReport.query.order_by(ProfitTaxReport.date.desc()).all(),
        cogs_form=CostOfGoodsForm(date=date.today()),
        editing_cogs=None,
    )


@reports_bp.route("/cogs/<int:cogs_id>/edit")
@login_required
@has_role("Accountant", "Auditor", "Viewer")
def edit_cogs(cogs_id: int):
    row = CostOfGoods.query.get_or_404(cogs_id)
    return render_template(
        "reports/index.html",
        sales_rows=SalesReport.query.order_by(SalesReport.date.desc()).all(),
        expense_rows=ExpenseReport.query.order_by(ExpenseReport.date.desc()).all(),
        cogs_rows=CostOfGoods.query.order_by(CostOfGoods.date.desc()).all(),
        tax_rows=ProfitTaxReport.query.order_by(ProfitTaxReport.date.desc()).all(),
        cogs_form=CostOfGoodsForm(obj=row),
        editing_cogs=row,
    )


@reports_bp.route("/cogs/create", methods=["POST"])
@login_required
@has_role("Accountant")
def create_cogs():
    form = CostOfGoodsForm()
    if form.validate_on_submit():
        row = CostOfGoods(
            date=form.date.data,
            item=form.item.data,
            brand=form.brand.data,
            purchasing_cost=form.purchasing_cost.data,
            purchasing_cost_under_value=form.purchasing_cost_under_value.data,
            shipping_cost=form.shipping_cost.data,
            tariff=form.tariff.data,
            transportation_cost=form.transportation_cost.data,
            total_cost_face_value=form.purchasing_cost.data
            + form.shipping_cost.data
            + form.tariff.data
            + form.transportation_cost.data,
            total_cost_under_value=form.purchasing_cost_under_value.data
            + form.shipping_cost.data
            + form.tariff.data
            + form.transportation_cost.data,
        )
        db.session.add(row)
        safe_commit("COGS row saved.")
        log_action("CREATE", "REPORTS", str(row.id), "COGS created")
    return redirect(url_for("reports.index"))


@reports_bp.route("/cogs/<int:cogs_id>/update", methods=["POST"])
@login_required
@has_role("Accountant")
def update_cogs(cogs_id: int):
    row = CostOfGoods.query.get_or_404(cogs_id)
    form = CostOfGoodsForm()
    if form.validate_on_submit():
        row.date = form.date.data
        row.item = form.item.data
        row.brand = form.brand.data
        row.purchasing_cost = form.purchasing_cost.data
        row.purchasing_cost_under_value = form.purchasing_cost_under_value.data
        row.shipping_cost = form.shipping_cost.data
        row.tariff = form.tariff.data
        row.transportation_cost = form.transportation_cost.data
        row.total_cost_face_value = (
            form.purchasing_cost.data
            + form.shipping_cost.data
            + form.tariff.data
            + form.transportation_cost.data
        )
        row.total_cost_under_value = (
            form.purchasing_cost_under_value.data
            + form.shipping_cost.data
            + form.tariff.data
            + form.transportation_cost.data
        )
        safe_commit("COGS row updated.")
        log_action("UPDATE", "REPORTS", str(row.id), "COGS updated")
    return redirect(url_for("reports.index"))


@reports_bp.route("/cogs/<int:cogs_id>/delete", methods=["POST"])
@login_required
@has_role("Accountant")
def delete_cogs(cogs_id: int):
    row = CostOfGoods.query.get_or_404(cogs_id)
    db.session.delete(row)
    safe_commit("COGS row deleted.")
    log_action("DELETE", "REPORTS", str(cogs_id), "COGS deleted")
    return redirect(url_for("reports.index"))


@reports_bp.route("/tax/recalculate", methods=["POST"])
@login_required
@has_role("Accountant")
def recalculate_tax():
    report = compute_tax_snapshot()
    log_action("UPDATE", "REPORTS", str(report.id), "Tax snapshot recalculated")
    return redirect(url_for("reports.index"))


@reports_bp.route("/export/excel")
@login_required
@has_role("Accountant", "Auditor", "Viewer")
def export_excel():
    rows = SalesReport.query.order_by(SalesReport.date.desc()).all()
    data = [
        {
            "Date": r.date.strftime("%d/%m/%Y"),
            "Product ID": r.product_id,
            "Item": r.item,
            "Total Sale": r.total_sale,
            "Status": r.status,
        }
        for r in rows
    ]
    output = BytesIO()
    pd.DataFrame(data).to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="sales_report.xlsx")


@reports_bp.route("/export/pdf")
@login_required
@has_role("Accountant", "Auditor", "Viewer")
def export_pdf():
    output = BytesIO()
    p = canvas.Canvas(output)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, 810, "H/A Sales Report")
    p.setFont("Helvetica", 10)
    y = 790
    for row in SalesReport.query.order_by(SalesReport.date.desc()).limit(40).all():
        p.drawString(
            40,
            y,
            f"{row.date.strftime('%d/%m/%Y')} | {row.product_id} | {row.item} | ETB {row.total_sale:,.2f}",
        )
        y -= 16
        if y < 50:
            p.showPage()
            y = 790
    p.save()
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="sales_report.pdf")


@reports_bp.route("/tax-summary/print")
@login_required
@has_role("Accountant", "Auditor", "Viewer")
def tax_summary_print():
    latest_tax = ProfitTaxReport.query.order_by(ProfitTaxReport.date.desc()).first()
    return render_template("reports/tax_summary_print.html", latest_tax=latest_tax)
