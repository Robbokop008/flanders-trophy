# -*- coding: utf-8 -*-
"""
scripts/migrate_offer_request_nights.py
------------------------------------------
Eenmalige migratie voor het vereenvoudigde "Request Your Offer"-formulier
(routes/offers.py, templates/request_offer.html): arrival_date,
departure_date en transport zijn uit OfferRequest verdwenen (aankomst,
vertrek en vervoer worden niet meer gevraagd), en daarvoor in de plaats is
er nights (aantal overnachtingen: 2 = vertrek zondag, 3 = vertrek
maandag) bijgekomen - zie models.NIGHTS_CHOICES.

De kolom wordt via een losse ALTER TABLE toegevoegd i.p.v. via
db.create_all() (dat enkel ontbrekende tabellen aanmaakt, geen kolommen aan
bestaande tabellen toevoegt) - zie README.md voor waarom dit project geen
Flask-Migrate/Alembic gebruikt.

De oude kolommen (arrival_date, departure_date, transport) worden bewust
niet verwijderd: SQLite kan dat niet zonder de tabel te herbouwen, en
ongebruikte kolommen die niet meer in het model staan zijn onschadelijk -
eventuele oude data blijft gewoon staan voor wie ze nog wil inkijken.

Idempotent: als de kolom al bestaat wordt de ALTER TABLE overgeslagen.

Gebruik:
    python scripts/migrate_offer_request_nights.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app import create_app
from extensions import db


def run():
    app = create_app("development")
    with app.app_context():
        inspector = inspect(db.engine)
        bestaande_kolommen = {col["name"] for col in inspector.get_columns("offer_requests")}
        if "nights" in bestaande_kolommen:
            print("Kolom 'nights' bestaat al - ALTER TABLE overgeslagen.")
            return
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE offer_requests ADD COLUMN nights INTEGER"))
        print("Kolom 'nights' toegevoegd aan offer_requests.")


if __name__ == "__main__":
    run()
