"""
scripts/create_admin.py
-------------------------
Maakt een admin-gebruiker aan (of werkt het wachtwoord van een bestaande
gebruiker met die gebruikersnaam bij). Er is bewust geen publieke
registratiepagina op deze site (zie routes/auth.py) - dit script is de
manier om je eerste (of een extra) admin-login aan te maken.

Idempotent: opnieuw draaien met dezelfde gebruikersnaam werkt het
wachtwoord/de gegevens van die gebruiker bij i.p.v. een duplicaat aan te maken.

Gebruik (interactief, vraagt de ontbrekende gegevens op):
    python scripts/create_admin.py

Of alles in één keer via argumenten:
    python scripts/create_admin.py --username admin --email admin@flanderstrophy.be --password EenSterkWachtwoord1! --first-name Admin --last-name User
"""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from extensions import db
from models import User


def _prompt(label, default=None):
    suffix = f" [{default}]" if default else ""
    waarde = input(f"{label}{suffix}: ").strip()
    return waarde or default or ""


def run(username, email, password, first_name, last_name):
    app = create_app("development")
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(
                username=username, email=email,
                first_name=first_name or "Admin", last_name=last_name or "User",
                is_admin=True,
            )
            db.session.add(user)
            actie = "aangemaakt"
        else:
            user.email = email or user.email
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.is_admin = True
            actie = "bijgewerkt (wachtwoord + is_admin=True)"

        user.set_password(password)
        db.session.commit()
        print(f"Admin-gebruiker '{username}' {actie}.")


def main():
    parser = argparse.ArgumentParser(description="Maak een admin-gebruiker aan of werk die bij.")
    parser.add_argument("--username")
    parser.add_argument("--email")
    parser.add_argument("--password")
    parser.add_argument("--first-name")
    parser.add_argument("--last-name")
    args = parser.parse_args()

    username = args.username or _prompt("Gebruikersnaam")
    email = args.email or _prompt("E-mailadres")
    first_name = args.first_name or _prompt("Voornaam", "Admin")
    last_name = args.last_name or _prompt("Achternaam", "User")
    password = args.password or getpass.getpass("Wachtwoord: ")

    if not username or not password:
        print("Gebruikersnaam en wachtwoord zijn verplicht.")
        sys.exit(1)

    run(username, email, password, first_name, last_name)


if __name__ == "__main__":
    main()
