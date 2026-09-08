# -*- coding: utf-8 -*-
"""
scripts/migrate_offer_status.py
------------------------------------
Eenmalige migratie: voegt de kolom SiteSettings.offer_status toe (zie
models.py OFFER_STATUS_CHOICES) waarmee een admin via het adminpaneel
(routes/admin.py home_settings) de "Request your Offer"-knop op de homepage
kan zetten op "nog niet beschikbaar", "beschikbaar" of "niet meer
beschikbaar" - zie templates/index.html en routes/offers.py request_offer.

De kolom wordt via een losse ALTER TABLE toegevoegd i.p.v. via
db.create_all() (dat enkel ontbrekende tabellen aanmaakt, geen kolommen aan
bestaande tabellen toevoegt) - zie README.md voor waarom dit project geen
Flask-Migrate/Alembic gebruikt.

Idempotent: als de kolom al bestaat wordt de ALTER TABLE overgeslagen.

Gebruik:
    python scripts/migrate_offer_status.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app import create_app
from extensions import db
from models import OFFER_STATUS_AVAILABLE


def run():
    app = create_app("development")
    with app.app_context():
        inspector = inspect(db.engine)
        bestaande_kolommen = {col["name"] for col in inspector.get_columns("site_settings")}
        if "offer_status" in bestaande_kolommen:
            print("Kolom 'offer_status' bestaat al - ALTER TABLE overgeslagen.")
            return
        with db.engine.begin() as conn:
            conn.execute(text(
                f"ALTER TABLE site_settings ADD COLUMN offer_status VARCHAR(20) "
                f"NOT NULL DEFAULT '{OFFER_STATUS_AVAILABLE}'"
            ))
        print("Kolom 'offer_status' toegevoegd aan site_settings.")


if __name__ == "__main__":
    run()
