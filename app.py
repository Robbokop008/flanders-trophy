"""
app.py
------
Dit is het hart van de applicatie. Hier wordt de Flask-app aangemaakt via
een "application factory" (de functie create_app). Dat patroon zorgt ervoor
dat je later makkelijk kan testen, meerdere configuraties kan gebruiken,
en de app in kleinere, overzichtelijke stukken (blueprints) kan opdelen.

Starten voor development doe je via run.py, niet via dit bestand direct.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request

from config import config_by_name, ONVEILIGE_STANDAARD_SECRET_KEY
from extensions import db, csrf, limiter, babel


def create_app(config_name="development"):
    """Bouwt en configureert een Flask-app en geeft die terug."""

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Geen stille onveilige standaardwaarde in productie: als SECRET_KEY niet
    # via de omgevingsvariabelen ingesteld is, valt Config terug op een
    # sleutel die letterlijk in de broncode staat (handig om lokaal snel te
    # kunnen opstarten, maar onveilig als dat ook in productie zou gebeuren -
    # daarmee zijn sessies/cookies voor iedereen met leestoegang tot de repo
    # te vervalsen). Faal hier duidelijk i.p.v. stil onveilig te draaien.
    if config_name == "production" and app.config["SECRET_KEY"] == ONVEILIGE_STANDAARD_SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY staat nog op de onveilige standaardwaarde. Stel een "
            "echte, geheime sleutel in via de omgevingsvariabelen (.env) "
            "voor je de site in productie draait."
        )

    # Logging naar een draaiend logbestand (instance/logs/app.log) i.p.v.
    # enkel de console-output van de WSGI-server, die op een host als
    # PythonAnywhere niet altijd makkelijk terug te vinden is. Bestaande
    # current_app.logger.warning/error-aanroepen (routes/admin.py,
    # routes/main.py, routes/offers.py) komen hierdoor ergens terecht i.p.v.
    # in het niets te verdwijnen.
    if not app.debug and not app.testing:
        log_map = os.path.join(app.root_path, "instance", "logs")
        os.makedirs(log_map, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_map, "app.log"), maxBytes=1_000_000, backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    # Extensies koppelen aan de app
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from utils.i18n import get_locale, resolve_i18n_field, raw_i18n_field
    babel.init_app(app, locale_selector=get_locale)

    # Taalwisselaar + vertaalde CMS-paginatitels (zie utils/i18n.py en
    # templates/pages/view.html) beschikbaar in elke template.
    @app.context_processor
    def inject_i18n():
        return {"current_lang": get_locale(), "languages": app.config["LANGUAGES"]}

    # Haalt de juiste taalwaarde uit een per-taal blok-veld op: i18n_value
    # (met terugval naar Engels) voor de publieke blok-templates, i18n_raw
    # (zonder terugval) om het admin-blokformulier per taal correct leeg/
    # gevuld te tonen bij bewerken - zie utils/i18n.py.
    app.add_template_global(resolve_i18n_field, name="i18n_value")
    app.add_template_global(raw_i18n_field, name="i18n_raw")

    # Blueprints registreren: dit "plakt" de routes uit routes/*.py
    # aan de app vast.
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.pages import pages_bp
    from routes.offers import offers_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(offers_bp)

    # Zorgt dat de database-tabellen bestaan (handig in development;
    # voor productie gebruik je later beter Flask-Migrate).
    with app.app_context():
        db.create_all()

    # Stelt de navbar-boom (NavItem's) beschikbaar in elke template, zodat
    # base.html de navigatie kan renderen zonder dat elke route dit zelf
    # moet meegeven.
    from utils.nav import build_nav_tree

    @app.context_processor
    def inject_nav_tree():
        return {"nav_tree": build_nav_tree()}

    # Footer-copyrightjaar: automatisch het huidige jaar, niet iets wat een
    # admin kan laten "vergeten bijwerken" - zie templates/base.html.
    from datetime import datetime as _datetime

    @app.context_processor
    def inject_huidig_jaar():
        return {"huidig_jaar": _datetime.utcnow().year}

    # Welke body-class (zie static/style.css) een pagina krijgt, per
    # route-endpoint - een gewone Python-lookup i.p.v. een groeiende
    # if/elif-keten in templates/base.html.
    PAGINA_STIJL_PER_ENDPOINT = {
        "main.home": "home-page",
        "main.contact": "content-page",
        "pages.view": "content-page",
        "offers.request_offer": "content-page",
        "auth.login": "auth-page",
    }

    @app.context_processor
    def inject_body_page_class():
        return {"body_page_class": PAGINA_STIJL_PER_ENDPOINT.get(request.endpoint)}

    # Jinja-filter die gesaniteerde rich-text HTML omzet naar leesbare platte
    # tekst voor previews - zie utils/sanitize.py.
    from utils.sanitize import html_naar_platte_tekst

    app.add_template_filter(html_naar_platte_tekst, name="platte_tekst")

    # Jinja-global om de canonieke video-embed-URL server-side op te bouwen
    # in templates/pages/_blocks/video.html - zie utils/url_validation.py.
    from utils.url_validation import build_video_embed_url

    app.add_template_global(build_video_embed_url, name="video_embed_url")

    # Jinja-global om de stijlvelden (uitlijning/achtergrond/breedte/witruimte)
    # van een pagina-blok met defaults aan te vullen - zie utils/page_blocks.py.
    from utils.page_blocks import resolve_style

    app.add_template_global(resolve_style, name="resolve_style")

    # Jinja-global om een meta-omschrijving af te leiden uit de eigenlijke
    # paginainhoud (i.p.v. een apart in te vullen SEO-veld) - zie
    # utils/seo.py en templates/base.html (block meta_description).
    from utils.seo import page_meta_description

    app.add_template_global(page_meta_description, name="page_meta_description")

    # Eigen foutpagina's i.p.v. Flask/Werkzeug's kale standaardpagina's:
    # 404 (onbestaande URL) en 429 (rate limit overschreden, bv. te vaak
    # inloggen na elkaar - zie @limiter.limit(...) in routes/auth.py).
    @app.errorhandler(404)
    def pagina_niet_gevonden(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def te_veel_aanvragen(_error):
        return render_template("errors/429.html"), 429

    # Onverwachte serverfouten: nette pagina i.p.v. Flask/Werkzeug's kale
    # standaardpagina, en de volledige traceback in het logbestand
    # hierboven i.p.v. enkel zichtbaar voor wie toevallig de host-console
    # bekijkt.
    @app.errorhandler(500)
    def interne_serverfout(error):
        app.logger.error("Interne serverfout op %s: %s", request.path, error, exc_info=True)
        return render_template("errors/500.html"), 500

    # Baseline HTTP-securityheaders op elke response. Geen Content-Security-
    # Policy hier: de site gebruikt op verschillende plekken inline <style>/
    # <script>, en een CSP zonder zorgvuldige nonce-aanpak zou die stukken
    # zomaar kunnen blokkeren - dat is bewust buiten deze scope gehouden.
    @app.after_request
    def voeg_security_headers_toe(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        # De admin-preview van een pagina moet in een eigen <iframe> in het
        # bewerkscherm kunnen tonen (zie admin.preview_page) - enkel daar
        # SAMEORIGIN i.p.v. DENY, zodat framen van buitenaf nog steeds
        # geblokkeerd blijft.
        if request.endpoint == "admin.preview_page":
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        else:
            response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    return app
