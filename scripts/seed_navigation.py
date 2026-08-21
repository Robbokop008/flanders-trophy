"""
scripts/seed_navigation.py
----------------------------
Zet de voorgestelde hoofdnavigatie voor de Flanders Trophy-site op: 7
hoofditems (Home, Tournament, Prices & Stay, Program, Results, Practical
Info, Contact) plus een aparte "Request Your Offer"-CTA, met de submenu's
zoals uitgewerkt in het herbouwvoorstel (customer journey: ontdekken ->
offerte aanvragen -> inschrijven -> voorbereiden -> tornooi volgen ->
resultaten).

Voor elk menu-item van het type "page" wordt een lege, ongepubliceerde
Page-stub aangemaakt (titel + slug, nog zonder blokken) zodat de structuur
al klopt terwijl de inhoud later via /admin/pages ingevuld wordt. Zolang
zo'n pagina ongepubliceerd blijft, toont utils/nav.build_nav_tree() het
bijhorende menu-item niet in de live navbar (zie _resolve_url) - de navbar
groeit dus vanzelf mee naarmate pagina's gepubliceerd worden.

"Home" en "Contact" linken naar bestaande vaste routes (main.home /
main.contact) en zijn dus meteen zichtbaar.

Idempotent: bestaande pagina's (op slug) en navitems (op label + parent)
worden hergebruikt in plaats van gedupliceerd - dit script kan dus veilig
opnieuw gedraaid worden, bv. na het toevoegen van een extra item hieronder.

Gebruik:
    python scripts/seed_navigation.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from extensions import db
from models import NavItem, Page


# Elk top-level item is één van:
#   {"label": ..., "type": "route", "endpoint": "main.xxx"}
#   {"label": ..., "type": "page", "slug": "..."}
#   {"label": ..., "type": "category", "children": [{"label": ..., "slug": "..."}, ...]}
NAV_STRUCTURE = [
    {"label": "Home", "type": "route", "endpoint": "main.home"},
    {
        "label": "Tournament",
        "type": "category",
        "children": [
            {"label": "About Flanders Trophy", "slug": "about-flanders-trophy"},
            {"label": "Categories", "slug": "categories"},
            {"label": "Tournament Format", "slug": "tournament-format"},
            {"label": "Tournament Rules", "slug": "tournament-rules"},
            {"label": "Fair Play", "slug": "fair-play"},
        ],
    },
    {
        "label": "Prices & Stay",
        "type": "category",
        "children": [
            {"label": "Packages & Tariffs", "slug": "packages-tariffs"},
            {"label": "Accommodation", "slug": "accommodation"},
            {"label": "Meals", "slug": "meals"},
            {"label": "Shuttle", "slug": "shuttle"},
        ],
    },
    {
        "label": "Program",
        "type": "category",
        "children": [
            {"label": "Weekend Program", "slug": "weekend-program"},
            {"label": "Teams & Groups", "slug": "teams-groups"},
            {"label": "Match Schedule", "slug": "match-schedule"},
            {"label": "Locations", "slug": "locations"},
            {"label": "Flag Parade", "slug": "flag-parade"},
        ],
    },
    {
        "label": "Results",
        "type": "category",
        "children": [
            {"label": "Live Results", "slug": "live-results"},
            {"label": "Rankings", "slug": "rankings"},
            {"label": "Previous Editions", "slug": "previous-editions"},
        ],
    },
    {
        "label": "Practical Info",
        "type": "category",
        "children": [
            {"label": "Check-in", "slug": "check-in"},
            {"label": "Travel & Parking", "slug": "travel-parking"},
            {"label": "FAQ", "slug": "faq"},
            {"label": "Downloads", "slug": "downloads"},
        ],
    },
    {"label": "Contact", "type": "route", "endpoint": "main.contact"},
    # Los van de 7 hoofditems: de belangrijkste conversieknop, rechtsboven
    # in contrasterende stijl - dat is een template/CSS-taak, hier zetten
    # we enkel het navitem + de doelpagina klaar.
    {"label": "Request Your Offer", "type": "page", "slug": "request-your-offer"},
]


def _get_or_create_page(slug, title):
    page = Page.query.filter_by(slug=slug).first()
    if page is None:
        page = Page(slug=slug, title=title, is_published=False)
        db.session.add(page)
        db.session.flush()  # page.id beschikbaar voor de NavItem hieronder
        print(f"  + pagina aangemaakt: {slug}")
    return page


def _get_or_create_nav_item(label, parent_id, next_position, **kwargs):
    item = NavItem.query.filter_by(label=label, parent_id=parent_id).first()
    if item is None:
        item = NavItem(label=label, parent_id=parent_id, position=next_position(), **kwargs)
        db.session.add(item)
        db.session.flush()
        print(f"  + navitem aangemaakt: {label}")
    return item


def run():
    app = create_app("development")
    with app.app_context():
        top_position = {"n": (db.session.query(db.func.max(NavItem.position)).filter_by(parent_id=None).scalar() or 0)}

        def next_top_position():
            top_position["n"] += 1
            return top_position["n"]

        for entry in NAV_STRUCTURE:
            label, item_type = entry["label"], entry["type"]

            if item_type == "route":
                _get_or_create_nav_item(
                    label, None, next_top_position,
                    item_type="route", route_endpoint=entry["endpoint"],
                )

            elif item_type == "page":
                page = _get_or_create_page(entry["slug"], label)
                _get_or_create_nav_item(
                    label, None, next_top_position,
                    item_type="page", page_id=page.id,
                )

            elif item_type == "category":
                category = _get_or_create_nav_item(label, None, next_top_position, item_type="category")

                child_position = {"n": (db.session.query(db.func.max(NavItem.position)).filter_by(parent_id=category.id).scalar() or 0)}

                def next_child_position():
                    child_position["n"] += 1
                    return child_position["n"]

                for child in entry["children"]:
                    page = _get_or_create_page(child["slug"], child["label"])
                    _get_or_create_nav_item(
                        child["label"], category.id, next_child_position,
                        item_type="page", page_id=page.id,
                    )

        db.session.commit()
        print("Navigatiestructuur staat klaar. Ongepubliceerde pagina's verschijnen pas in de live navbar zodra je ze publiceert via /admin/pages.")


if __name__ == "__main__":
    run()
