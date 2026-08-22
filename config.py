"""
config.py
---------
Alle instellingen voor de Flask-app staan hier gebundeld, zodat je nooit
gevoelige gegevens (zoals een secret key of database-wachtwoord) hardcoded
in je code hoeft te zetten. Instellingen worden uit omgevingsvariabelen
gehaald (.env-bestand), met een veilige standaardwaarde voor development.
"""

import os
from dotenv import load_dotenv

# Basisdirectory van het project, handig voor bestandspaden
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Laad variabelen uit het .env-bestand in de projectroot (indien aanwezig).
# Expliciet pad i.p.v. load_dotenv() zonder argument: dat laatste zoekt vanaf
# de working directory van het proces, en die klopt niet noodzakelijk onder
# een WSGI-server (bv. PythonAnywhere) - .env werd daardoor stilzwijgend
# genegeerd in plaats van een fout te geven.
load_dotenv(os.path.join(BASE_DIR, ".env"))

# instance/ staat niet in git (enkel *.db is genegeerd, maar de map zelf
# wordt door git niet getrackt als ze leeg is) - zonder deze regel bestaat de
# map niet na een verse git clone, en faalt SQLite met "unable to open
# database file" zodra db.create_all() de db probeert aan te maken.
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

# Standaard SQLite-pad, gedeeld door Development- en ProductionConfig zodat
# je zonder DATABASE_URL (bv. op een host zonder losse databaseservice, zoals
# PythonAnywhere's gratis plan) ook in productie gewoon met SQLite draait.
_DEFAULT_SQLITE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'flanders_trophy.db')}"


# Enkel bedoeld als snelle fallback voor lokaal ontwikkelen. create_app()
# (app.py) weigert op te starten met config_name="production" zolang
# SECRET_KEY nog op deze waarde staat.
ONVEILIGE_STANDAARD_SECRET_KEY = "verander-deze-sleutel-in-productie"


class Config:
    """Instellingen die in elke omgeving gelden."""
    SECRET_KEY = os.environ.get("SECRET_KEY", ONVEILIGE_STANDAARD_SECRET_KEY)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Publieke site in 4 talen (zie utils/i18n.py voor taalkeuze-logica):
    # BABEL_DEFAULT_LOCALE hieronder is enkel de fallback-taal voor de
    # site-chrome (navigatie, knoppen, formulieren, vertaald via
    # translations/<taal>/LC_MESSAGES). CMS-paginatitels en -inhoud worden
    # per taal opgeslagen en automatisch aangevuld via DeepL zodra een admin
    # een taal invult (zie utils/translate.py, utils/i18n.py).
    LANGUAGES = {"en": "English", "nl": "Nederlands", "fr": "Français", "de": "Deutsch"}
    BABEL_DEFAULT_LOCALE = "en"
    BABEL_TRANSLATION_DIRECTORIES = os.path.join(BASE_DIR, "translations")

    # Sessiecookie hardening: HttpOnly voorkomt uitlezen via JavaScript (bv.
    # bij een XSS-lek elders), SameSite=Lax beperkt wanneer de cookie
    # meegestuurd wordt bij een request vanaf een andere site (CSRF-defense
    # in depth, naast Flask-WTF's eigen CSRF-tokens). SESSION_COOKIE_SECURE
    # staat pas op True in productie (zie ProductionConfig) - lokaal draait
    # de site over gewone http, waar een secure cookie nooit verstuurd zou worden.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Mail (contactformulier)
    GMAIL_USER = os.environ.get("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

    # Automatische vertaling van CMS-paginatitels/-inhoud (zie utils/translate.py) -
    # optioneel: zonder key wordt er simpelweg niet vertaald (utils/translate.py
    # geeft dan overal None terug in plaats van te crashen).
    DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY")

    # Upload-map voor geüploade afbeeldingen: pagina-hero-afbeeldingen en
    # inline afbeeldingen in de pagina-editor (relatief aan static/)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images")
    # Upload-map voor downloadbare documenten (PDF/Word/Excel/PowerPoint) in
    # het "documents"-blok (zie routes/admin.py) - los van UPLOAD_FOLDER
    # hierboven, dat is specifiek voor afbeeldingen.
    DOCUMENT_UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "documents")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024   # 8 MB, voorkomt te grote uploads


class DevelopmentConfig(Config):
    """Instellingen voor lokaal ontwikkelen."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", _DEFAULT_SQLITE_URI)


def _normalize_database_url(url):
    """Sommige hosts (bv. oudere Heroku-achtige styleconventies) geven 'postgres://'
    terug, maar SQLAlchemy 1.4+ vereist het volledige 'postgresql://'-schema."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class ProductionConfig(Config):
    """Instellingen voor de live-omgeving (bv. PythonAnywhere, Render, Hetzner)."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get("DATABASE_URL")) or _DEFAULT_SQLITE_URI
    SESSION_COOKIE_SECURE = True


# Maak het eenvoudig om per omgeving de juiste config te kiezen
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
