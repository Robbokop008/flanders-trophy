# -*- coding: utf-8 -*-
"""
scripts/debug_nav_items.py
------------------------------
Alleen-lezen diagnosescript: print elk NavItem-rij zodat je op de
productieserver kan nakijken hoe het "Request your Offer"-navitem precies
staat ingesteld (item_type, route_endpoint, external_url, ...) - handig als
utils/nav.py build_nav_tree() het item niet herkent als de offerteknop (zie
models.SiteSettings.offer_status).

Wijzigt niets aan de database.

Gebruik:
    python scripts/debug_nav_items.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from models import NavItem


def run():
    app = create_app("development")
    with app.app_context():
        for item in NavItem.query.order_by(NavItem.parent_id, NavItem.position).all():
            print(
                f"id={item.id} parent_id={item.parent_id} type={item.item_type!r} "
                f"label={item.label!r} route_endpoint={item.route_endpoint!r} "
                f"external_url={item.external_url!r} page_id={item.page_id} "
                f"visible={item.is_visible}"
            )


if __name__ == "__main__":
    run()
