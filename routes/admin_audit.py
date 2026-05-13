from datetime import datetime, date
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from auth import has_role
from models import AuditLog, db
from export_utils import export_audit_log_csv


admin_audit_bp = Blueprint("admin_audit", __name__)


@admin_audit_bp.route("/audit-trail")
@login_required
@has_role("Admin")
def audit_trail():
    # Get filter parameters
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    user_filter = request.args.get("user")
    action_filter = request.args.get("action")
    module_filter = request.args.get("module")
    
    # Build query
    query = AuditLog.query
    
    # Apply filters
    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
            query = query.filter(AuditLog.timestamp >= datetime.combine(from_dt, datetime.min.time()))
        except ValueError:
            pass
    
    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
            query = query.filter(AuditLog.timestamp <= datetime.combine(to_dt, datetime.max.time()))
        except ValueError:
            pass
    
    if user_filter and user_filter.strip():
        query = query.filter(AuditLog.username.ilike(f"%{user_filter.strip()}%"))
    
    if action_filter and action_filter.strip():
        query = query.filter(AuditLog.action.ilike(f"%{action_filter.strip()}%"))
    
    if module_filter and module_filter.strip():
        query = query.filter(AuditLog.module.ilike(f"%{module_filter.strip()}%"))
    
    # Order by timestamp descending
    audit_logs = query.order_by(AuditLog.timestamp.desc()).limit(1000).all()
    
    return render_template(
        "admin/audit_trail.html",
        audit_logs=audit_logs,
        from_date=from_date,
        to_date=to_date,
        user_filter=user_filter,
        action_filter=action_filter,
        module_filter=module_filter
    )


@admin_audit_bp.route("/audit-trail/export")
@login_required
@has_role("Admin")
def export_audit_trail():
    # Get filter parameters
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    user_filter = request.args.get("user")
    action_filter = request.args.get("action")
    module_filter = request.args.get("module")
    
    # Build query
    query = AuditLog.query
    
    # Apply filters
    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
            query = query.filter(AuditLog.timestamp >= datetime.combine(from_dt, datetime.min.time()))
        except ValueError:
            pass
    
    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
            query = query.filter(AuditLog.timestamp <= datetime.combine(to_dt, datetime.max.time()))
        except ValueError:
            pass
    
    if user_filter and user_filter.strip():
        query = query.filter(AuditLog.username.ilike(f"%{user_filter.strip()}%"))
    
    if action_filter and action_filter.strip():
        query = query.filter(AuditLog.action.ilike(f"%{action_filter.strip()}%"))
    
    if module_filter and module_filter.strip():
        query = query.filter(AuditLog.module.ilike(f"%{module_filter.strip()}%"))
    
    # Get filtered data
    filtered_logs = query.order_by(AuditLog.timestamp.desc()).all()
    
    return export_audit_log_csv(filtered_logs)
