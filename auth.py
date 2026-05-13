from functools import wraps
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from models import User, db, AuditLog
from forms import LoginForm


auth_bp = Blueprint("auth", __name__)


ROLES = ["Admin", "Store Keeper", "Sales Person", "Accountant", "Auditor", "Viewer"]


def has_role(*allowed_roles):
    """
    Enhanced role-based access decorator
    Admin can access everything
    Other roles can only access their allowed modules
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            # Admin can access everything
            if current_user.role == "Admin":
                return f(*args, **kwargs)
            
            # Check if user's role is in allowed roles
            if current_user.role in allowed_roles:
                return f(*args, **kwargs)
            
            # If not allowed, return 403 Forbidden
            abort(403)

        return wrapper

    return decorator


def require_any_role(*allowed_roles):
    """
    Allow access if user has ANY of the specified roles
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            # Admin can access everything
            if current_user.role == "Admin":
                return f(*args, **kwargs)
            
            # Check if user's role is in allowed roles
            if current_user.role in allowed_roles:
                return f(*args, **kwargs)
            
            # If not allowed, return 403 Forbidden
            abort(403)

        return wrapper

    return decorator


def log_action(action: str, module: str, target_id: str = "", details: str = "") -> None:
    entry = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        username=current_user.username if current_user.is_authenticated else "system",
        action=action,
        module=module,
        target_id=target_id,
        details=details,
    )
    db.session.add(entry)
    db.session.commit()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    
    # Check if setup is needed
    from models import Company
    import os
    db_path = os.path.join(os.getcwd(), "instance", "ha_business.db")
    
    # If database doesn't exist or has no companies, redirect to setup
    if not os.path.exists(db_path) or Company.query.count() == 0:
        return redirect(url_for("setup.index"))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data) and user.is_active_user:
            login_user(user, remember=form.remember.data)
            log_action("LOGIN", "AUTH", str(user.id), "User logged in")
            flash("Login successful.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard.index"))
        flash("Invalid credentials or inactive user.", "danger")
    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_action("LOGOUT", "AUTH", str(current_user.id), "User logged out")
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "error")
            return render_template("change_password.html")
        
        # Validate new password
        if not new_password:
            flash("New password is required.", "error")
            return render_template("change_password.html")
        
        if len(new_password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("change_password.html")
        
        if not any(c.isalpha() for c in new_password):
            flash("Password must contain at least 1 letter.", "error")
            return render_template("change_password.html")
        
        if not any(c.isdigit() for c in new_password):
            flash("Password must contain at least 1 number.", "error")
            return render_template("change_password.html")
        
        if new_password == current_password:
            flash("New password must be different from current password.", "error")
            return render_template("change_password.html")
        
        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("change_password.html")
        
        # Change password
        current_user.set_password(new_password)
        db.session.commit()
        log_action("UPDATE", "AUTH", str(current_user.id), "User changed password")
        flash("Password changed successfully.", "success")
        return redirect(url_for("dashboard.index"))
    
    return render_template("change_password.html")
