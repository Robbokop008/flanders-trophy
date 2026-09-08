"""
utils/nav.py
-------------
Bouwt de navbar-boom op uit NavItem-rijen. Wordt via een context processor
(zie app.py) in elke template geïnjecteerd als 'nav_tree', zodat base.html
de navigatie kan renderen zonder dat elke route dit zelf moet meegeven.
"""

from flask import url_for
from flask_babel import gettext as _
from werkzeug.routing import BuildError

from models import NavItem, SiteSettings, OFFER_STATUS_AVAILABLE, OFFER_STATUS_SOLD_OUT
from utils.i18n import get_locale, resolve_i18n_field


def _resolve_url(item):
    """Geeft de URL voor dit navitem terug, of None als het niet linkbaar is
    (categorie/divider) of niet meer oplosbaar is (bv. verouderd route_endpoint,
    of een onbereikbare/verwijderde pagina)."""
    if item.item_type == "page":
        if item.page is None or not item.page.is_published:
            return None
        return url_for("pages.view", slug=item.page.slug)

    if item.item_type == "route":
        try:
            return url_for(item.route_endpoint)
        except BuildError:
            return None

    if item.item_type == "external":
        return item.external_url

    return None


def build_nav_tree():
    """Geeft een lijst van top-level navitems terug, elk met een '.children'
    lijst (aangevuld met een opgeloste '.url' per item) en enkel de
    zichtbare/oplosbare items."""
    all_items = NavItem.query.order_by(NavItem.position).all()
    by_parent = {}
    for item in all_items:
        by_parent.setdefault(item.parent_id, []).append(item)

    lang = get_locale()
    offer_status = SiteSettings.get().offer_status
    offer_request_url = url_for("offers.request_offer")

    def build_level(parent_id):
        nodes = []
        for item in by_parent.get(parent_id, []):
            if not item.is_visible:
                continue
            node = {
                "id": item.id,
                "label": resolve_i18n_field(item.label_i18n, lang) or item.label,
                "item_type": item.item_type,
                "open_in_new_tab": item.open_in_new_tab,
                "url": _resolve_url(item),
                "disabled": False,
                "children": build_level(item.id),
            }
            # Het navitem naar het offerteformulier volgt dezelfde 3 standen
            # als de knop op de homepage (zie models.SiteSettings.offer_status,
            # templates/index.html) - tekst en klikbaarheid passen zich dus
            # samen aan, i.p.v. een verouderd label te tonen dat naar een
            # onbereikbaar formulier linkt (routes/offers.py request_offer).
            # Herkend op de opgeloste URL (i.p.v. enkel item_type == "route")
            # zodat dit ook werkt als het navitem als "external"-link naar
            # hetzelfde pad staat ingesteld (bv. handmatig aangemaakt/bewerkt
            # via /admin/navigation vóór scripts/migrate_offer_nav.py).
            if node["url"] == offer_request_url:
                if offer_status != OFFER_STATUS_AVAILABLE:
                    node["label"] = _("Sold out") if offer_status == OFFER_STATUS_SOLD_OUT else _("Request your Offer soon")
                    node["disabled"] = True
            # Een klikbaar item zonder oplosbare URL (bv. gedepubliceerde
            # pagina of verwijderd route-endpoint) tonen we niet.
            if item.item_type not in ("category", "divider") and node["url"] is None:
                continue
            nodes.append(node)
        return nodes

    return build_level(None)
