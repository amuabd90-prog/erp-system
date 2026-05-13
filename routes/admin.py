from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from flask_login import login_required, current_user
from auth import has_role, log_action
from forms import UserForm
from models import AuditLog, User, db
from utils import safe_commit


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
@has_role("Admin")
def index():
    return render_template(
        "admin/index.html",
        users=User.query.order_by(User.created_at.desc()).all(),
        logs=AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(300).all(),
        form=UserForm(),
    )


@admin_bp.route("/users/create", methods=["POST"])
@login_required
@has_role("Admin")
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists.", "warning")
            return redirect(url_for("admin.index"))
        
        password = form.password.data.strip()
        if not password:
            flash("Password is required.", "error")
            return redirect(url_for("admin.index"))
        
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for("admin.index"))
        
        if not any(c.isalpha() for c in password):
            flash("Password must contain at least 1 letter.", "error")
            return redirect(url_for("admin.index"))
        
        if not any(c.isdigit() for c in password):
            flash("Password must contain at least 1 number.", "error")
            return redirect(url_for("admin.index"))
        
        user = User(
            username=form.username.data,
            full_name=form.full_name.data,
            role=form.role.data,
            is_active_user=True,
        )
        user.set_password(password)
        db.session.add(user)
        safe_commit("User created.")
        log_action("CREATE", "ADMIN", str(user.id), f"Created user {user.username}")
        flash(f"User {user.username} created successfully.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@has_role("Admin")
def toggle_user(user_id: int):
    user = User.query.get_or_404(user_id)
    user.is_active_user = not user.is_active_user
    safe_commit("User status changed.")
    log_action("UPDATE", "ADMIN", str(user_id), f"Toggled user {user.username}")
    return redirect(url_for("admin.index"))


@admin_bp.route("/users/<int:user_id>/change-username", methods=["POST"])
@login_required
@has_role("Admin")
def change_username(user_id: int):
    user = User.query.get_or_404(user_id)
    new_username = request.form.get("new_username", "").strip()
    
    if not new_username:
        flash("New username is required.", "error")
        return redirect(url_for("admin.index"))
    
    if User.query.filter_by(username=new_username).first():
        flash("Username already exists.", "error")
        return redirect(url_for("admin.index"))
    
    old_username = user.username
    user.username = new_username
    safe_commit("Username changed.")
    log_action("UPDATE", "ADMIN", str(user_id), f"Changed username from {old_username} to {new_username}")
    flash(f"Username changed from {old_username} to {new_username}.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@has_role("Admin")
def reset_user_password(user_id: int):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get("new_password", "").strip()
    
    if not new_password:
        flash("New password is required.", "error")
        return redirect(url_for("admin.index"))
    
    if len(new_password) < 8:
        flash("Password must be at least 8 characters long.", "error")
        return redirect(url_for("admin.index"))
    
    if not any(c.isalpha() for c in new_password):
        flash("Password must contain at least 1 letter.", "error")
        return redirect(url_for("admin.index"))
    
    if not any(c.isdigit() for c in new_password):
        flash("Password must contain at least 1 number.", "error")
        return redirect(url_for("admin.index"))
    
    user.set_password(new_password)
    safe_commit("Password reset.")
    log_action("UPDATE", "ADMIN", str(user_id), f"Reset password for {user.username}")
    flash(f"Password reset for {user.username}.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/companies")
@login_required
@has_role("Admin")
def companies():
    from models import Company
    # FIXED: Show ALL companies, not just active ones
    companies = Company.query.order_by(Company.created_at.desc()).all()
    return render_template("admin/company.html", 
                         companies=companies, 
                         current_company=current_user.company if current_user.company else None)


@admin_bp.route("/company-data/<int:company_id>")
@login_required
@has_role("Admin")
def company_data(company_id):
    from models import Company
    company = Company.query.get_or_404(company_id)
    return jsonify({
        'id': company.id,
        'company_name': company.company_name,
        'tax_registration_number': company.tax_registration_number,
        'address': company.address,
        'phone': company.phone,
        'email': company.email,
        'is_active': company.is_active
    })


@admin_bp.route("/create-company", methods=["POST"])
@login_required
@has_role("Admin")
def create_company():
    from models import Company
    import os
    
    company_name = request.form.get("company_name")
    tax_registration_number = request.form.get("tax_registration_number")
    address = request.form.get("address")
    phone = request.form.get("phone")
    email = request.form.get("email")
    # FIXED: Default to True if checkbox not checked
    is_active = True
    
    if not company_name:
        flash("Company name is required.", "error")
        return redirect(url_for("admin.companies"))
    
    logo_path = None
    if "logo" in request.files:
        logo = request.files["logo"]
        if logo and logo.filename:
            upload_dir = os.path.join(os.getcwd(), "static", "uploads", "logos")
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"company_{company_name}_{logo.filename}"
            logo_path = os.path.join("static", "uploads", "logos", filename)
            logo.save(logo_path)
            logo_path = f"uploads/logos/{filename}"
    
    try:
        company = Company(
            company_name=company_name,
            tax_registration_number=tax_registration_number,
            address=address,
            phone=phone,
            email=email,
            logo_path=logo_path,
            is_active=is_active
        )
        db.session.add(company)
        db.session.commit()
        
        if not current_user.company_id:
            current_user.company_id = company.id
            db.session.commit()
        
        flash("Company created successfully!", "success")
        log_action("CREATE", "ADMIN", str(company.id), f"Created company: {company_name}")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating company: {str(e)}", "error")
    
    return redirect(url_for("admin.companies"))


@admin_bp.route("/update-company/<int:company_id>", methods=["POST"])
@login_required
@has_role("Admin")
def update_company(company_id):
    from models import Company
    import os
    
    company = Company.query.get_or_404(company_id)
    
    company_name = request.form.get("company_name")
    tax_registration_number = request.form.get("tax_registration_number")
    address = request.form.get("address")
    phone = request.form.get("phone")
    email = request.form.get("email")
    is_active = request.form.get("is_active") == "on"
    
    if "logo" in request.files:
        logo = request.files["logo"]
        if logo and logo.filename:
            upload_dir = os.path.join(os.getcwd(), "static", "uploads", "logos")
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"company_{company_name}_{logo.filename}"
            logo_path = os.path.join("static", "uploads", "logos", filename)
            logo.save(logo_path)
            company.logo_path = f"uploads/logos/{filename}"
    
    try:
        company.company_name = company_name
        company.tax_registration_number = tax_registration_number
        company.address = address
        company.phone = phone
        company.email = email
        company.is_active = is_active
        
        db.session.commit()
        flash("Company updated successfully!", "success")
        log_action("UPDATE", "ADMIN", str(company_id), f"Updated company: {company_name}")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating company: {str(e)}", "error")
    
    return redirect(url_for("admin.companies"))


@admin_bp.route("/delete-company/<int:company_id>", methods=["POST"])
@login_required
@has_role("Admin")
def delete_company(company_id):
    from models import Company
    
    company = Company.query.get_or_404(company_id)
    
    if current_user.company_id == company_id:
        flash("Cannot delete your currently active company!", "error")
        return redirect(url_for("admin.companies"))
    
    try:
        db.session.delete(company)
        db.session.commit()
        flash("Company deleted successfully!", "success")
        log_action("DELETE", "ADMIN", str(company_id), f"Deleted company: {company.company_name}")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting company: {str(e)}", "error")
    
    return redirect(url_for("admin.companies"))


@admin_bp.route("/switch-company/<int:company_id>", methods=["POST"])
@login_required
@has_role("Admin")
def switch_company(company_id):
    from models import Company
    
    company = Company.query.get_or_404(company_id)
    
    try:
        current_user.company_id = company.id
        db.session.commit()
        flash(f"Switched to company: {company.company_name}", "success")
        log_action("UPDATE", "ADMIN", str(company_id), f"Switched to company: {company.company_name}")
    except Exception as e:
        db.session.rollback()
        flash(f"Error switching company: {str(e)}", "error")
    
    return redirect(url_for("dashboard.index"))