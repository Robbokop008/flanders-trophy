#!/bin/bash
# Eenmalig diagnosescript, uit te voeren via konsoleH's Cron job Manager
# (handmatig via het afspeel-icoontje) - zie deploy/hetzner/create_admin.sh
# voor hetzelfde patroon.
#
# Print alle NavItem-rijen (alleen-lezend, wijzigt niets) zodat je kan
# nakijken hoe het "Request your Offer"-navitem precies staat ingesteld -
# zie scripts/debug_nav_items.py en utils/nav.py build_nav_tree().

/usr/home/drf93y/virtualenvs/flanders_trophy/bin/python /usr/home/drf93y/flanders-trophy/scripts/debug_nav_items.py
