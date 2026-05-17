from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from . import auth_bp
from app import db
from app.models import Admin

ADMIN_SECRET_CODE = "ICSC@2026"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin    = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            if not admin.is_approved:
                flash("Your account is pending super admin approval.", "warning")
                return redirect(url_for("auth.login"))
            login_user(admin)
            flash(f"Welcome back, {admin.username}!", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Invalid username or password", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        secret   = request.form.get("secret_code", "")

        if secret != ADMIN_SECRET_CODE:
            flash("Invalid registration code.", "danger")
            return redirect(url_for("auth.register"))

        if " " in username:
            flash("Username cannot contain spaces.", "danger")
            return redirect(url_for("auth.register"))

        if Admin.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.register"))

        # First ever admin becomes super admin, auto-approved
        is_first   = Admin.query.count() == 0
        admin      = Admin(username=username,
                           is_super=is_first,
                           is_approved=is_first)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        if is_first:
            flash("Super admin account created. You can login now.", "success")
        else:
            flash("Account created. Waiting for super admin approval.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ── Profile ───────────────────────────────────────────────────────────────────
@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        new_username = request.form.get("username", "").strip()
        new_password = request.form.get("new_password", "")
        confirm      = request.form.get("confirm_password", "")

    if new_username and new_username != current_user.username:
        if " " in new_username:
            flash("Username cannot contain spaces.", "danger")
            return redirect(url_for("auth.profile"))
        existing = Admin.query.filter_by(username=new_username).first()
        if existing:
            flash("Username already taken.", "danger")
            return redirect(url_for("auth.profile"))
        current_user.username = new_username

        if new_password:
            if new_password != confirm:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("auth.profile"))
            if len(new_password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return redirect(url_for("auth.profile"))
            current_user.set_password(new_password)

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html")


# ── Super admin — approvals ───────────────────────────────────────────────────
@auth_bp.route("/approvals")
@login_required
def approvals():
    if not current_user.is_super:
        flash("Access denied.", "danger")
        return redirect(url_for("admin.dashboard"))
    pending    = Admin.query.filter_by(is_approved=False).all()
    all_admins = Admin.query.filter_by(is_approved=True).all()
    return render_template("auth/approvals.html",
                           pending=pending, all_admins=all_admins)


@auth_bp.route("/approve/<int:admin_id>", methods=["POST"])
@login_required
def approve_admin(admin_id):
    if not current_user.is_super:
        flash("Access denied.", "danger")
        return redirect(url_for("admin.dashboard"))
    a = Admin.query.get_or_404(admin_id)
    a.is_approved = True
    db.session.commit()
    flash(f"{a.username} approved.", "success")
    return redirect(url_for("auth.approvals"))


@auth_bp.route("/reject/<int:admin_id>", methods=["POST"])
@login_required
def reject_admin(admin_id):
    if not current_user.is_super:
        flash("Access denied.", "danger")
        return redirect(url_for("admin.dashboard"))
    a = Admin.query.get_or_404(admin_id)
    db.session.delete(a)
    db.session.commit()
    flash("Account rejected and removed.", "info")
    return redirect(url_for("auth.approvals"))


@auth_bp.route("/deactivate/<int:admin_id>", methods=["POST"])
@login_required
def deactivate_admin(admin_id):
    if not current_user.is_super:
        flash("Access denied.", "danger")
        return redirect(url_for("admin.dashboard"))
    a = Admin.query.get_or_404(admin_id)
    if a.is_super:
        flash("Cannot deactivate super admin.", "danger")
        return redirect(url_for("auth.approvals"))
    a.is_approved = False
    db.session.commit()
    flash(f"{a.username} deactivated.", "info")
    return redirect(url_for("auth.approvals"))