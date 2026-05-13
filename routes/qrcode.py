import os
import json
import zipfile
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Stock
import requests
from datetime import datetime
import tempfile
from io import BytesIO
from PIL import Image
import io

qrcode_bp = Blueprint("qrcode", __name__)

# QR Code API endpoints
QR_APIS = {
    'primary': 'https://quickchart.io/qr',
    'fallback': 'https://api.qrserver.com/v1/create-qr-code/'
}

def generate_qr_code_url(data, size=250, label=None):
    """Generate QR code URL using primary or fallback API"""
    try:
        # Try primary API (quickchart.io)
        params = {
            'text': data,
            'size': f'{size}x{size}',
            'format': 'png',
            'margin': 0
        }
        
        if label:
            params['label'] = label
            params['label-font-size'] = 32
        
        response = requests.get(QR_APIS['primary'], params=params, timeout=10)
        if response.status_code == 200:
            return response.content, True
    except:
        pass
    
    try:
        # Fallback API (qrserver.com)
        params = {
            'size': f'{size}x{size}',
            'data': data,
            'format': 'png'
        }
        
        response = requests.get(QR_APIS['fallback'], params=params, timeout=10)
        if response.status_code == 200:
            return response.content, True
    except:
        pass
    
    return None, False

def get_qr_filename(stock_id, item_name):
    """Generate QR code filename"""
    safe_name = "".join(c for c in item_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"QR_{stock_id}_{safe_name}.png"

def get_qr_data(stock):
    """Generate QR code data for stock item"""
    data_parts = [
        f"INV:{stock.id}",
        f"Item:{stock.item}",
        f"Brand:{stock.brand}",
        f"Color:{stock.color}",
        f"Size:{stock.size}"
    ]
    
    # Only include non-empty fields
    data_parts = [part for part in data_parts if ':' in part and part.split(':', 1)[1].strip()]
    
    return ' | '.join(data_parts)

def ensure_qr_directory():
    """Ensure QR codes directory exists"""
    qr_dir = os.path.join('static', 'qrcodes')
    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)
    return qr_dir

@qrcode_bp.route("/generate/<int:stock_id>", methods=["POST"])
@login_required
def generate_single_qr(stock_id):
    """Generate QR code for a single stock item"""
    try:
        stock = Stock.query.get_or_404(stock_id)
        
        # Check if user has access to this stock
        if stock.company_id != current_user.company_id:
            flash("Access denied", "error")
            return redirect(url_for('warehouse.stock_list'))
        
        # Generate QR code data
        qr_data = get_qr_data(stock)
        label = f"ID: {stock.id}"
        
        # Generate QR code
        qr_image, success = generate_qr_code_url(qr_data, size=250, label=label)
        
        if not success:
            flash("Failed to generate QR code", "error")
            return redirect(url_for('warehouse.stock_list'))
        
        # Save QR code
        qr_dir = ensure_qr_directory()
        filename = get_qr_filename(stock.id, stock.item)
        filepath = os.path.join(qr_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(qr_image)
        
        flash(f"QR code generated for {stock.item}", "success")
        return redirect(url_for('warehouse.stock_list'))
        
    except Exception as e:
        flash(f"Error generating QR code: {str(e)}", "error")
        return redirect(url_for('warehouse.stock_list'))

@qrcode_bp.route("/generate_all", methods=["POST"])
@login_required
def generate_all_qr_codes():
    """Generate QR codes for all stock items"""
    try:
        # Get all stock items for current user's company
        stocks = Stock.query.filter_by(company_id=current_user.company_id).all()
        
        if not stocks:
            flash("No stock items found", "info")
            return redirect(url_for('warehouse.stock_list'))
        
        qr_dir = ensure_qr_directory()
        generated_count = 0
        skipped_count = 0
        
        for stock in stocks:
            try:
                # Check if QR code already exists
                filename = get_qr_filename(stock.id, stock.item)
                filepath = os.path.join(qr_dir, filename)
                
                if os.path.exists(filepath):
                    skipped_count += 1
                    continue
                
                # Generate QR code data
                qr_data = get_qr_data(stock)
                label = f"ID: {stock.id}"
                
                # Generate QR code
                qr_image, success = generate_qr_code_url(qr_data, size=250, label=label)
                
                if not success:
                    skipped_count += 1
                    continue
                
                # Save QR code
                with open(filepath, 'wb') as f:
                    f.write(qr_image)
                
                generated_count += 1
                
            except Exception as e:
                skipped_count += 1
                continue
        
        flash(f"Generated {generated_count} QR codes, skipped {skipped_count} (already exist or errors)", "success")
        return redirect(url_for('warehouse.stock_list'))
        
    except Exception as e:
        flash(f"Error generating QR codes: {str(e)}", "error")
        return redirect(url_for('warehouse.stock_list'))

@qrcode_bp.route("/export", methods=["POST"])
@login_required
def export_qr_codes():
    """Export all QR codes as ZIP file"""
    try:
        # Get all stock items for current user's company
        stocks = Stock.query.filter_by(company_id=current_user.company_id).all()
        
        if not stocks:
            flash("No stock items found", "info")
            return redirect(url_for('warehouse.stock_list'))
        
        qr_dir = ensure_qr_directory()
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            added_count = 0
            
            for stock in stocks:
                try:
                    filename = get_qr_filename(stock.id, stock.item)
                    filepath = os.path.join(qr_dir, filename)
                    
                    if os.path.exists(filepath):
                        zip_file.write(filepath, filename)
                        added_count += 1
                
                except Exception as e:
                    continue
        
        if added_count == 0:
            flash("No QR codes found to export", "warning")
            return redirect(url_for('warehouse.stock_list'))
        
        zip_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"QR_Codes_{current_user.company.company_name}_{timestamp}.zip"
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        flash(f"Error exporting QR codes: {str(e)}", "error")
        return redirect(url_for('warehouse.stock_list'))

@qrcode_bp.route("/preview/<int:stock_id>")
@login_required
def preview_qr_code(stock_id):
    """Preview QR code for a stock item"""
    try:
        stock = Stock.query.get_or_404(stock_id)
        
        # Check if user has access to this stock
        if stock.company_id != current_user.company_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if QR code already exists
        qr_dir = ensure_qr_directory()
        filename = get_qr_filename(stock.id, stock.item)
        filepath = os.path.join(qr_dir, filename)
        
        if os.path.exists(filepath):
            # Return existing QR code
            return send_file(filepath, mimetype='image/png')
        
        # Generate QR code data
        qr_data = get_qr_data(stock)
        label = f"ID: {stock.id}"
        
        # Generate QR code (smaller size for preview)
        qr_image, success = generate_qr_code_url(qr_data, size=100, label=label)
        
        if not success:
            return jsonify({'error': 'Failed to generate QR code'}), 500
        
        # Return generated QR code
        return send_file(
            BytesIO(qr_image),
            mimetype='image/png',
            download_name=f"preview_{stock.id}.png"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qrcode_bp.route("/progress")
@login_required
def qr_generation_progress():
    """Get QR code generation progress (for AJAX updates)"""
    try:
        stocks = Stock.query.filter_by(company_id=current_user.company_id).all()
        qr_dir = ensure_qr_directory()
        
        total_count = len(stocks)
        existing_count = 0
        
        for stock in stocks:
            filename = get_qr_filename(stock.id, stock.item)
            filepath = os.path.join(qr_dir, filename)
            if os.path.exists(filepath):
                existing_count += 1
        
        return jsonify({
            'total': total_count,
            'existing': existing_count,
            'remaining': total_count - existing_count,
            'progress': (existing_count / total_count * 100) if total_count > 0 else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qrcode_bp.route("/delete/<int:stock_id>", methods=["POST"])
@login_required
def delete_qr_code(stock_id):
    """Delete QR code for a stock item"""
    try:
        stock = Stock.query.get_or_404(stock_id)
        
        # Check if user has access to this stock
        if stock.company_id != current_user.company_id:
            flash("Access denied", "error")
            return redirect(url_for('warehouse.stock_list'))
        
        # Delete QR code file
        qr_dir = ensure_qr_directory()
        filename = get_qr_filename(stock.id, stock.item)
        filepath = os.path.join(qr_dir, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f"QR code deleted for {stock.item}", "success")
        else:
            flash("QR code not found", "warning")
        
        return redirect(url_for('warehouse.stock_list'))
        
    except Exception as e:
        flash(f"Error deleting QR code: {str(e)}", "error")
        return redirect(url_for('warehouse.stock_list'))

@qrcode_bp.route("/status")
@login_required
def qr_status():
    """Get QR code generation status for all stock items"""
    try:
        stocks = Stock.query.filter_by(company_id=current_user.company_id).all()
        qr_dir = ensure_qr_directory()
        
        status_list = []
        
        for stock in stocks:
            filename = get_qr_filename(stock.id, stock.item)
            filepath = os.path.join(qr_dir, filename)
            
            status_list.append({
                'id': stock.id,
                'item': stock.item,
                'has_qr': os.path.exists(filepath),
                'filename': filename
            })
        
        return jsonify({'status': status_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
