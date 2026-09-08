#!/bin/bash
# Eenmalig migratiescript, uit te voeren via konsoleH's Cron job Manager
# (handmatig via het afspeel-icoontje, niet als terugkerende taak) - zie
# deploy/hetzner/create_admin.sh voor hetzelfde patroon.
#
# Voegt de kolom site_settings.offer_status toe (zie scripts/migrate_offer_status.py
# en models.py OFFER_STATUS_CHOICES) zonder de bestaande database te
# overschrijven. Idempotent: opnieuw draaien na een geslaagde run doet niets.
#
# Na een geslaagde run mag je deze cronjob weer verwijderen in konsoleH.

/usr/home/drf93y/virtualenvs/flanders_trophy/bin/python /usr/home/drf93y/flanders-trophy/scripts/migrate_offer_status.py
