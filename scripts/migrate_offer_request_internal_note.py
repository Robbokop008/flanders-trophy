# -*- coding: utf-8 -*-
"""
scripts/migrate_offer_request_internal_note.py
------------------------------------------------
Eenmalige migratie voor de fiche-pagina van offerteaanvragen
(routes/admin.py offer_request_detail, templates/admin/offer_request_detail.html):
internal_note op OfferRequest (models.py) laat een admin een interne notitie
bijhouden bij een aanvraag (bv. "offerte verstuurd op 3/10"), los van de
gegevens die de club zelf invulde.

De kolom wordt via een losse ALTER TABLE toegevoegd i.p.v. via
db.create_all() (dat enkel ontbrekende tabellen aanmaakt, geen kolommen aan
bestaande tabellen toevoegt) - zie README.md voor waarom dit project geen
Flask-Migrate/Alembic gebruikt.

Idempotent: als de kolom al bestaat wordt de ALTER TABLE overgeslagen.

Gebruik:
    python scripts/migrate_offer_request_internal_note.py
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
        if "internal_note" in bestaande_kolommen:
            print("Kolom 'internal_note' bestaat al - ALTER TABLE overgeslagen.")
            return
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE offer_requests ADD COLUMN internal_note TEXT"))
        print("Kolom 'internal_note' toegevoegd aan offer_requests.")


if __name__ == "__main__":
    run()
