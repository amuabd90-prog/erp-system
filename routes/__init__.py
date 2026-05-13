from .warehouse import warehouse_bp
from .sales import sales_bp
from .expenses import expenses_bp
from .reconciliation import reconciliation_bp
from .reports import reports_bp
from .bank_recon import bank_recon_bp
from .dashboard import dashboard_bp
from .telegram import telegram_bp
from .admin import admin_bp
from .admin_audit import admin_audit_bp
from .api_validation import api_validation_bp
from .setup import setup_bp


def register_blueprints(app):
    app.register_blueprint(setup_bp, url_prefix="/setup")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(warehouse_bp, url_prefix="/warehouse")
    app.register_blueprint(sales_bp, url_prefix="/sales")
    app.register_blueprint(expenses_bp, url_prefix="/expenses")
    app.register_blueprint(reconciliation_bp, url_prefix="/reconciliation")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(bank_recon_bp, url_prefix="/bank")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(admin_audit_bp, url_prefix="/admin/audit")
    app.register_blueprint(api_validation_bp, url_prefix="/api")
    app.register_blueprint(telegram_bp, url_prefix="/telegram")