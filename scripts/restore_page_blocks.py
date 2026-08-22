# -*- coding: utf-8 -*-
"""
scripts/restore_page_blocks.py
---------------------------------
Noodherstelscript: op de productie-database (PythonAnywhere) bevatte de
'page_blocks'-tabel corrupte data (rijen die eigenlijk navigatie-data leken
te zijn i.p.v. echte paginablokken - block_type als "Home"/"Tournament"/...,
data als de platte string "route"/"category"/"page" i.p.v. geldige JSON).
Hoe dat precies gebeurd is, kon niet met zekerheid achterhaald worden (de
seed-scripts in deze repo zijn nagekeken en bevatten geen fout die dit zou
verklaren) - dit script herstelt de paginablokken gewoon naar de correcte
inhoud, ongeacht de oorzaak.

Gebruikt scripts/restore_page_blocks_data.json (een export van de correcte
PageBlock-data, per paginaslug) om voor elke pagina:
  1. de bestaande (mogelijk corrupte) PageBlock-rijen te verwijderen,
  2. de correcte blokken opnieuw aan te maken, in de juiste volgorde.

Matcht op Page.slug (niet op numerieke id), want de id's van pagina's op
productie hoeven niet overeen te komen met die in de lokale database waaruit
dit bestand geëxporteerd is.

Idempotent: opnieuw draaien geeft gewoon nog eens dezelfde correcte inhoud
terug (bestaande blokken worden eerst verwijderd, dus geen duplicaten).

Gebruik (op PythonAnywhere, in je projectmap, virtualenv actief):
    python scripts/restore_page_blocks.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app import create_app
from extensions import db
from models import Page, PageBlock

DATA_FILE = Path(__file__).resolve().parent / "restore_page_blocks_data.json"


def run():
    app = create_app("production")
    with app.app_context():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)

        # Groepeer per slug, in de oorspronkelijke volgorde.
        per_slug = {}
        for item in items:
            per_slug.setdefault(item["slug"], []).append(item)

        hersteld = 0
        niet_gevonden = []
        for slug, blocks in per_slug.items():
            page = Page.query.filter_by(slug=slug).first()
            if page is None:
                niet_gevonden.append(slug)
                continue

            # Rechtstreekse SQL i.p.v. page.blocks/PageBlock.query: de
            # bestaande rijen kunnen ongeldige JSON in 'data' bevatten (dat
            # is precies het probleem dat dit script oplost), waardoor de
            # normale ORM-relationship crasht bij het inladen.
            aantal_bestaand = db.session.execute(
                text("SELECT COUNT(*) FROM page_blocks WHERE page_id = :pid"), {"pid": page.id}
            ).scalar()
            db.session.execute(text("DELETE FROM page_blocks WHERE page_id = :pid"), {"pid": page.id})

            for item in blocks:
                db.session.add(PageBlock(
                    page_id=page.id,
                    block_type=item["block_type"],
                    position=item["position"],
                    data=item["data"],
                ))
            hersteld += 1
            print(f"  + {slug}: {aantal_bestaand} bestaand(e) blok(ken) vervangen door {len(blocks)} correcte blok(ken)")

        db.session.commit()
        print(f"\nKlaar: {hersteld} pagina('s) hersteld.")
        if niet_gevonden:
            print(f"LET OP: geen pagina gevonden voor slug(s): {', '.join(niet_gevonden)} - niets gedaan voor deze.")


if __name__ == "__main__":
    run()
