"""
routes/main.py
---------------
Routes voor het publieke, informatieve deel van de site: home en contact.
Bewust minimaal - dit is een scaffold, de echte homepage-inhoud (nieuws,
evenementen, ...) is club-specifiek en hoort hier niet thuis. Zie
templates/index.html voor de placeholder-hero.
"""

from flask import Blueprint, render_template, request, current_app, session, redirect, url_for
from flask_babel import gettext as _

from extensions import limiter
from utils.mail import send_contact_mail

main_bp = Blueprint("main", __name__)

CONTACT_TOPICS = ["General questions", "Registration / Offers", "Referees", "Parade", "During tournament"]


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/set-language/<lang_code>")
def set_language(lang_code):
    if lang_code in current_app.config["LANGUAGES"]:
        session["lang"] = lang_code

    next_url = request.args.get("next") or ""
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("main.home")
    return redirect(next_url)


@main_bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        topic = request.form.get("topic")
        topic = topic if topic in CONTACT_TOPICS else CONTACT_TOPICS[0]

        if not name or not email or not message or "@" not in email:
            return render_template(
                "contact.html", topics=CONTACT_TOPICS,
                error=_("Please fill in all fields correctly (with a valid email address)."),
                name=name, email=email, message=message, topic=topic,
            )

        try:
            send_contact_mail(name, email, message, topic=topic)
        except Exception as exc:
            # Mail-fout mag de gebruiker niet blokkeren, maar loggen we wel
            current_app.logger.error(f"Kon contactmail niet versturen: {exc}")

        return render_template("contact.html", topics=CONTACT_TOPICS, success=_("Your message has been sent successfully."))

    return render_template("contact.html", topics=CONTACT_TOPICS)
