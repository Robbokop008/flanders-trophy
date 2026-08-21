"""
utils/i18n.py
---------------
Taalkeuze voor de publieke site (Engels/Nederlands/Frans/Duits). Bewust
sessie-gebaseerd (een 'lang'-cookie via de Flask-sessie) i.p.v. een
taalprefix in de URL (/nl/..., /fr/...): dat laatste is beter voor SEO per
taal, maar had een grote verbouwing van alle routes/links betekend. Deze
aanpak is de pragmatische keuze voor nu; een taalprefix kan later alsnog,
als aparte stap.

get_locale() wordt als locale_selector aan Flask-Babel doorgegeven (zie
app.py). Vertaalde site-chrome (navigatie, knoppen, formulieren) zit in
translations/<taal>/LC_MESSAGES - CMS-pagina-inhoud is voorlopig nog enkel
Engels (zie de melding in templates/pages/view.html)."""

from flask import session, request, current_app


def get_locale():
    lang = session.get("lang")
    if lang in current_app.config["LANGUAGES"]:
        return lang
    return request.accept_languages.best_match(current_app.config["LANGUAGES"].keys()) or current_app.config["BABEL_DEFAULT_LOCALE"]


def resolve_i18n_field(value, lang, fallback="en"):
    """Geeft de waarde voor 'lang' terug uit een per-taal veld van een
    PageBlock (bv. {"en": "...", "nl": "...", ...}), met terugval naar
    'fallback' (Engels) als die taal niet ingevuld is. Blokken die van vóór
    de meertalige content-velden dateren, hadden dat veld nog als platte
    string i.p.v. een dict - die worden hier ook nog opgevangen zodat zo'n
    (in principe niet meer voorkomend) blok niet stuk rendert.
    Gebruikt zowel in de publieke blok-templates (welke taal tonen) als in
    het admin-blokformulier (elk taalveld vullen bij bewerken) - zie
    app.py voor de registratie als Jinja-global 'i18n_value'."""
    if isinstance(value, dict):
        return value.get(lang) or value.get(fallback) or ""
    if lang == fallback:
        return value or ""
    return ""


def raw_i18n_field(value, lang):
    """Geeft de opgeslagen waarde voor 'lang' terug zonder terugval naar
    Engels - gebruikt om het admin-blokformulier te vullen bij bewerken
    (zie templates/admin/page_block_form.html), waar elk taalveld z'n eigen
    (mogelijk lege) waarde moet tonen i.p.v. per ongeluk de Engelse tekst in
    een leeg NL/FR/DE-veld te herhalen. Legacy platte-string data (van vóór
    de per-taal velden) wordt enkel voor 'en' teruggegeven."""
    if isinstance(value, dict):
        return value.get(lang) or ""
    if lang == "en":
        return value or ""
    return ""
