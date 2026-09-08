#!/bin/bash
# Eenmalig script om het allereerste admin-account aan te maken, uit te
# voeren via konsoleH's Cron job Manager (handmatig via het afspeel-icoontje).
# Verwijder dit bestand en de bijhorende cronjob NA gebruik - het bevat
# hieronder een wachtwoord in platte tekst.

/usr/home/drf93y/virtualenvs/flanders_trophy/bin/python /usr/home/drf93y/flanders-trophy/scripts/create_admin.py \
    --username RobbeBoyen \
    --email robbeboyen28@gmail.com \
    --password "placeholder" \
    --first-name Robbe \
    --last-name Boyen
