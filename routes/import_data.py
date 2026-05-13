import os
import csv
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from models import db, Stock, Sales, Expenses
import openpyxl
from datetime import datetime
import requests
import zipfile
import tempfile
from io import BytesIO

import_data_bp = Blueprint("import_data", __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_excel_file(file_path):
    """Parse Excel file and return data as list of dictionaries"""
    try:
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        data = []
        headers = []
        
        # Get headers from first row
        for cell in sheet[1]:
            headers.append(cell.value)
        
        # Get data from remaining rows
        for row in sheet.iter_rows(min_row=2):
            row_data = {}
            for i, cell in enumerate(row):
                if i < len(headers):
                    row_data[headers[i]] = cell.value
            data.append(row_data)
        
        return data, headers
    except Exception as e:
        raise Exception(f"Error parsing Excel file: {str(e)}")

def parse_csv_file(file_path):
    """Parse CSV file and return data as list of dictionaries"""
    try:
        data = []
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(dict(row))
        
        if data:
            headers = list(data[0].keys())
        else:
            headers = []
        
        return data, headers
    except Exception as e:
        raise Exception(f"Error parsing CSV file: {str(e)}")

@import_data_bp.route("/warehouse/import", methods=["GET", "POST"])
@login_required
def import_warehouse():
    """Import warehouse stock data"""
    if request.method == "POST":
        if 'file' not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("No file selected", "error")
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('temp', filename)
            
            # Create temp directory if it doesn't exist
            os.makedirs('temp', exist_ok=True)
            file.save(file_path)
            
            try:
                # Parse file based on extension
                if filename.endswith('.xlsx') or filename.endswith('.xls'):
                    data, headers = parse_excel_file(file_path)
                else:
                    data, headers = parse_csv_file(file_path)
                
                # Define warehouse field mappings
                warehouse_fields = {
                    'item': 'Item Name',
                    'brand': 'Brand', 
                    'color': 'Color',
                    'size': 'Size',
                    'quantity': 'Quantity',
                    'unit_price': 'Unit Price',
                    'total_amount': 'Total Amount',
                    'supplier': 'Supplier',
                    'date': 'Date',
                    'notes': 'Notes'
                }
                
                # Store data in session for mapping
                from flask import session
                session['import_data'] = data
                session['import_headers'] = headers
                session['import_type'] = 'warehouse'
                session['field_mappings'] = warehouse_fields
                
                return render_template("import/mapping.html", 
                                     headers=headers, 
                                     fields=warehouse_fields,
                                     data_preview=data[:5])  # Show first 5 rows as preview
                
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return redirect(request.url)
        else:
            flash("Invalid file type. Please upload CSV or Excel files.", "error")
            return redirect(request.url)
    
    return render_template("import/upload.html", import_type="warehouse")

@import_data_bp.route("/sales/import", methods=["GET", "POST"])
@login_required
def import_sales():
    """Import sales data"""
    if request.method == "POST":
        if 'file' not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("No file selected", "error")
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('temp', filename)
            
            # Create temp directory if it doesn't exist
            os.makedirs('temp', exist_ok=True)
            file.save(file_path)
            
            try:
                # Parse file based on extension
                if filename.endswith('.xlsx') or filename.endswith('.xls'):
                    data, headers = parse_excel_file(file_path)
                else:
                    data, headers = parse_csv_file(file_path)
                
                # Define sales field mappings
                sales_fields = {
                    'item': 'Item Name',
                    'item_type': 'Item Type',
                    'quantity': 'Quantity',
                    'unit_price': 'Unit Price',
                    'total_amount': 'Total Amount',
                    'customer_name': 'Customer Name',
                    'customer_phone': 'Customer Phone',
                    'date': 'Date',
                    'payment_method': 'Payment Method',
                    'notes': 'Notes'
                }
                
                # Store data in session for mapping
                from flask import session
                session['import_data'] = data
                session['import_headers'] = headers
                session['import_type'] = 'sales'
                session['field_mappings'] = sales_fields
                
                return render_template("import/mapping.html", 
                                     headers=headers, 
                                     fields=sales_fields,
                                     data_preview=data[:5])  # Show first 5 rows as preview
                
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return redirect(request.url)
        else:
            flash("Invalid file type. Please upload CSV or Excel files.", "error")
            return redirect(request.url)
    
    return render_template("import/upload.html", import_type="sales")

@import_data_bp.route("/expenses/import", methods=["GET", "POST"])
@login_required
def import_expenses():
    """Import expenses data"""
    if request.method == "POST":
        if 'file' not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("No file selected", "error")
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('temp', filename)
            
            # Create temp directory if it doesn't exist
            os.makedirs('temp', exist_ok=True)
            file.save(file_path)
            
            try:
                # Parse file based on extension
                if filename.endswith('.xlsx') or filename.endswith('.xls'):
                    data, headers = parse_excel_file(file_path)
                else:
                    data, headers = parse_csv_file(file_path)
                
                # Define expenses field mappings
                expenses_fields = {
                    'category': 'Category',
                    'amount': 'Amount',
                    'description': 'Description',
                    'date': 'Date',
                    'payment_method': 'Payment Method',
                    'receipt_number': 'Receipt Number',
                    'vendor': 'Vendor',
                    'notes': 'Notes'
                }
                
                # Store data in session for mapping
                from flask import session
                session['import_data'] = data
                session['import_headers'] = headers
                session['import_type'] = 'expenses'
                session['field_mappings'] = expenses_fields
                
                return render_template("import/mapping.html", 
                                     headers=headers, 
                                     fields=expenses_fields,
                                     data_preview=data[:5])  # Show first 5 rows as preview
                
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return redirect(request.url)
        else:
            flash("Invalid file type. Please upload CSV or Excel files.", "error")
            return redirect(request.url)
    
    return render_template("import/upload.html", import_type="expenses")

@import_data_bp.route("/mapping", methods=["POST"])
@login_required
def process_mapping():
    """Process column mapping and show preview with validation"""
    from flask import session
    
    # Get mapping from form
    mapping = {}
    for field, header in session['field_mappings'].items():
        mapped_header = request.form.get(f"map_{field}")
        if mapped_header:
            mapping[field] = mapped_header
    
    # Get data from session
    data = session.get('import_data', [])
    import_type = session.get('import_type')
    
    # Validate and process data
    validated_data = []
    errors = []
    
    for i, row in enumerate(data):
        validated_row = {}
        row_errors = []
        
        for field, header in mapping.items():
            value = row.get(header, '')
            
            # Validate based on field type and import type
            if field in ['quantity', 'unit_price', 'total_amount', 'amount']:
                try:
                    validated_row[field] = float(value) if value else 0.0
                except (ValueError, TypeError):
                    row_errors.append(f"Invalid {field}: {value}")
                    validated_row[field] = 0.0
            elif field == 'date':
                if value:
                    try:
                        validated_row[field] = datetime.strptime(str(value), '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            validated_row[field] = datetime.strptime(str(value), '%m/%d/%Y').date()
                        except ValueError:
                            row_errors.append(f"Invalid date format: {value}")
                            validated_row[field] = datetime.now().date()
                else:
                    validated_row[field] = datetime.now().date()
            else:
                validated_row[field] = str(value) if value else ''
        
        if row_errors:
            errors.append({'row': i + 1, 'errors': row_errors})
        
        validated_data.append(validated_row)
    
    # Store validated data in session
    session['validated_data'] = validated_data
    session['mapping'] = mapping
    session['validation_errors'] = errors
    
    return render_template("import/preview.html", 
                         data=validated_data[:10],  # Show first 10 rows
                         errors=errors,
                         import_type=import_type,
                         total_rows=len(validated_data))

@import_data_bp.route("/confirm_import", methods=["POST"])
@login_required
def confirm_import():
    """Final import of validated data"""
    from flask import session
    
    validated_data = session.get('validated_data', [])
    mapping = session.get('mapping', {})
    import_type = session.get('import_type')
    errors = session.get('validation_errors', [])
    
    imported_count = 0
    skipped_count = 0
    
    try:
        for row_data in validated_data:
            try:
                if import_type == 'warehouse':
                    # Create Stock record
                    stock = Stock(
                        item=row_data.get('item', ''),
                        brand=row_data.get('brand', ''),
                        color=row_data.get('color', ''),
                        size=row_data.get('size', ''),
                        quantity=int(row_data.get('quantity', 0)),
                        unit_price=float(row_data.get('unit_price', 0)),
                        total_amount=float(row_data.get('total_amount', 0)),
                        supplier=row_data.get('supplier', ''),
                        date=row_data.get('date', datetime.now().date()),
                        notes=row_data.get('notes', ''),
                        company_id=current_user.company_id
                    )
                    db.session.add(stock)
                    imported_count += 1
                
                elif import_type == 'sales':
                    # Create Sales record
                    sale = Sales(
                        item=row_data.get('item', ''),
                        item_type=row_data.get('item_type', ''),
                        quantity=int(row_data.get('quantity', 0)),
                        unit_price=float(row_data.get('unit_price', 0)),
                        total_amount=float(row_data.get('total_amount', 0)),
                        customer_name=row_data.get('customer_name', ''),
                        customer_phone=row_data.get('customer_phone', ''),
                        date=row_data.get('date', datetime.now().date()),
                        payment_method=row_data.get('payment_method', ''),
                        notes=row_data.get('notes', ''),
                        company_id=current_user.company_id
                    )
                    db.session.add(sale)
                    imported_count += 1
                
                elif import_type == 'expenses':
                    # Create Expenses record
                    expense = Expenses(
                        category=row_data.get('category', ''),
                        amount=float(row_data.get('amount', 0)),
                        description=row_data.get('description', ''),
                        date=row_data.get('date', datetime.now().date()),
                        payment_method=row_data.get('payment_method', ''),
                        receipt_number=row_data.get('receipt_number', ''),
                        vendor=row_data.get('vendor', ''),
                        notes=row_data.get('notes', ''),
                        company_id=current_user.company_id
                    )
                    db.session.add(expense)
                    imported_count += 1
                
            except Exception as e:
                skipped_count += 1
                continue
        
        db.session.commit()
        
        flash(f"Import completed! {imported_count} rows imported, {skipped_count} skipped.", "success")
        
        # Clear session data
        session.pop('import_data', None)
        session.pop('import_headers', None)
        session.pop('import_type', None)
        session.pop('field_mappings', None)
        session.pop('validated_data', None)
        session.pop('mapping', None)
        session.pop('validation_errors', None)
        
        # Redirect based on import type
        if import_type == 'warehouse':
            return redirect(url_for('warehouse.stock_in'))
        elif import_type == 'sales':
            return redirect(url_for('sales.index'))
        elif import_type == 'expenses':
            return redirect(url_for('expenses.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error during import: {str(e)}", "error")
        return redirect(url_for('import_data.process_mapping'))
    
    return redirect(url_for('dashboard.index'))
