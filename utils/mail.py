"""
utils/mail.py
--------------
Helperfunctie om e-mails te versturen via Gmail SMTP: enkel het
contactformulier op deze site (de andere mailfuncties van de hoofdclubsite -
orderbevestiging, inschrijvingen, GDPR-meldingen - horen bij functionaliteit
die hier niet geport is).
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def _veilige_header_waarde(waarde):
    """Verwijdert regeleinden uit een waarde vóór die in een e-mailheader
    (Reply-To, Subject, ...) terechtkomt. Zonder dit zou gebruikersinvoer
    (bv. het e-mailadres/naam in een formulier) extra headers of een
    volledig nieuwe e-mailinhoud kunnen injecteren (header/CRLF-injectie)."""
    return (waarde or "").replace("\r", " ").replace("\n", " ").strip()


def _send(msg):
    gmail_user = current_app.config["GMAIL_USER"]
    gmail_password = current_app.config["GMAIL_APP_PASSWORD"]
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)


def send_contact_mail(name, email, message, topic=None):
    """Stuurt een kopie van het contactformulier naar de organisatiemail."""
    gmail_user = current_app.config["GMAIL_USER"]
    topic = _veilige_header_waarde(topic) or "General questions"

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = gmail_user
    msg["Subject"] = f"[{topic}] Nieuw contactformulier bericht"
    msg["Reply-To"] = _veilige_header_waarde(email)

    body = f"""
    Onderwerp: {topic}
    Naam: {name}
    Email: {email}

    Bericht:
    {message}
    """
    msg.attach(MIMEText(body, "plain"))
    _send(msg)


def send_offer_request_mail(offer_request):
    """Stuurt een notificatiemail naar de organisatiemail bij een nieuwe
    offerteaanvraag (models.OfferRequest), zodat het team meteen een offerte
    kan voorbereiden. Geen automatische bevestigingsmail naar de club zelf -
    die krijgt enkel de bevestiging op het scherm (zie routes/offers.py)."""
    gmail_user = current_app.config["GMAIL_USER"]

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = gmail_user
    msg["Subject"] = f"Nieuwe offerteaanvraag - {_veilige_header_waarde(offer_request.club_name)}"
    msg["Reply-To"] = _veilige_header_waarde(offer_request.email)

    teams_regel = ", ".join(
        f"{label}: {getattr(offer_request, veld) or 0}"
        for veld, label in offer_request.TEAM_FIELDS
        if getattr(offer_request, veld)
    ) or "(geen teams opgegeven)"

    body = f"""
    Club: {offer_request.club_name} ({offer_request.country})
    Contactpersoon: {offer_request.contact_person}
    Email: {offer_request.email}
    Telefoon: {offer_request.phone or '-'}

    Teams: {teams_regel}
    Verwacht aantal deelnemers: {offer_request.expected_participants or '-'}
    Voorkeur pakket: {offer_request.preferred_package or '-'}
    Aankomst: {offer_request.arrival_date or '-'}
    Vertrek: {offer_request.departure_date or '-'}
    Vervoer: {offer_request.transport or '-'}

    Opmerkingen:
    {offer_request.comments or '-'}
    """
    msg.attach(MIMEText(body, "plain"))
    _send(msg)
