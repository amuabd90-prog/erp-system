from flask import Blueprint, current_app, flash, redirect, url_for
from flask_login import login_required
from auth import has_role


telegram_bp = Blueprint("telegram", __name__)


@telegram_bp.route("/send-daily", methods=["POST"])
@login_required
@has_role("Admin", "Accountant")
def send_daily():
    if not current_app.config.get("TELEGRAM_ENABLED"):
        flash("Telegram is disabled in local config.", "warning")
        return redirect(url_for("dashboard.index"))
    flash("Telegram sending integration enabled but requires local scheduler setup.", "info")
    return redirect(url_for("dashboard.index"))
