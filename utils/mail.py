"""
utils/mail.py
--------------
Helperfuncties om e-mails te versturen via Gmail SMTP: contactformulier,
offerteaanvraag, databasebackup, en een beveiligingsmelding bij het
aanmaken van een nieuwe admin-login (zie routes/admin.py create_user).
"""

import os
import smtplib
from email.mime.application import MIMEApplication
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


def send_backup_mail(backup_pad):
    """Stuurt een databasebackup als bijlage naar de organisatiemail (zie
    scripts/backup_db.py) - de off-server kopie naast de lokale rotatie in
    instance/backups/, zodat een schijfprobleem op de server niet ook de
    enige backup meeneemt."""
    gmail_user = current_app.config["GMAIL_USER"]
    bestandsnaam = os.path.basename(backup_pad)

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = gmail_user
    msg["Subject"] = f"Databasebackup Flanders Trophy - {bestandsnaam}"
    msg.attach(MIMEText(f"Automatische databasebackup in bijlage: {bestandsnaam}", "plain"))

    with open(backup_pad, "rb") as f:
        bijlage = MIMEApplication(f.read(), Name=bestandsnaam)
    bijlage["Content-Disposition"] = f'attachment; filename="{bestandsnaam}"'
    msg.attach(bijlage)

    _send(msg)


def send_new_admin_mail(new_user, created_by):
    """Stuurt een beveiligingsmelding naar de organisatiemail zodra een
    nieuwe admin-login aangemaakt wordt (zie routes/admin.py create_user) -
    zodat een onverwachte/ongeautoriseerde nieuwe admin opvalt, ongeacht wie
    er op dat moment ingelogd was. Faalt bewust soft (zie de aanroep in
    routes/admin.py): een mailhapering mag het aanmaken van een admin niet
    blokkeren."""
    gmail_user = current_app.config["GMAIL_USER"]

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = gmail_user
    msg["Subject"] = f"Beveiligingsmelding: nieuwe {'admin' if new_user.is_admin else 'gebruiker'} aangemaakt - {_veilige_header_waarde(new_user.username)}"

    body = f"""
    Er werd zonet een nieuwe login aangemaakt op de Flanders Trophy-website.

    Naam: {new_user.first_name} {new_user.last_name}
    Gebruikersnaam: {new_user.username}
    Email: {new_user.email or '-'}
    Admin-rechten: {'Ja' if new_user.is_admin else 'Nee'}

    Aangemaakt door: {created_by.username} ({created_by.first_name} {created_by.last_name})
    Tijdstip: {new_user.created_at.strftime('%d/%m/%Y %H:%M') if new_user.created_at else '-'}

    Herken je dit niet, of kwam dit niet van jullie eigen team? Wijzig dan
    meteen het wachtwoord van de betrokken admin-account(s) en controleer
    de gebruikerslijst in het adminpaneel (/admin/users).
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
    Tarief: {offer_request.preferred_package or '-'}
    Aantal nachten: {offer_request.nights or '-'}

    Opmerkingen:
    {offer_request.comments or '-'}
    """
    msg.attach(MIMEText(body, "plain"))
    _send(msg)
