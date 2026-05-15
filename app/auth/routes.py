from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required

from . import auth_bp
from app import db
from app.models import Admin


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):

            login_user(admin)

            flash("Login successful", "success")

            return redirect(url_for("admin.dashboard"))

        flash("Invalid username or password", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully", "info")

    return redirect(url_for("auth.login"))

    # Secret code for admin registration
# Change this to something only you know
ADMIN_SECRET_CODE = "ICSC@2026"


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username   = request.form.get("username", "").strip()
        password   = request.form.get("password", "")
        secret     = request.form.get("secret_code", "")

        if secret != ADMIN_SECRET_CODE:
            flash("Invalid registration code.", "danger")
            return redirect(url_for("auth.register"))

        if Admin.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.register"))

        admin = Admin(username=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        flash("Admin account created. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")