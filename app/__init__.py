from flask import Flask
from app.models import db, migrate, Base

def create_app(test_config=None):
    app = Flask(__name__)
    
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY='dev-imports-sec',
            SQLALCHEMY_DATABASE_URI='sqlite:///app.db',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
    else:
        app.config.from_mapping(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.api import bp as api_bp
    from app.routes.web import bp as web_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    with app.app_context():
        db.create_all()

    @app.cli.command("init-db")
    def init_db_command():
        """Clear the existing data and create new tables."""
        db.create_all()
        print('Initialized the database.')

    return app
