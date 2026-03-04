import os

from flask import Flask
from sqlalchemy import event
from app.models import db, migrate, Base


def _set_sqlite_pragmas(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=FULL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        db_path = os.environ.get('DATABASE_PATH', 'instance/app.db')
        # Ensure the directory exists
        db_dir = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(db_dir, exist_ok=True)
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-imports-sec'),
            SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.abspath(db_path)}',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
    else:
        app.config.from_mapping(test_config)
        if 'SECRET_KEY' not in test_config:
            app.config['SECRET_KEY'] = 'test-secret'

    db.init_app(app)
    migrate.init_app(app, db)

    # Apply SQLite PRAGMAs on every new connection
    with app.app_context():
        event.listen(db.engine, "connect", _set_sqlite_pragmas)

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
