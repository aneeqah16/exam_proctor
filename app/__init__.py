from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db           = SQLAlchemy()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from app.models import Admin
    return Admin.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view     = "auth.login"
    login_manager.login_message  = "Please login first."
    login_manager.login_message_category = "warning"

    # Register blueprints
    from app.auth.routes  import auth_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp,  url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Home route — redirects to login
    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    with app.app_context():
        from app.models import Admin
        db.create_all()

        if not Admin.query.first():
            admin = Admin(username="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created — username: admin | password: admin123")

    return app