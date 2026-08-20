"""
utils/nav.py
-------------
Bouwt de navbar-boom op uit NavItem-rijen. Wordt via een context processor
(zie app.py) in elke template geïnjecteerd als 'nav_tree', zodat base.html
de navigatie kan renderen zonder dat elke route dit zelf moet meegeven.
"""

from flask import url_for
from werkzeug.routing import BuildError

from models import NavItem


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

    def build_level(parent_id):
        nodes = []
        for item in by_parent.get(parent_id, []):
            if not item.is_visible:
                continue
            node = {
                "id": item.id,
                "label": item.label,
                "item_type": item.item_type,
                "open_in_new_tab": item.open_in_new_tab,
                "url": _resolve_url(item),
                "children": build_level(item.id),
            }
            # Een klikbaar item zonder oplosbare URL (bv. gedepubliceerde
            # pagina of verwijderd route-endpoint) tonen we niet.
            if item.item_type not in ("category", "divider") and node["url"] is None:
                continue
            nodes.append(node)
        return nodes

    return build_level(None)
