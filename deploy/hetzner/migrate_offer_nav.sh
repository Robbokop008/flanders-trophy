#!/bin/bash
# Eenmalig migratiescript, uit te voeren via konsoleH's Cron job Manager
# (handmatig via het afspeel-icoontje, niet als terugkerende taak) - zie
# deploy/hetzner/create_admin.sh voor hetzelfde patroon.
#
# Zet het "Request Your Offer"-navitem om naar een "route"-item dat
# rechtstreeks naar offers.request_offer linkt (zie scripts/migrate_offer_nav.py
# en utils/nav.py build_nav_tree()), zodat het navitem dezelfde 3 standen
# volgt als de knop op de homepage.
#
# Idempotent: opnieuw draaien na een geslaagde run doet niets.
#
# Na een geslaagde run mag je deze cronjob weer verwijderen in konsoleH.

/usr/home/drf93y/virtualenvs/flanders_trophy/bin/python /usr/home/drf93y/flanders-trophy/scripts/migrate_offer_nav.py
