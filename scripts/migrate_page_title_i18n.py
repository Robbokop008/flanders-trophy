# -*- coding: utf-8 -*-
"""
scripts/migrate_page_title_i18n.py
------------------------------------
Eenmalige migratie: voegt de kolom Page.title_i18n toe (zie models.py) en
vult ze voor elke bestaande pagina in met {"en": <huidige title>, "nl": "",
"fr": "", "de": ""}, meteen gevolgd door een automatische DeepL-vertaling
(dezelfde stap als bij het opslaan van een pagina, zie
routes/admin.py:add_page/edit_page) zodat bestaande pagina's meteen ook in
NL/FR/DE staan zonder dat een admin ze moet heropslaan.

Zet ook Page.title (de platte spiegelkolom, gebruikt in de interne
adminlijst - zie templates/admin/pages_list.html) telkens gelijk aan de
NL-titel zodra die gevuld is, exact dezelfde nl-of-en-of-eerste-taal-regel
als add_page/edit_page. Zonder deze stap bleven de oorspronkelijke 21
pagina's Engelse titels tonen in de adminlijst, terwijl een nieuw
aangemaakte pagina daar meteen zijn Nederlandse titel toont - verwarrend
inconsistent voor de admin.

De kolom wordt via een losse ALTER TABLE toegevoegd i.p.v. via
db.create_all() (dat enkel ontbrekende tabellen aanmaakt, geen kolommen aan
bestaande tabellen toevoegt) - zie README.md voor waarom dit project geen
Flask-Migrate/Alembic gebruikt.

Idempotent, en herbruikbaar als backfill: als de kolom al bestaat wordt
ALTER TABLE overgeslagen, en een taal die al ingevuld is wordt nooit
overschreven - maar een pagina waarvan title_i18n al bestaat doch nog lege
talen heeft (bv. omdat dit script de eerste keer zonder DEEPL_API_KEY
draaide) wordt wél opnieuw langsgegaan om die lege talen alsnog aan te
vullen. Dus: gewoon dit script nog eens draaien nadat je een DEEPL_API_KEY
in .env gezet hebt, vult de tot dan toe overgeslagen talen alsnog aan.

Gebruik:
    python scripts/migrate_page_title_i18n.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app import create_app
from extensions import db
from models import Page
from utils.i18n import auto_translate_i18n_field


def _add_title_i18n_column():
    inspector = inspect(db.engine)
    bestaande_kolommen = {col["name"] for col in inspector.get_columns("pages")}
    if "title_i18n" in bestaande_kolommen:
        print("Kolom 'title_i18n' bestaat al - ALTER TABLE overgeslagen.")
        return
    with db.engine.begin() as conn:
        conn.execute(text("ALTER TABLE pages ADD COLUMN title_i18n JSON"))
    print("Kolom 'title_i18n' toegevoegd aan pages.")


def run():
    app = create_app("development")
    with app.app_context():
        _add_title_i18n_column()

        vertaald = 0
        overgeslagen = 0
        for page in Page.query.order_by(Page.slug).all():
            basis = page.title_i18n or {"en": page.title, "nl": "", "fr": "", "de": ""}
            if all((basis.get(lang) or "").strip() for lang in ("en", "nl", "fr", "de")):
                overgeslagen += 1
                continue
            title_i18n = auto_translate_i18n_field(basis)
            if title_i18n == page.title_i18n:
                # Geen enkele taal kon aangevuld worden (bv. nog steeds geen
                # DEEPL_API_KEY) - niet nodeloos als "gewijzigd" tellen.
                overgeslagen += 1
                continue
            page.title_i18n = title_i18n
            vertaald += 1
            print(f"  + {page.slug}: title_i18n aangevuld ({', '.join(f'{k}={v!r}' for k, v in title_i18n.items())})")

        gespiegeld = 0
        for page in Page.query.all():
            nieuwe_titel = page.title_i18n.get("nl") or page.title_i18n.get("en") or next(
                (v for v in page.title_i18n.values() if v), page.title
            )
            if nieuwe_titel != page.title:
                print(f"  ~ {page.slug}: Page.title '{page.title}' -> '{nieuwe_titel}' (spiegelkolom voor adminlijst)")
                page.title = nieuwe_titel
                gespiegeld += 1

        db.session.commit()
        print(f"\nKlaar: {vertaald} pagina('s) van title_i18n voorzien/aangevuld, {overgeslagen} al volledig "
              f"(of nog steeds onvolledig zonder DEEPL_API_KEY), {gespiegeld} Page.title-spiegelkolom(men) bijgewerkt.")


if __name__ == "__main__":
    run()
