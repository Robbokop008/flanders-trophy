"""
routes/main.py
---------------
Routes voor het publieke, informatieve deel van de site: home en contact.
Bewust minimaal - dit is een scaffold, de echte homepage-inhoud (nieuws,
evenementen, ...) is club-specifiek en hoort hier niet thuis. Zie
templates/index.html voor de placeholder-hero.
"""

from flask import Blueprint, render_template, request, current_app

from extensions import limiter
from utils.mail import send_contact_mail

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message or "@" not in email:
            return render_template(
                "contact.html", error="Vul alle velden correct in (met een geldig e-mailadres).", name=name, email=email, message=message
            )

        try:
            send_contact_mail(name, email, message)
        except Exception as exc:
            # Mail-fout mag de gebruiker niet blokkeren, maar loggen we wel
            current_app.logger.error(f"Kon contactmail niet versturen: {exc}")

        return render_template("contact.html", success="Je bericht is succesvol verzonden.")

    return render_template("contact.html")
