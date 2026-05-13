from datetime import datetime, date
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


NON_RECEIPT_ACCOUNTS = {
    "1000084206087",
    "57861258",
    "1014657935101",
    "08804884936001",
    "0001883620101",
    "1000564090001",
    "5038523396011",
    "01320927866200",
    "01320927862269",
    "0911190064",
}


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Company(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    tax_registration_number = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    logo_path = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    
    def __repr__(self):
        return f'<Company {self.company_name}>'


class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, index=True)
    is_active_user = db.Column(db.Boolean, default=True, nullable=False)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    username = db.Column(db.String(80), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    module = db.Column(db.String(80), nullable=False)
    target_id = db.Column(db.String(80), nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class StockIn(TimestampMixin, db.Model):
    inventory_no = db.Column(db.String(64), primary_key=True)
    item = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    size = db.Column(db.String(50), nullable=True)
    pieces = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)
    delivered_by = db.Column(db.String(120), nullable=True)
    received_by = db.Column(db.String(120), nullable=True)
    date_added = db.Column(db.Date, default=date.today, nullable=False)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class Stock(TimestampMixin, db.Model):
    inventory_no = db.Column(db.String(64), primary_key=True)
    item = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    size = db.Column(db.String(50), nullable=True)
    pieces = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)
    received_by = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(5), default="No", nullable=False, index=True)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)
    date_added = db.Column(db.Date, default=date.today, nullable=False)


class StockOut(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    inventory_no = db.Column(db.String(64), db.ForeignKey("stock.inventory_no"), nullable=False)
    item = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    size = db.Column(db.String(50), nullable=True)
    pieces = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)
    delivered_by = db.Column(db.String(120), nullable=True)
    received_by = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(5), default="Yes", nullable=False)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)
    __table_args__ = (UniqueConstraint("inventory_no", name="uq_stockout_inventory_no"),)


class InventoryIn(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inv_no = db.Column(db.String(64), unique=True, nullable=False)
    item = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    size = db.Column(db.String(50), nullable=True)
    pieces = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)
    received_by = db.Column(db.String(120), nullable=True)
    date = db.Column(db.Date, default=date.today, nullable=False)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class Inventory(TimestampMixin, db.Model):
    inv_no = db.Column(db.String(64), primary_key=True)
    item = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    size = db.Column(db.String(50), nullable=True)
    pieces = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)
    received_by = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(5), default="No", nullable=False)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class AfterSale(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, nullable=False)
    inv_no = db.Column(db.String(64), nullable=False)
    item = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    size = db.Column(db.String(50), nullable=True)
    pieces = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)
    sold_by = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(5), default="Yes", nullable=False)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class Sales(TimestampMixin, db.Model):
    product_id = db.Column(db.String(64), primary_key=True)
    date = db.Column(db.Date, default=date.today, nullable=False)
    item_type = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    bank_invoice_no = db.Column(db.String(120), nullable=True)
    invoice_image = db.Column(db.String(255), nullable=True)
    sales_rep = db.Column(db.String(120), nullable=True)
    deduction = db.Column(db.Float, default=0.0, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(10), default="No", nullable=False)
    ha_receipt_number = db.Column(db.String(120), nullable=True)
    deposited_account_number = db.Column(db.String(64), nullable=True)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)

    @property
    def total_amount(self) -> float:
        return max((self.price * self.quantity) - self.deduction, 0)


class WeeklyCommission(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_start = db.Column(db.Date, nullable=False, index=True)
    week_end = db.Column(db.Date, nullable=False, index=True)
    total_sales = db.Column(db.Float, nullable=False, default=0.0)
    suits_sold = db.Column(db.Integer, nullable=False, default=0)
    coats_sold = db.Column(db.Integer, nullable=False, default=0)
    sale_bonus_1pct = db.Column(db.Float, nullable=False, default=0.0)
    suit_bonus = db.Column(db.Float, nullable=False, default=0.0)
    coat_bonus = db.Column(db.Float, nullable=False, default=0.0)
    total_commission = db.Column(db.Float, nullable=False, default=0.0)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)
    __table_args__ = (UniqueConstraint("week_start", "week_end", name="uq_week_window"),)


class Expenses(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    reference_no = db.Column(db.String(120), nullable=True)
    invoice_image = db.Column(db.String(255), nullable=True)
    payed_by = db.Column(db.String(120), nullable=True)
    account_number = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(10), default="2", nullable=False)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class Reconciliation(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, nullable=False)
    item = db.Column(db.String(120), nullable=False)
    store_count = db.Column(db.Integer, nullable=False, default=0)
    inventory_count = db.Column(db.Integer, nullable=False, default=0)
    total_system = db.Column(db.Integer, nullable=False, default=0)
    physical_count = db.Column(db.Integer, nullable=False, default=0)
    difference = db.Column(db.Integer, nullable=False, default=0)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class CostOfGoods(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, nullable=False)
    item = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    purchasing_cost = db.Column(db.Float, default=0.0, nullable=False)
    purchasing_cost_under_value = db.Column(db.Float, default=0.0, nullable=False)
    shipping_cost = db.Column(db.Float, default=0.0, nullable=False)
    tariff = db.Column(db.Float, default=0.0, nullable=False)
    transportation_cost = db.Column(db.Float, default=0.0, nullable=False)
    total_cost_face_value = db.Column(db.Float, default=0.0, nullable=False)
    total_cost_under_value = db.Column(db.Float, default=0.0, nullable=False)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class SalesReport(TimestampMixin, db.Model):
    product_id = db.Column(db.String(64), primary_key=True)
    date = db.Column(db.Date, nullable=False)
    item = db.Column(db.String(120), nullable=False)
    total_sale = db.Column(db.Float, nullable=False)
    bank_receipt_number = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(10), nullable=False)
    ha_receipt_number = db.Column(db.String(120), nullable=True)
    deposited_account_number = db.Column(db.String(64), nullable=True)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class ExpenseReport(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    total_expenses = db.Column(db.Float, nullable=False)
    payment_receipt_number = db.Column(db.String(120), nullable=True)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class ProfitTaxReport(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    total_profit = db.Column(db.Float, nullable=False, default=0.0)
    vat_15 = db.Column(db.Float, nullable=False, default=0.0)
    profit_tax = db.Column(db.Float, nullable=False, default=0.0)
    total_tax_payable = db.Column(db.Float, nullable=False, default=0.0)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class BankReconSales(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    product_id = db.Column(db.String(64), nullable=False, unique=True)
    item = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    ha_receipt_number = db.Column(db.String(120), nullable=True)
    bank_invoice_no = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(10), nullable=False)
    deposited_account_number = db.Column(db.String(64), nullable=True)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)


class BankReconExpenses(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    reasons = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    bank_invoice_no = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(10), nullable=False)
    company_id = db.Column(db.Integer, ForeignKey('company.id'), nullable=False)
