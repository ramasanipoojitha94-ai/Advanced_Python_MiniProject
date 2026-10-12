import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    load_dotenv()
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        instance_relative_config=True,
    )
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", f"sqlite:///{Path(app.instance_path) / 'yatrago.sqlite'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Sign in to access your YatraGo account."
    login_manager.login_message_category = "info"
    csrf.init_app(app)

    from yatrago import models  # noqa: F401
    from yatrago.auth import auth
    from yatrago.bookings import bookings
    from yatrago.air_stays import travel
    from yatrago.routes import main
    from yatrago.transport import transport as transport_blueprint
    from yatrago.world import world as world_blueprint

    app.register_blueprint(auth)
    app.register_blueprint(bookings)
    app.register_blueprint(travel)
    app.register_blueprint(transport_blueprint)
    app.register_blueprint(world_blueprint)
    app.register_blueprint(main)

    @app.errorhandler(404)
    def not_found(_error):
        from flask import render_template

        return render_template("errors/404.html"), 404

    with app.app_context():
        db.create_all()
        from yatrago.migrations import migrate_reusable_bus_seats, migrate_add_user_avatar
        from yatrago.seed import seed_demo_data

        migrate_reusable_bus_seats()
        migrate_add_user_avatar()
        seed_demo_data()

    return app
