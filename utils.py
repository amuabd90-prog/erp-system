from collections import defaultdict
from datetime import date, timedelta
from flask import flash
from sqlalchemy import func
from models import (
    CostOfGoods,
    ExpenseReport,
    Expenses,
    Inventory,
    ProfitTaxReport,
    Sales,
    SalesReport,
    Stock,
    db,
)


NON_DEDUCTIBLE_KEYWORDS = {
    "salary",
    "salaries",
    "payroll",
    "wage",
    "wages",
    "staff salary",
    "employee salary",
    "employee payment",
    "staff payment",
    "worker salary",
    "worker payment",
    "compensation",
    "remuneration",
}


def etb(value: float) -> str:
    return f"ETB {value:,.2f}"


def format_date(d: date) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def compute_week_range(target_date: date):
    weekday = target_date.weekday()
    sunday_offset = (weekday + 1) % 7
    week_start = target_date - timedelta(days=sunday_offset)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def progressive_profit_tax(taxable_income: float) -> float:
    if taxable_income <= 24000:
        return 0.0
    brackets = [
        (24000, 48000, 0.15),
        (48000, 84000, 0.20),
        (84000, 120000, 0.25),
        (120000, 168000, 0.30),
        (168000, float("inf"), 0.35),
    ]
    tax = 0.0
    for lower, upper, rate in brackets:
        if taxable_income > lower:
            tax += (min(taxable_income, upper) - lower) * rate
    return max(tax, 0.0)


def is_deductible_expense(reason: str) -> bool:
    lowered = (reason or "").lower()
    return not any(k in lowered for k in NON_DEDUCTIBLE_KEYWORDS)


def recompute_reports():
    existing_sales_ids = {s.product_id for s in Sales.query.all()}
    if existing_sales_ids:
        SalesReport.query.filter(~SalesReport.product_id.in_(existing_sales_ids)).delete(
            synchronize_session=False
        )
    else:
        SalesReport.query.delete()

    for sale in Sales.query.all():
        report = SalesReport.query.get(sale.product_id) or SalesReport(product_id=sale.product_id)
        report.date = sale.date
        report.item = sale.item_type
        report.total_sale = sale.total_amount
        report.bank_receipt_number = sale.bank_invoice_no
        report.status = sale.status
        report.ha_receipt_number = sale.ha_receipt_number
        report.deposited_account_number = sale.deposited_account_number
        db.session.add(report)

    grouped_expenses = (
        db.session.query(Expenses.date, func.sum(Expenses.amount))
        .group_by(Expenses.date)
        .all()
    )
    ExpenseReport.query.delete()
    for exp_date, total in grouped_expenses:
        db.session.add(ExpenseReport(date=exp_date, total_expenses=total or 0.0))

    db.session.commit()


def get_cogs_for_sale(item_type: str, brand: str) -> float:
    row = (
        CostOfGoods.query.filter_by(item=item_type, brand=brand)
        .order_by(CostOfGoods.date.desc(), CostOfGoods.created_at.desc())
        .first()
    )
    return row.total_cost_under_value if row else 0.0


def compute_tax_snapshot(snapshot_date: date | None = None):
    current_date = snapshot_date or date.today()
    sales_rows = Sales.query.all()
    expenses_rows = Expenses.query.all()

    total_revenue = sum(s.total_amount for s in sales_rows)
    taxable_revenue = sum(s.total_amount for s in sales_rows if s.status == "Yes")
    deductible_expenses = sum(e.amount for e in expenses_rows if is_deductible_expense(e.reason))
    cogs = sum(get_cogs_for_sale(s.item_type, s.brand) * s.quantity for s in sales_rows)

    total_profit = total_revenue - deductible_expenses - cogs
    vat_15 = taxable_revenue * 0.15
    taxable_net_income = taxable_revenue - deductible_expenses - cogs - vat_15
    min_margin_base = cogs * 0.21
    adjusted_income = max(taxable_net_income, min_margin_base)
    profit_tax = progressive_profit_tax(adjusted_income)
    if total_profit < 0:
        profit_tax = max(total_revenue * 0.02, 0.0)
    total_tax_payable = vat_15 + profit_tax

    report = ProfitTaxReport(
        date=current_date,
        total_profit=total_profit,
        vat_15=vat_15,
        profit_tax=profit_tax,
        total_tax_payable=total_tax_payable,
    )
    db.session.add(report)
    db.session.commit()
    return report


def reconciliation_seed():
    grouped = defaultdict(lambda: {"store": 0, "inventory": 0})

    for row in Stock.query.filter_by(status="No").all():
        grouped[row.item]["store"] += row.pieces
    for row in Inventory.query.all():
        grouped[row.item]["inventory"] += row.pieces
    return grouped


def safe_commit(message: str = "Operation completed."):
    try:
        db.session.commit()
        flash(message, "success")
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        flash(f"Operation failed: {exc}", "danger")
