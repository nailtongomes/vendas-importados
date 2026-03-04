import os
from functools import wraps

from flask import redirect, request, session, url_for


def check_credentials(username, password):
    """Validate credentials against environment variables."""
    admin_user = os.environ.get('ADMIN_USER', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    if not admin_password:
        return False
    return username == admin_user and password == admin_password


def login_required(f):
    """Decorator that redirects unauthenticated users to /login."""
    @wraps(f)
    def decorated(*args, **kwargs):
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
