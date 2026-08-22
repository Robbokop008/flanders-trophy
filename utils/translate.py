# -*- coding: utf-8 -*-
"""
utils/translate.py
-------------------
Dunne wrapper rond de DeepL API, gebruikt door utils.i18n.auto_translate_i18n_field
om CMS-paginatitels en -inhoud automatisch aan te vullen in de talen die een
admin leeg laat (zie routes/admin.py: _parse_block_form, add_page/edit_page).

Faalt overal bewust "soft": zonder DEEPL_API_KEY, of bij een netwerk-/quotafout,
geeft translate_text() gewoon None terug in plaats van de opslag van de pagina
te laten crashen. De aanroeper laat het veld dan leeg, zoals vóór deze functie
bestond (zie utils/i18n.resolve_i18n_field() voor de fallback-naar-Engels die
in dat geval nog steeds van toepassing is).
"""

from flask import current_app

# Onze eigen taalcodes (config.LANGUAGES) -> DeepL-taalcodes. DeepL onderscheidt
# voor Engels een doeltaal-variant (EN-GB/EN-US) maar accepteert als brontaal
# gewoon "EN".
_DEEPL_TARGET_LANG = {"en": "EN-GB", "nl": "NL", "fr": "FR", "de": "DE"}
_DEEPL_SOURCE_LANG = {"en": "EN", "nl": "NL", "fr": "FR", "de": "DE"}

_translator = None
_translator_key = None


def _get_translator():
    """Bouwt de deepl.Translator lazy op (en hergebruikt hem), enkel als er
    een API-key geconfigureerd is. Geeft None terug zonder key, of als de
    deepl-package niet geïnstalleerd is."""
    global _translator, _translator_key

    api_key = current_app.config.get("DEEPL_API_KEY")
    if not api_key:
        return None

    if _translator is None or _translator_key != api_key:
        try:
            import deepl
        except ImportError:
            current_app.logger.warning("DEEPL_API_KEY is gezet maar de 'deepl'-package is niet geïnstalleerd.")
            return None
        _translator = deepl.Translator(api_key)
        _translator_key = api_key

    return _translator


def translate_text(text, target_lang, source_lang, html=False):
    """Vertaalt 'text' van source_lang naar target_lang (onze eigen taalcodes,
    bv. 'nl'/'en'/'fr'/'de'). Geeft None terug als er niets vertaald kon
    worden (geen tekst, geen API-key, of een fout bij de DeepL-aanroep) - de
    aanroeper (utils.i18n.auto_translate_i18n_field) laat het doelveld dan
    gewoon leeg."""
    text = (text or "").strip()
    if not text:
        return None

    translator = _get_translator()
    if translator is None:
        return None

    deepl_target = _DEEPL_TARGET_LANG.get(target_lang)
    deepl_source = _DEEPL_SOURCE_LANG.get(source_lang)
    if deepl_target is None or deepl_source is None:
        return None

    try:
        result = translator.translate_text(
            text,
            source_lang=deepl_source,
            target_lang=deepl_target,
            tag_handling="html" if html else None,
        )
        return result.text
    except Exception:
        current_app.logger.exception(f"DeepL-vertaling ({source_lang} -> {target_lang}) mislukt.")
        return None
