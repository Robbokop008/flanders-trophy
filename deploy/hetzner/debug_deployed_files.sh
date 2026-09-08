#!/bin/bash
# Eenmalig diagnosescript, uit te voeren via konsoleH's Cron job Manager
# (handmatig via het afspeel-icoontje) - zie deploy/hetzner/create_admin.sh
# voor hetzelfde patroon.
#
# Controleert of de effectief geüploade bestanden op de server de nieuwe
# "offerteknop volgt offer_status"-code bevatten - zie
# scripts/debug_deployed_files.py.

/usr/home/drf93y/virtualenvs/flanders_trophy/bin/python /usr/home/drf93y/flanders-trophy/scripts/debug_deployed_files.py
