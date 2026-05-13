from datetime import date
from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required
from auth import has_role, log_action
from forms import ReconciliationForm
from models import Reconciliation, db
from utils import reconciliation_seed, safe_commit


reconciliation_bp = Blueprint("reconciliation", __name__)


@reconciliation_bp.route("/")
@login_required
@has_role("Auditor", "Admin", "Viewer")
def index():
    seed = reconciliation_seed()
    return render_template(
        "reports/reconciliation.html",
        rows=Reconciliation.query.order_by(Reconciliation.date.desc()).all(),
        seed=seed,
        form=ReconciliationForm(date=date.today()),
    )


@reconciliation_bp.route("/create", methods=["POST"])
@login_required
@has_role("Auditor", "Admin")
def create_row():
    form = ReconciliationForm()
    if form.validate_on_submit():
        seed = reconciliation_seed().get(form.item.data, {"store": 0, "inventory": 0})
        total_system = seed["store"] + seed["inventory"]
        row = Reconciliation(
            date=form.date.data,
            item=form.item.data,
            store_count=seed["store"],
            inventory_count=seed["inventory"],
            total_system=total_system,
            physical_count=form.physical_count.data,
            difference=form.physical_count.data - total_system,
        )
        db.session.add(row)
        safe_commit("Reconciliation row saved.")
        log_action("CREATE", "RECONCILIATION", str(row.id), "Reconciliation recorded")
    return redirect(url_for("reconciliation.index"))
