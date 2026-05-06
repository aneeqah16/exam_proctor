from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from app import db
from app.models import Admin


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        admin    = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            flash("Welcome back!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))