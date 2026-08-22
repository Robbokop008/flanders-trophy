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
translations/<taal>/LC_MESSAGES - CMS-paginatitels/-inhoud worden per taal
opgeslagen (zie resolve_i18n_field hieronder) en automatisch aangevuld via
DeepL wanneer een admin een pagina opslaat (zie auto_translate_i18n_field
hieronder en utils/translate.py)."""

import re

from flask import session, request, current_app

from utils.translate import translate_text


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


# Voorkeursvolgorde om de "brontaal" van een i18n-veld te bepalen bij het
# automatisch vertalen: admins typen voortaan doorgaans eerst Nederlands,
# maar bestaande content (van vóór deze functie) is Engels - vandaar nl vóór
# en, en fr/de erna als er ooit enkel in die talen getypt wordt.
_AUTO_TRANSLATE_SOURCE_PRIORITY = ("nl", "en", "fr", "de")


def _is_leeg(value, html):
    """Is 'value' effectief leeg? Voor gewone tekstvelden volstaat .strip(),
    maar Quill (de rich-text-editor) stuurt een ongebruikte taaleditor niet
    als lege string door, wel als '<p><br></p>' - zonder deze check zou
    auto_translate_i18n_field zo'n taal ten onrechte als 'al ingevuld' zien
    en dus overslaan (zelfde controle als _html_is_blank in
    routes/admin.py, hier herbruikt omdat deze module geen routes mag
    importeren)."""
    value = value or ""
    if not value.strip():
        return True
    if html:
        tekst = re.sub(r"<[^>]+>", "", value).strip()
        return not tekst and "<img" not in value
    return False


def auto_translate_i18n_field(value, html=False):
    """Vult de lege talen van een per-taal veld (zoals geproduceerd door
    _parse_i18n_field in routes/admin.py) automatisch aan via DeepL, op basis
    van de eerst ingevulde taal (zie _AUTO_TRANSLATE_SOURCE_PRIORITY). Talen
    die de admin al zelf ingevuld heeft, worden nooit overschreven. Geeft
    'value' ongewijzigd terug als er geen brontekst is, of als DeepL niet
    beschikbaar is (zie utils/translate.translate_text - faalt dan soft)."""
    if not isinstance(value, dict):
        return value

    source_lang = next(
        (lang for lang in _AUTO_TRANSLATE_SOURCE_PRIORITY if not _is_leeg(value.get(lang), html)),
        None,
    )
    if source_lang is None:
        return value

    source_text = value[source_lang]
    result = dict(value)
    for lang in current_app.config["LANGUAGES"]:
        if lang == source_lang or not _is_leeg(result.get(lang), html):
            continue
        vertaling = translate_text(source_text, target_lang=lang, source_lang=source_lang, html=html)
        if vertaling is not None:
            result[lang] = vertaling
    return result
