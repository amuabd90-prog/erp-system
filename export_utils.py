from datetime import date, datetime
from flask import make_response
import csv
import io
from models import (
    StockIn, Stock, StockOut, InventoryIn, Inventory, AfterSale, 
    Sales, Expenses, AuditLog, WeeklyCommission, BankReconSales, 
    BankReconExpenses, CostOfGoods, Reconciliation
)


def export_stock_in_csv(filtered_data=None):
    """Export Stock In data to CSV"""
    data = filtered_data if filtered_data else StockIn.query.order_by(StockIn.date_added.desc()).all()
    
    headers = [
        'Inventory No', 'Item', 'Brand', 'Color', 'Description', 'Size',
        'Pieces', 'Price', 'Delivered By', 'Received By', 'Date Added', 
        'Created At', 'Updated At'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.inventory_no,
            item.item,
            item.brand,
            item.color or '',
            item.description or '',
            item.size or '',
            item.pieces,
            f"{item.price:.2f}",
            item.delivered_by or '',
            item.received_by or '',
            item.date_added.strftime('%Y-%m-%d') if item.date_added else '',
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        ])
    
    return create_csv_response(headers, rows, 'stock_in')


def export_stock_csv(filtered_data=None):
    """Export Stock data to CSV"""
    data = filtered_data if filtered_data else Stock.query.order_by(Stock.date_added.desc()).all()
    
    headers = [
        'Inventory No', 'Item', 'Brand', 'Color', 'Description', 'Size',
        'Pieces', 'Price', 'Received By', 'Status', 'Date Added',
        'Created At', 'Updated At'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.inventory_no,
            item.item,
            item.brand,
            item.color or '',
            item.description or '',
            item.size or '',
            item.pieces,
            f"{item.price:.2f}",
            item.received_by or '',
            item.status,
            item.date_added.strftime('%Y-%m-%d') if item.date_added else '',
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        ])
    
    return create_csv_response(headers, rows, 'stock')


def export_stock_out_csv(filtered_data=None):
    """Export Stock Out data to CSV"""
    data = filtered_data if filtered_data else StockOut.query.order_by(StockOut.date.desc()).all()
    
    headers = [
        'ID', 'Date', 'Inventory No', 'Item', 'Brand', 'Color', 'Description', 'Size',
        'Pieces', 'Price', 'Delivered By', 'Received By', 'Status',
        'Created At', 'Updated At'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.id,
            item.date.strftime('%Y-%m-%d') if item.date else '',
            item.inventory_no,
            item.item,
            item.brand,
            item.color or '',
            item.description or '',
            item.size or '',
            item.pieces,
            f"{item.price:.2f}",
            item.delivered_by or '',
            item.received_by or '',
            item.status,
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        ])
    
    return create_csv_response(headers, rows, 'stock_out')


def export_inventory_in_csv(filtered_data=None):
    """Export Inventory In data to CSV"""
    data = filtered_data if filtered_data else InventoryIn.query.order_by(InventoryIn.date.desc()).all()
    
    headers = [
        'ID', 'Inv No', 'Item', 'Brand', 'Color', 'Description', 'Size',
        'Pieces', 'Price', 'Received By', 'Date',
        'Created At', 'Updated At'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.id,
            item.inv_no,
            item.item,
            item.brand,
            item.color or '',
            item.description or '',
            item.size or '',
            item.pieces,
            f"{item.price:.2f}",
            item.received_by or '',
            item.date.strftime('%Y-%m-%d') if item.date else '',
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        ])
    
    return create_csv_response(headers, rows, 'inventory_in')


def export_inventory_csv(filtered_data=None):
    """Export Inventory data to CSV"""
    data = filtered_data if filtered_data else Inventory.query.order_by(Inventory.created_at.desc()).all()
    
    headers = [
        'Inv No', 'Item', 'Brand', 'Color', 'Description', 'Size',
        'Pieces', 'Price', 'Received By', 'Status',
        'Created At', 'Updated At'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.inv_no,
            item.item,
            item.brand,
            item.color or '',
            item.description or '',
            item.size or '',
            item.pieces,
            f"{item.price:.2f}",
            item.received_by or '',
            item.status,
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        ])
    
    return create_csv_response(headers, rows, 'inventory')


def export_sales_csv(filtered_data=None):
    """Export Sales data to CSV"""
    data = filtered_data if filtered_data else Sales.query.order_by(Sales.date.desc()).all()
    
    headers = [
        'Product ID', 'Date', 'Item Type', 'Brand', 'Color', 'Size',
        'Quantity', 'Price', 'Total Amount', 'Bank Invoice No', 'Invoice Image',
        'Sales Rep', 'Deduction', 'Description', 'Status', 'H/A Receipt Number',
        'Deposited Account Number', 'Created At', 'Updated At'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.product_id,
            item.date.strftime('%Y-%m-%d') if item.date else '',
            item.item_type,
            item.brand,
            item.color or '',
            item.size or '',
            item.quantity,
            f"{item.price:.2f}",
            f"{item.total_amount:.2f}",
            item.bank_invoice_no or '',
            item.invoice_image or '',
            item.sales_rep or '',
            f"{item.deduction:.2f}",
            item.description or '',
            item.status,
            item.ha_receipt_number or '',
            item.deposited_account_number or '',
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        ])
    
    return create_csv_response(headers, rows, 'sales')


def export_after_sale_csv(filtered_data=None):
    """Export After Sale data to CSV"""
    data = filtered_data if filtered_data else AfterSale.query.order_by(AfterSale.date.desc()).all()
    
    headers = [
        'ID', 'Date', 'Inv No', 'Item', 'Brand', 'Color', 'Description', 'Size',
        'Pieces', 'Price', 'Sold By', 'Status',
        'Created At', 'Updated At'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.id,
            item.date.strftime('%Y-%m-%d') if item.date else '',
            item.inv_no,
            item.item,
            item.brand,
            item.color or '',
            item.description or '',
            item.size or '',
            item.pieces,
            f"{item.price:.2f}",
            item.sold_by or '',
            item.status,
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        ])
    
    return create_csv_response(headers, rows, 'after_sale')


def export_expenses_csv(filtered_data=None):
    """Export Expenses data to CSV"""
    data = filtered_data if filtered_data else Expenses.query.order_by(Expenses.date.desc()).all()
    
    headers = [
        'ID', 'Date', 'Amount', 'Reason', 'Reference No', 'Invoice Image',
        'Payed By', 'Account Number', 'Status',
        'Created At', 'Updated At'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.id,
            item.date.strftime('%Y-%m-%d') if item.date else '',
            f"{item.amount:.2f}",
            item.reason,
            item.reference_no or '',
            item.invoice_image or '',
            item.payed_by or '',
            item.account_number or '',
            item.status,
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        ])
    
    return create_csv_response(headers, rows, 'expenses')


def export_audit_log_csv(filtered_data=None):
    """Export Audit Log data to CSV"""
    data = filtered_data if filtered_data else AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    
    headers = [
        'ID', 'User ID', 'Username', 'Action', 'Module', 'Target ID',
        'Details', 'Timestamp'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.id,
            item.user_id or '',
            item.username or '',
            item.action,
            item.module,
            item.target_id or '',
            item.details or '',
            item.timestamp.strftime('%Y-%m-%d %H:%M:%S') if item.timestamp else ''
        ])
    
    return create_csv_response(headers, rows, 'audit_log')


def export_weekly_commission_csv(filtered_data=None):
    """Export Weekly Commission data to CSV"""
    data = filtered_data if filtered_data else WeeklyCommission.query.order_by(WeeklyCommission.week_start.desc()).all()
    
    headers = [
        'ID', 'Week Start', 'Week End', 'Total Sales', 'Suits Sold', 'Coats Sold',
        'Sale Bonus 1%', 'Suit Bonus', 'Coat Bonus', 'Total Commission',
        'Created At', 'Updated At'
    ]
    
    rows = []
    for item in data:
        rows.append([
            item.id,
            item.week_start.strftime('%Y-%m-%d') if item.week_start else '',
            item.week_end.strftime('%Y-%m-%d') if item.week_end else '',
            f"{item.total_sales:.2f}",
            item.suits_sold,
            item.coats_sold,
            f"{item.sale_bonus_1pct:.2f}",
            f"{item.suit_bonus:.2f}",
            f"{item.coat_bonus:.2f}",
            f"{item.total_commission:.2f}",
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        ])
    
    return create_csv_response(headers, rows, 'weekly_commission')


def create_csv_response(headers, rows, filename_prefix):
    """Create CSV response with headers and data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(headers)
    
    # Write data rows
    for row in rows:
        writer.writerow(row)
    
    output.seek(0)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={filename_prefix}_{date.today().strftime('%Y-%m-%d')}.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response
