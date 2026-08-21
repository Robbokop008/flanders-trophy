"""
routes/offers.py
------------------
De publieke "Request Your Offer"-pagina: het startpunt van de customer
journey voor een buitenlandse club (ontdekken -> offerte aanvragen ->
inschrijven -> ...). Bewust een aparte route/model (OfferRequest) i.p.v.
een CMS-pagina: dit is een gestructureerd formulier, geen vrije inhoud.

Na een geldige aanvraag: een OfferRequest-rij opslaan, een notificatiemail
naar de organisatie sturen (zie utils/mail.send_offer_request_mail) en een
bevestiging tonen op het scherm - er gaat bewust geen automatische
bevestigingsmail naar de club zelf (zie module-docstring van send_offer_request_mail).
"""

from datetime import datetime

from flask import Blueprint, render_template, request, current_app
from flask_babel import gettext as _

from extensions import db, limiter
from models import OfferRequest, TRANSPORT_CHOICES
from utils.mail import send_offer_request_mail

offers_bp = Blueprint("offers", __name__)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_int(value):
    try:
        getal = int(value)
    except (TypeError, ValueError):
        return 0
    return getal if getal > 0 else 0


def _form_values():
    """Leest alle formuliervelden uit request.form, met veilige defaults -
    los bruikbaar zodat we bij een validatiefout dezelfde waarden kunnen
    teruggeven aan het formulier (i.p.v. de gebruiker alles te laten
    herbeginnen)."""
    values = {
        "club_name": (request.form.get("club_name") or "").strip(),
        "country": (request.form.get("country") or "").strip(),
        "contact_person": (request.form.get("contact_person") or "").strip(),
        "email": (request.form.get("email") or "").strip(),
        "phone": (request.form.get("phone") or "").strip(),
        "expected_participants_raw": (request.form.get("expected_participants") or "").strip(),
        "preferred_package": (request.form.get("preferred_package") or "").strip(),
        "arrival_raw": (request.form.get("arrival") or "").strip(),
        "departure_raw": (request.form.get("departure") or "").strip(),
        "transport": request.form.get("transport") or "",
        "comments": (request.form.get("comments") or "").strip(),
    }
    for veld, _label in OfferRequest.TEAM_FIELDS:
        values[veld] = (request.form.get(veld) or "").strip()
    return values


@offers_bp.route("/request-offer", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def request_offer():
    if request.method != "POST":
        return render_template("request_offer.html", transport_choices=TRANSPORT_CHOICES, form=_form_values())

    form = _form_values()

    error = None
    if not form["club_name"] or not form["country"] or not form["contact_person"] or not form["email"]:
        error = _("Please fill in club, country, contact person and email address.")
    elif "@" not in form["email"]:
        error = _("Please enter a valid email address.")
    elif sum(_parse_int(form[veld]) for veld, _label in OfferRequest.TEAM_FIELDS) == 0:
        error = _("Please fill in at least one team in at least one category.")

    if error:
        return render_template("request_offer.html", transport_choices=TRANSPORT_CHOICES, form=form, error=error)

    offer_request = OfferRequest(
        club_name=form["club_name"], country=form["country"],
        contact_person=form["contact_person"], email=form["email"], phone=form["phone"] or None,
        expected_participants=_parse_int(form["expected_participants_raw"]) or None,
        preferred_package=form["preferred_package"] or None,
        arrival_date=_parse_date(form["arrival_raw"]), departure_date=_parse_date(form["departure_raw"]),
        transport=form["transport"] if form["transport"] in TRANSPORT_CHOICES else None,
        comments=form["comments"] or None,
    )
    for veld, _label in OfferRequest.TEAM_FIELDS:
        setattr(offer_request, veld, _parse_int(form[veld]))

    db.session.add(offer_request)
    db.session.commit()

    try:
        send_offer_request_mail(offer_request)
    except Exception as exc:
        # Mail-fout mag de aanvraag niet blokkeren (die staat al veilig in de
        # database) - wel loggen, zelfde patroon als routes/main.contact.
        current_app.logger.error(f"Kon offerteaanvraag-mail niet versturen: {exc}")

    return render_template("request_offer.html", transport_choices=TRANSPORT_CHOICES, form=_form_values(), success=True)
