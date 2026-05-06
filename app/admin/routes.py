from flask import render_template
from flask_login import login_required, current_user
from . import admin_bp


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome {current_user.username} — Dashboard coming soon!"