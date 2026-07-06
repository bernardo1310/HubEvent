# utils/decorators.py
"""Decorators utilitários usados nas rotas Flask."""

from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    """Restringe o acesso de uma rota apenas a usuários administradores."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return f(*args, **kwargs)
    return decorated
