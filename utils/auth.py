"""
utils/auth.py
--------------
Decorators om routes te beschermen: @login_required voor ingelogde
gebruikers, @admin_required voor beheerders. Voorkomt dat elke route
zelf handmatig 'if "user_id" not in session' moet herhalen.
"""

from functools import wraps
from flask import session, redirect, url_for, g
from models import User


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        g.user = User.query.get(session["user_id"])
        if g.user is None:
            # gebruiker bestaat niet meer -> sessie opruimen
            session.clear()
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not g.user.is_admin:
            return redirect(url_for("main.home"))
        return view(*args, **kwargs)
    return wrapped
