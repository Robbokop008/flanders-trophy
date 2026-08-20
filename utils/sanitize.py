"""
utils/sanitize.py
-------------------
Saniteert rich-text HTML (van de pagina-editor) vóór opslag in de database.
Enkel admins kunnen pagina's schrijven, maar we filteren toch server-side
tegen stored-XSS - clientside filtering (de editor) is geen garantie.
"""

import re

import bleach

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s",
    "h2", "h3", "h4",
    "ul", "ol", "li",
    "a", "img",
    "blockquote",
    "table", "thead", "tbody", "tr", "th", "td",
    "iframe",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "target", "rel"],
    "img": ["src", "alt"],
    "td": ["data-row"],
    # Quill's video-embed (YouTube/Vimeo) rendert als <iframe class="ql-video" ...>
    "iframe": ["src", "class", "frameborder", "allowfullscreen", "width", "height"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(raw_html):
    """Geeft een veilige subset van de opgegeven HTML terug (lege string als raw_html leeg is)."""
    if not raw_html:
        return ""

    cleaned = bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return cleaned


# Blok-elementen die bij het platsstrijken naar platte tekst een spatie nodig
# hebben op de plek van hun sluit-tag, anders plakken bv. tabelcellen of
# opeenvolgende paragrafen zonder spatie aan elkaar.
_BLOK_SLUIT_TAGS = re.compile(
    r"</?(p|br|li|h2|h3|h4|blockquote|table|thead|tbody|tr|td|th|ul|ol)\s*/?>",
    re.IGNORECASE,
)
_WHITESPACE = re.compile(r"\s+")


def html_naar_platte_tekst(html):
    """Zet gesaniteerde rich-text HTML om naar leesbare platte tekst (voor previews/samenvattingen)."""
    if not html:
        return ""
    met_spaties = _BLOK_SLUIT_TAGS.sub(" ", html)
    zonder_tags = bleach.clean(met_spaties, tags=[], attributes={}, strip=True)
    return _WHITESPACE.sub(" ", zonder_tags).strip()
