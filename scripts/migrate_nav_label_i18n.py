# -*- coding: utf-8 -*-
"""
scripts/migrate_nav_label_i18n.py
------------------------------------
Eenmalige migratie: voegt de kolom NavItem.label_i18n toe (zie models.py) en
vult ze voor elk bestaand navigatie-item in met {"en": <huidig label>, "nl":
"", "fr": "", "de": ""}, meteen gevolgd door een automatische DeepL-vertaling
(dezelfde stap als bij het opslaan van een navigatie-item, zie
routes/admin.py:add_nav_item/edit_nav_item) zodat bestaande menu-items meteen
ook in NL/FR/DE staan zonder dat een admin ze moet heropslaan.

Zet ook NavItem.label (de platte spiegelkolom, gebruikt in de interne
navigatie-adminlijst - zie templates/admin/navigation.html) telkens gelijk
aan het NL-label zodra dat gevuld is, exact dezelfde nl-of-en-of-eerste-taal-
regel als add_nav_item/edit_nav_item.

De kolom wordt via een losse ALTER TABLE toegevoegd i.p.v. via
db.create_all() (dat enkel ontbrekende tabellen aanmaakt, geen kolommen aan
bestaande tabellen toevoegt) - zie README.md voor waarom dit project geen
Flask-Migrate/Alembic gebruikt.

Idempotent, en herbruikbaar als backfill: net als migrate_page_title_i18n.py
kan je dit script gewoon nog eens draaien nadat je een DEEPL_API_KEY in .env
gezet hebt, om tot dan toe overgeslagen talen alsnog aan te vullen.

Gebruik:
    python scripts/migrate_nav_label_i18n.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app import create_app
from extensions import db
from models import NavItem
from utils.i18n import auto_translate_i18n_field


def _add_label_i18n_column():
    inspector = inspect(db.engine)
    bestaande_kolommen = {col["name"] for col in inspector.get_columns("nav_items")}
    if "label_i18n" in bestaande_kolommen:
        print("Kolom 'label_i18n' bestaat al - ALTER TABLE overgeslagen.")
        return
    with db.engine.begin() as conn:
        conn.execute(text("ALTER TABLE nav_items ADD COLUMN label_i18n JSON"))
    print("Kolom 'label_i18n' toegevoegd aan nav_items.")


def run():
    app = create_app("development")
    with app.app_context():
        _add_label_i18n_column()

        vertaald = 0
        overgeslagen = 0
        for item in NavItem.query.order_by(NavItem.id).all():
            basis = item.label_i18n or {"en": item.label, "nl": "", "fr": "", "de": ""}
            if all((basis.get(lang) or "").strip() for lang in ("en", "nl", "fr", "de")):
                overgeslagen += 1
                continue
            label_i18n = auto_translate_i18n_field(basis)
            if label_i18n == item.label_i18n:
                overgeslagen += 1
                continue
            item.label_i18n = label_i18n
            vertaald += 1
            print(f"  + item {item.id}: label_i18n aangevuld ({', '.join(f'{k}={v!r}' for k, v in label_i18n.items())})")

        gespiegeld = 0
        for item in NavItem.query.all():
            nieuw_label = item.label_i18n.get("nl") or item.label_i18n.get("en") or next(
                (v for v in item.label_i18n.values() if v), item.label
            )
            if nieuw_label != item.label:
                print(f"  ~ item {item.id}: NavItem.label '{item.label}' -> '{nieuw_label}' (spiegelkolom voor adminlijst)")
                item.label = nieuw_label
                gespiegeld += 1

        db.session.commit()
        print(f"\nKlaar: {vertaald} navigatie-item(s) van label_i18n voorzien/aangevuld, {overgeslagen} al volledig "
              f"(of nog steeds onvolledig zonder DEEPL_API_KEY), {gespiegeld} NavItem.label-spiegelkolom(men) bijgewerkt.")


if __name__ == "__main__":
    run()
