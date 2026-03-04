from functools import wraps

from flask import redirect, request, session, url_for


def needs_setup():
    """Check if the application needs initial admin setup."""
    from app.models import AdminUser
    return AdminUser.query.count() == 0


def check_credentials(username, password):
    """Validate credentials against database."""
    from app.models import AdminUser
    admin = AdminUser.query.filter_by(username=username).first()
    if not admin:
        return False
    return admin.check_password(password)


def login_required(f):
    """Decorator that redirects unauthenticated users to /login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if needs_setup():
            return redirect(url_for('web.setup'))
        if not session.get('authenticated'):
            return redirect(url_for('web.login', next=request.path))
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    """Decorator for API routes — returns 401 JSON instead of redirect."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            from flask import jsonify
            return jsonify({'error': 'Não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated
