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


def send_contact_mail(name, email, message):
    """Stuurt een kopie van het contactformulier naar de organisatiemail."""
    gmail_user = current_app.config["GMAIL_USER"]

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = gmail_user
    msg["Subject"] = "Nieuw contactformulier bericht"
    msg["Reply-To"] = _veilige_header_waarde(email)

    body = f"""
    Naam: {name}
    Email: {email}

    Bericht:
    {message}
    """
    msg.attach(MIMEText(body, "plain"))
    _send(msg)
