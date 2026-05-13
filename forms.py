from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")


class StockInForm(FlaskForm):
    inventory_no = StringField("Inventory No", validators=[DataRequired(), Length(max=64)])
    item = StringField("Item", validators=[DataRequired(), Length(max=120)])
    brand = StringField("Brand", validators=[DataRequired(), Length(max=120)])
    color = StringField("Color", validators=[Optional(), Length(max=50)])
    description = TextAreaField("Description", validators=[Optional()])
    size = StringField("Size", validators=[Optional(), Length(max=50)])
    pieces = IntegerField("Pieces", validators=[DataRequired(), NumberRange(min=1)])
    price = FloatField("Price", validators=[DataRequired(), NumberRange(min=0)])
    delivered_by = StringField("Delivered By", validators=[Optional(), Length(max=120)])
    received_by = StringField("Received By", validators=[Optional(), Length(max=120)])
    date_added = DateField("Date Added", format="%Y-%m-%d", validators=[DataRequired()])
    submit = SubmitField("Save")


class StockOutForm(FlaskForm):
    date = DateField("Date", format="%Y-%m-%d", validators=[DataRequired()])
    inventory_no = StringField("Inventory No", validators=[DataRequired(), Length(max=64)])
    delivered_by = StringField("Delivered By", validators=[Optional(), Length(max=120)])
    received_by = StringField("Received By", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Stock Out")


class SalesForm(FlaskForm):
    product_id = StringField("Product ID", validators=[DataRequired(), Length(max=64)])
    date = DateField("Date", format="%Y-%m-%d", validators=[DataRequired()])
    item_type = StringField("Item Type", validators=[DataRequired(), Length(max=120)])
    brand = StringField("Brand", validators=[DataRequired(), Length(max=120)])
    color = StringField("Color", validators=[Optional(), Length(max=50)])
    size = StringField("Size", validators=[Optional(), Length(max=50)])
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)])
    price = FloatField("Price", validators=[DataRequired(), NumberRange(min=0)])
    bank_invoice_no = StringField("Bank Invoice No", validators=[Optional(), Length(max=120)])
    invoice_image = StringField("Invoice Image", validators=[Optional(), Length(max=255)])
    sales_rep = StringField("Sales Rep", validators=[Optional(), Length(max=120)])
    deduction = FloatField("Deduction", validators=[Optional(), NumberRange(min=0)])
    description = TextAreaField("Description", validators=[Optional()])
    status = SelectField("Status", choices=[("Yes", "1 = Yes"), ("No", "2 = No")], validators=[DataRequired()])
    ha_receipt_number = StringField("H/A Receipt Number", validators=[Optional(), Length(max=120)])
    deposited_account_number = StringField(
        "Deposited Account Number", validators=[Optional(), Length(max=64)]
    )
    submit = SubmitField("Save")


class ExpenseForm(FlaskForm):
    date = DateField("Date", format="%Y-%m-%d", validators=[DataRequired()])
    amount = FloatField("Amount", validators=[DataRequired(), NumberRange(min=0)])
    reason = StringField("Reason", validators=[DataRequired(), Length(max=255)])
    reference_no = StringField("Reference No", validators=[Optional(), Length(max=120)])
    payed_by = StringField("Payed By", validators=[Optional(), Length(max=120)])
    account_number = StringField("Account Number", validators=[Optional(), Length(max=64)])
    status = SelectField("Status", choices=[("1", "1 = Yes"), ("2", "2 = No")], validators=[DataRequired()])
    submit = SubmitField("Save")


class ReconciliationForm(FlaskForm):
    date = DateField("Date", format="%Y-%m-%d", validators=[DataRequired()])
    item = StringField("Item", validators=[DataRequired(), Length(max=120)])
    physical_count = IntegerField("Physical Count", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Save")


class CostOfGoodsForm(FlaskForm):
    date = DateField("Date", format="%Y-%m-%d", validators=[DataRequired()])
    item = StringField("Item", validators=[DataRequired(), Length(max=120)])
    brand = StringField("Brand", validators=[DataRequired(), Length(max=120)])
    purchasing_cost = FloatField("Purchasing Cost", validators=[DataRequired(), NumberRange(min=0)])
    purchasing_cost_under_value = FloatField(
        "Purchasing Cost Under Value", validators=[DataRequired(), NumberRange(min=0)]
    )
    shipping_cost = FloatField("Shipping Cost", validators=[DataRequired(), NumberRange(min=0)])
    tariff = FloatField("Tariff", validators=[DataRequired(), NumberRange(min=0)])
    transportation_cost = FloatField("Transportation Cost", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Save")


class UserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Password", validators=[Optional(), Length(min=8)])
    role = SelectField(
        "Role",
        choices=[
            ("Admin", "Admin"),
            ("Store Keeper", "Store Keeper"),
            ("Sales Person", "Sales Person"),
            ("Accountant", "Accountant"),
            ("Auditor", "Auditor"),
            ("Viewer", "Viewer"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save")
