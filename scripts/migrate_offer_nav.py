"""
scripts/migrate_offer_nav.py
-------------------------------
Eenmalige migratie: het "Request Your Offer"-navitem (aangemaakt door
scripts/seed_navigation.py) wees tot nu toe naar een lege CMS-pagina met
uitleg + een link naar het contactformulier (scripts/seed_mvp_content.py),
als tussenoplossing zolang er nog geen echt formulier bestond.

Nu dat er een echt formulier is (routes/offers.py, /request-offer), zet dit
script het navitem om naar een "route"-item dat rechtstreeks naar
offers.request_offer linkt, en verwijdert de nu overbodige CMS-pagina
'request-your-offer' (die geen andere navitems meer aan zich heeft hangen).

Idempotent: als het navitem al van het type "route" is, gebeurt er niets.

Gebruik:
    python scripts/migrate_offer_nav.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from extensions import db
from models import NavItem, Page


def run():
    app = create_app("development")
    with app.app_context():
        item = NavItem.query.filter_by(label="Request Your Offer", parent_id=None).first()
        if item is None:
            print("Geen 'Request Your Offer'-navitem gevonden - niets te doen.")
            return

        if item.item_type == "route" and item.route_endpoint == "offers.request_offer":
            print("Navitem wijst al naar offers.request_offer - niets te doen.")
            return

        oude_page_id = item.page_id
        item.item_type = "route"
        item.route_endpoint = "offers.request_offer"
        item.page_id = None
        db.session.commit()
        print("Navitem 'Request Your Offer' wijst nu naar offers.request_offer.")

        if oude_page_id is not None:
            oude_page = Page.query.get(oude_page_id)
            if oude_page is not None and not NavItem.query.filter_by(page_id=oude_page.id).count():
                slug = oude_page.slug
                for block in list(oude_page.blocks):
                    db.session.delete(block)
                db.session.delete(oude_page)
                db.session.commit()
                print(f"Overbodige CMS-pagina '{slug}' verwijderd.")


if __name__ == "__main__":
    run()
