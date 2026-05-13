from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user
from models import db, User, Company
from auth import log_action
from werkzeug.security import generate_password_hash
import os

setup_bp = Blueprint("setup", __name__)


@setup_bp.route("/")
def index():
    """Check if setup is needed and show setup wizard"""
    # Check if database exists and has companies
    db_path = os.path.join(os.getcwd(), "instance", "ha_business.db")
    
    # If database exists and has companies, redirect to login
    if os.path.exists(db_path):
        try:
            company_count = Company.query.count()
            user_count = User.query.count()
            if company_count > 0 and user_count > 0:
                flash("🏢 Amana ERP is already set up! Please sign in.", "info")
                return redirect(url_for("auth.login"))
        except:
            pass  # Database might be corrupted, continue with setup
    
    return render_template("setup/index.html")


@setup_bp.route("/step1", methods=["GET", "POST"])
def step1():
    """Step 1: Create Company"""
    if request.method == "POST":
        try:
            company_name = request.form.get("company_name", "").strip()
            tax_registration_number = request.form.get("tax_registration_number", "").strip()
            address = request.form.get("address", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            
            # Validate required fields
            if not company_name:
                flash("Company name is required.", "error")
                return render_template("setup/step1.html")
            
            # Check if company already exists
            existing_company = Company.query.filter_by(company_name=company_name).first()
            if existing_company:
                flash("A company with this name already exists. Please use a different name.", "error")
                return render_template("setup/step1.html")
            
            # Create company
            company = Company(
                company_name=company_name,
                tax_registration_number=tax_registration_number,
                address=address,
                phone=phone,
                email=email,
                is_active=True
            )
            
            db.session.add(company)
            db.session.commit()
            
            flash("Company created successfully!", "success")
            return redirect(url_for("setup.step2"))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating company: {str(e)}", "error")
    
    return render_template("setup/step1.html")


@setup_bp.route("/step2", methods=["GET", "POST"])
def step2():
    """Step 2: Create Admin Account"""
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            
            # Validate required fields
            if not username or not email or not password:
                flash("All fields are required.", "error")
                return render_template("setup/step2.html")
            
            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template("setup/step2.html")
            
            if len(password) < 6:
                flash("Password must be at least 6 characters long.", "error")
                return render_template("setup/step2.html")
            
            # Check if username already exists
            if User.query.filter_by(username=username).first():
                flash("Username already exists. Please choose a different username.", "error")
                return render_template("setup/step2.html")
            
            # Get the first company (created in step 1)
            company = Company.query.first()
            if not company:
                flash("No company found. Please create a company first.", "error")
                return redirect(url_for("setup.step1"))
            
            # Create admin user and associate with company
            admin_user = User(
                username=username,
                full_name=username.title(),  # Use username as full name for now
                role="Admin",
                is_active_user=True,
                company_id=company.id
            )
            admin_user.set_password(password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            flash("🎉 Setup completed successfully! Please sign in with your new account.", "success")
            return redirect(url_for("auth.login"))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating admin account: {str(e)}", "error")
    
    return render_template("setup/step2.html")


@setup_bp.route("/complete")
def complete():
    """Setup complete - redirect to login"""
    flash("🎉 Setup completed successfully! Your Amana ERP is ready to use.", "success")
    log_action("CREATE", "SYSTEM", "", "Initial setup completed")
    return redirect(url_for("auth.login"))
