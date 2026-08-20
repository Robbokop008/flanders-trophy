"""
routes/auth.py
---------------
Login en uitloggen voor admins. Er is bewust geen publieke zelfregistratie
op deze site (in tegenstelling tot de hoofdclubsite) - de eerste admin
maak je aan via scripts/create_admin.py.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from extensions import limiter
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if "user_id" in session:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        error = None
        if not username or not password:
            error = "Gebruikersnaam en wachtwoord zijn verplicht."
        else:
            user = User.query.filter_by(username=username).first()
            if user is None or not user.check_password(password):
                error = "Ongeldige gebruikersnaam of wachtwoord."

        if error:
            return render_template("login.html", error=error)

        session["user_id"] = user.user_id
        return redirect(url_for("main.home"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
