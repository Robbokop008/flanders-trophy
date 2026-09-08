#!/bin/bash
# Eenmalig installatiescript, uit te voeren via konsoleH's Cron job Manager
# (handmatig via het afspeel-icoontje, niet als terugkerende taak) - er is
# geen interactieve SSH-shell beschikbaar op Webhosting M, dit is de manier
# om toch commando's op de server te draaien.

python3 -m pip install --user --break-system-packages virtualenv
python3 -m virtualenv /usr/home/drf93y/virtualenvs/flanders_trophy

# psycopg2-binary (PostgreSQL-driver) overslaan: de app gebruikt hier SQLite,
# en psycopg2-binary probeert anders C-code te compileren op de server, wat
# mislukt zonder de nodige compiler-bestanden (Python.h ontbreekt).
grep -v -i '^psycopg2' /usr/home/drf93y/flanders-trophy/requirements.txt > /usr/home/drf93y/requirements-server.txt

/usr/home/drf93y/virtualenvs/flanders_trophy/bin/pip install -r /usr/home/drf93y/requirements-server.txt flup
