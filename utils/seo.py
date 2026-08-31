"""
utils/seo.py
------------
Kleine SEO-hulpfunctie: een meta-omschrijving afgeleid uit de eigenlijke
paginainhoud, i.p.v. een apart "SEO-omschrijving"-veld dat een admin per
pagina zou moeten invullen (extra werk voor iets dat meestal al gewoon in de
tekst staat). Gebruikt in templates/base.html (block meta_description),
zie routes/main.py voor robots.txt/sitemap.xml.
"""

from utils.i18n import resolve_i18n_field
from utils.sanitize import html_naar_platte_tekst

META_DESCRIPTION_MAX_LENGTH = 160

# Bloktypes waarvan de tekst geschikt is als meta-omschrijving (een lopende
# zin) - bv. niet 'stats' (losse cijfers) of 'image_gallery' (geen tekst).
_TEXT_BLOCK_EXTRACTORS = {
    "rich_text": lambda data, lang: html_naar_platte_tekst(resolve_i18n_field(data.get("html"), lang)),
    "quote": lambda data, lang: resolve_i18n_field(data.get("text"), lang),
}


def page_meta_description(page, lang, fallback):
    """Geeft een meta-omschrijving (max META_DESCRIPTION_MAX_LENGTH tekens,
    afgebroken op een woordgrens) op basis van het eerste geschikte
    tekstblok van 'page'. Valt terug op 'fallback' als de pagina geen
    bruikbaar tekstblok heeft (bv. enkel afbeeldingen)."""
    for block in page.blocks:
        extractor = _TEXT_BLOCK_EXTRACTORS.get(block.block_type)
        if extractor is None:
            continue
        text = (extractor(block.data, lang) or "").strip()
        if text:
            return _truncate(text)
    return fallback


def _truncate(text):
    if len(text) <= META_DESCRIPTION_MAX_LENGTH:
        return text
    return text[:META_DESCRIPTION_MAX_LENGTH].rsplit(" ", 1)[0] + "…"
