"""
scripts/backup_db.py
---------------------
Maakt een backup van de SQLite-database: een lokale kopie in
instance/backups/ (met rotatie, de laatste BEWAAR_AANTAL dagen blijven
bewaard) én een off-server kopie via e-mail naar de organisatiemail, zodat
een probleem met de server zelf niet ook de enige backup meeneemt.

Bedoeld om dagelijks te draaien via een scheduled task (bv. PythonAnywhere's
"Tasks"-tabblad):

    python3 scripts/backup_db.py

Ondersteunt enkel SQLite (de huidige productie-database). Draait
Postgres via DATABASE_URL, dan stopt het script met een duidelijke melding -
Postgres-backups vragen een andere aanpak (bv. pg_dump).
"""

import os
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import BASE_DIR

BACKUP_DIR = os.path.join(BASE_DIR, "instance", "backups")
BEWAAR_AANTAL = 14  # aantal dagelijkse backups dat bewaard blijft


def maak_backup(db_pad):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    tijdstempel = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    doelpad = os.path.join(BACKUP_DIR, f"flanders_trophy_{tijdstempel}.db")

    bron = sqlite3.connect(db_pad)
    doel = sqlite3.connect(doelpad)
    with doel:
        bron.backup(doel)
    bron.close()
    doel.close()

    return doelpad


def ruim_oude_backups_op():
    bestanden = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith(".db"))
    for oud in bestanden[:-BEWAAR_AANTAL]:
        os.remove(os.path.join(BACKUP_DIR, oud))


def main():
    app = create_app("production")
    with app.app_context():
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        if not db_uri.startswith("sqlite:///"):
            print("backup_db.py ondersteunt enkel SQLite; DATABASE_URL wijst naar een andere database.")
            return

        db_pad = db_uri.replace("sqlite:///", "", 1)
        if not os.path.exists(db_pad):
            print(f"Geen databasebestand gevonden op {db_pad}.")
            return

        backup_pad = maak_backup(db_pad)
        ruim_oude_backups_op()
        print(f"Backup aangemaakt: {backup_pad}")

        from utils.mail import send_backup_mail
        try:
            send_backup_mail(backup_pad)
            print("Backup als bijlage gemaild.")
        except Exception as exc:
            app.logger.error(f"Kon backupmail niet versturen: {exc}")
            print(f"Waarschuwing: backupmail versturen mislukt ({exc}). Lokale kopie staat wel klaar.")


if __name__ == "__main__":
    main()
