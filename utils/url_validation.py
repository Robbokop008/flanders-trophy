"""
utils/url_validation.py
-------------------------
Validatie voor URL's die een admin invoert in de page-builder (knop-/
video-blokken). Enkel admins kunnen dit invullen, maar we vertrouwen die
invoer toch niet blindelings - een knop-URL belandt in een <a href>, en
een video-URL zou zonder validatie rechtstreeks in een iframe src kunnen
belanden.
"""

import re
from urllib.parse import urlsplit, parse_qs

_YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_VIMEO_ID = re.compile(r"^\d+$")


def is_safe_target_url(url):
    """True als url een veilig linkdoel is: een relatief pad (niet
    protocol-relatief, dus geen //evil.com) of een absolute http(s)-URL.
    Blokkeert bv. javascript:- en data:-URL's."""
    if not url:
        return False
    url = url.strip()
    if url.startswith("//"):
        return False
    if url.startswith("/"):
        return True
    parsed = urlsplit(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def parse_video_embed(url):
    """Herkent een YouTube- of Vimeo-URL en geeft (provider, embed_id) terug,
    of None als de URL niet herkend wordt. Enkel dit ID wordt opgeslagen -
    de canonieke embed-URL wordt pas bij het renderen opnieuw opgebouwd via
    build_video_embed_url(), nooit de ruwe admin-invoer rechtstreeks in een
    iframe src."""
    if not url:
        return None
    parsed = urlsplit(url.strip())
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    if host in ("youtube.com", "m.youtube.com", "youtube-nocookie.com"):
        video_id = None
        if parsed.path == "/watch":
            video_id = (parse_qs(parsed.query).get("v") or [None])[0]
        elif parsed.path.startswith("/embed/"):
            video_id = parsed.path[len("/embed/"):]
        if video_id and _YOUTUBE_ID.match(video_id):
            return ("youtube", video_id)
        return None

    if host == "youtu.be":
        video_id = parsed.path.lstrip("/")
        if video_id and _YOUTUBE_ID.match(video_id):
            return ("youtube", video_id)
        return None

    if host in ("vimeo.com", "player.vimeo.com"):
        segments = [s for s in parsed.path.split("/") if s]
        video_id = segments[-1] if segments else None
        if video_id and _VIMEO_ID.match(video_id):
            return ("vimeo", video_id)
        return None

    return None


def build_video_embed_url(provider, embed_id):
    """Bouwt de canonieke embed-URL server-side op uit een gevalideerd
    (provider, embed_id)-paar - zie parse_video_embed()."""
    if provider == "youtube":
        return f"https://www.youtube-nocookie.com/embed/{embed_id}"
    if provider == "vimeo":
        return f"https://player.vimeo.com/video/{embed_id}"
    return None
