"""
routes/admin.py
----------------
Adminpaneel: de generieke CMS - pagina's (opgebouwd uit blokken), navigatie
en een read-only gebruikerslijst. Overgenomen (en flink getrimd) van de
hoofdclubsite: dat adminpaneel beheert ook een webshop, nieuws, evenementen,
teams, sponsors en inschrijvingen - allemaal club-specifiek en dus hier niet
geport. Wat overblijft is de herbruikbare CMS-motor.
"""

import re
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, render_template, request, redirect, url_for, current_app, g, jsonify, abort
from werkzeug.utils import secure_filename

from werkzeug.routing import BuildError

from datetime import datetime

from extensions import db
from models import Page, PageBlock, PAGE_BLOCK_TYPES, NavItem, NAV_ITEM_TYPES, User, OfferRequest, SiteSettings, HOME_PAGE_SLUG
from utils.auth import admin_required
from utils.sanitize import sanitize_html
from utils.i18n import auto_translate_i18n_field
from utils.page_blocks import block_afbeeldingsbestanden, block_documentbestanden
from utils.url_validation import is_safe_target_url, parse_video_embed

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _save_uploaded_image(image_file):
    """Slaat een geüploade afbeelding op met een unieke bestandsnaam en geeft die naam terug
    (of None als er geen bestand is meegestuurd, of het geen toegelaten afbeeldingstype is)."""
    if not image_file or not image_file.filename:
        return None

    ext = Path(secure_filename(image_file.filename)).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return None

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4()}{ext}"
    image_file.save(upload_folder / filename)
    return filename


def _delete_uploaded_image(filename):
    """Verwijdert een eerder geüploade afbeelding van schijf. Genegeerd als
    filename leeg is of het bestand al niet (meer) bestaat - dit wordt
    aangeroepen telkens een afbeelding vervangen of een record met een
    afbeelding verwijderd wordt, zodat static/images/ niet blijft
    aangroeien met bestanden die nergens meer naar verwijzen."""
    if not filename:
        return
    path = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    try:
        path.unlink(missing_ok=True)
    except OSError:
        current_app.logger.warning(f"Kon geüploade afbeelding niet verwijderen: {filename}")


ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}


def _save_uploaded_document(document_file):
    """Zelfde als _save_uploaded_image hierboven, maar voor downloadbare
    documenten (PDF/Word/Excel/PowerPoint) in het "documents"-blok - eigen
    map (DOCUMENT_UPLOAD_FOLDER) en extensie-allowlist."""
    if not document_file or not document_file.filename:
        return None

    ext = Path(secure_filename(document_file.filename)).suffix.lower()
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        return None

    upload_folder = Path(current_app.config["DOCUMENT_UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4()}{ext}"
    document_file.save(upload_folder / filename)
    return filename


def _delete_uploaded_document(filename):
    """Verwijdert een eerder geüploed document van schijf. Zie
    _delete_uploaded_image hierboven - zelfde aanpak, andere map."""
    if not filename:
        return
    path = Path(current_app.config["DOCUMENT_UPLOAD_FOLDER"]) / filename
    try:
        path.unlink(missing_ok=True)
    except OSError:
        current_app.logger.warning(f"Kon geüpload document niet verwijderen: {filename}")


def _slugify(text):
    """Zet vrije tekst om in een URL-vriendelijke slug (kleine letters, koppeltekens)."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _parse_optioneel_positief_getal(value):
    """Parseert een optioneel getalveld: lege invoer -> None, geeft (waarde, fout) terug.
    Niet gebruikt door de huidige (getrimde) admin-secties, maar overgenomen als
    generieke helper voor als je later zelf een numeriek veld toevoegt."""
    value = (value or "").strip()
    if not value:
        return None, None
    try:
        getal = int(value)
    except ValueError:
        return None, "Vul een geheel getal in (of laat leeg)."
    if getal < 0:
        return None, "Vul een getal van 0 of hoger in."
    return getal, None


def _parse_datetime_local(value):
    """Parseert de waarde van een <input type="datetime-local"> (bv. '2026-08-08T14:30'),
    geeft None terug als de waarde leeg of ongeldig is."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def _parse_date(value):
    """Parseert de waarde van een <input type="date"> (bv. '2026-10-12'),
    geeft None terug als de waarde leeg of ongeldig is."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _html_is_blank(html):
    """True als deze rich-text HTML geen zichtbare tekst of afbeelding bevat
    (Quill stuurt een lege editor als '<p><br></p>', niet als lege string)."""
    text = re.sub(r"<[^>]+>", "", html or "").strip()
    return not text and "<img" not in (html or "")


PAGE_BLOCK_TYPE_LABELS = {
    "rich_text": "Tekstblok",
    "image_gallery": "Afbeelding(en)",
    "columns": "Kolommen",
    "video": "Video",
    "button": "Knop",
    "quote": "Citaat",
    "faq": "Veelgestelde vragen",
    "stats": "Statistieken",
    "embed_html": "HTML/embed",
    "documents": "Downloads / documenten",
}


def _next_block_position(page_id):
    max_position = db.session.query(db.func.max(PageBlock.position)).filter_by(page_id=page_id).scalar() or 0
    return max_position + 1


def _parse_weergave_fields():
    """Leest de gedeelde 'Weergave'-velden (uitlijning/achtergrond/breedte/
    witruimte) die op élk blokformulier staan - zie utils.page_blocks.
    STYLE_DEFAULTS voor de toegelaten waarden. Heet bewust 'weergave' i.p.v.
    'style' als data-sleutel, want het knop-blok gebruikt 'style' al voor
    zijn eigen kleur (primary/secondary)."""
    align = request.form.get("weergave_align")
    background = request.form.get("weergave_background")
    width = request.form.get("weergave_width")
    spacing = request.form.get("weergave_spacing")
    return {
        "align": align if align in ("left", "center", "right") else "left",
        "background": background if background in ("none", "licht", "blauw", "donker") else "none",
        "width": width if width in ("smal", "normaal", "breed") else "normaal",
        "spacing": spacing if spacing in ("compact", "normaal", "ruim") else "normaal",
    }


def _parse_i18n_field(field_prefix):
    """Leest een per-taal veld uit request.form: {"en": ..., "nl": ..., ...},
    één invoerveld per taal met naam '<field_prefix>_<taalcode>'. Gebruikt
    door elk bloktype met vertaalbare tekst (rich_text, button, quote, faq,
    stats) - zie templates/admin/page_block_form.html voor de bijhorende
    velden, en utils/i18n.resolve_i18n_field() voor hoe zo'n dict bij het
    weergeven weer met terugval naar Engels wordt uitgelezen."""
    return {
        lang: (request.form.get(f"{field_prefix}_{lang}") or "").strip()
        for lang in current_app.config["LANGUAGES"]
    }


def _parse_block_form(block_type, existing_data):
    """Leest request.form/request.files uit voor het gegeven bloktype en
    geeft (data, error) terug. existing_data is de huidige block.data bij
    bewerken (leeg dict bij toevoegen) - nodig om bestaande afbeeldingen/
    kolommen te kunnen behouden, vervangen of verwijderen. Ruimt zelf oude
    afbeeldingsbestanden op die vervangen/verwijderd worden (zelfde patroon
    als _delete_uploaded_image elders in dit bestand). Voegt de gedeelde
    'weergave'-stijlvelden toe aan het resultaat, ongeacht bloktype."""
    existing_data = existing_data or {}
    data = {}
    error = None

    if block_type == "rich_text":
        html = {
            lang: sanitize_html(request.form.get(f"html_{lang}") or "")
            for lang in current_app.config["LANGUAGES"]
        }
        # sanitize_html ook op de door DeepL aangevulde talen: die zouden
        # geen onveilige tags mogen bevatten (DeepL bewaart enkel de tags uit
        # de brontekst), maar dit is defense-in-depth, geen vertrouwen op DeepL.
        html = {
            lang: sanitize_html(v)
            for lang, v in auto_translate_i18n_field(html, html=True, existing=existing_data.get("html")).items()
        }
        data = {"html": html}

    elif block_type == "image_gallery":
        images = []
        bestaande = existing_data.get("images", [])
        for i, img in enumerate(bestaande):
            if request.form.get(f"remove_image_{i}"):
                _delete_uploaded_image(img.get("filename"))
                continue
            alt = (request.form.get(f"alt_{i}") or "").strip()
            images.append({"filename": img.get("filename"), "alt": alt})
        for bestand in request.files.getlist("new_images"):
            filename = _save_uploaded_image(bestand)
            if filename:
                images.append({"filename": filename, "alt": ""})
        data = {"images": images}

    elif block_type == "columns":
        try:
            aantal = int(request.form.get("column_count") or 2)
        except ValueError:
            aantal = 2
        aantal = min(max(aantal, 2), 4)

        bestaande = existing_data.get("columns", [])
        columns = []
        for i in range(aantal):
            oude_kolom = bestaande[i] if i < len(bestaande) else {}
            heading = auto_translate_i18n_field(_parse_i18n_field(f"heading_{i}"), existing=oude_kolom.get("heading"))
            text = auto_translate_i18n_field(_parse_i18n_field(f"text_{i}"), existing=oude_kolom.get("text"))
            oude_afbeelding = bestaande[i].get("image") if i < len(bestaande) else None
            nieuwe_afbeelding = _save_uploaded_image(request.files.get(f"image_{i}"))
            if nieuwe_afbeelding:
                _delete_uploaded_image(oude_afbeelding)
                afbeelding = nieuwe_afbeelding
            elif request.form.get(f"remove_image_{i}"):
                _delete_uploaded_image(oude_afbeelding)
                afbeelding = None
            else:
                afbeelding = oude_afbeelding
            columns.append({"heading": heading, "text": text, "image": afbeelding})

        # Bij het verkleinen van het aantal kolommen: afbeeldingen van de
        # kolommen die wegvallen niet laten rondslingeren op schijf.
        for oude_kolom in bestaande[aantal:]:
            _delete_uploaded_image(oude_kolom.get("image"))

        data = {"columns": columns}

    elif block_type == "video":
        url = (request.form.get("url") or "").strip()
        embed = parse_video_embed(url)
        if embed is None:
            data, error = {"url": url}, "Geen geldige YouTube- of Vimeo-URL herkend."
        else:
            provider, embed_id = embed
            data = {"provider": provider, "embed_id": embed_id, "source_url": url}

    elif block_type == "button":
        label = _parse_i18n_field("label")
        url = (request.form.get("url") or "").strip()
        stijl = request.form.get("style") if request.form.get("style") in ("primary", "secondary") else "primary"
        if not any(label.values()):
            error = "Vul de knoptekst in voor minstens één taal (de andere talen worden automatisch vertaald)."
        elif not is_safe_target_url(url):
            error = "Ongeldige URL. Gebruik een pad dat begint met '/', of een volledige http(s)-URL."
        label = auto_translate_i18n_field(label, existing=existing_data.get("label"))
        data = {"label": label, "url": url, "style": stijl}

    elif block_type == "quote":
        text = auto_translate_i18n_field(_parse_i18n_field("text"), existing=existing_data.get("text"))
        auteur = auto_translate_i18n_field(_parse_i18n_field("auteur"), existing=existing_data.get("auteur"))
        data = {"text": text, "auteur": auteur}

    elif block_type == "faq":
        # Geen vast maximum: de admin-UI voegt vraag/antwoord-velden dynamisch
        # toe (zie de "+ Vraag toevoegen"-knop in page_block_form.html) i.p.v.
        # een vaste reeks van 1 t.e.m. N velden te tonen, dus lezen we hier
        # gewoon alle vraag_<i>_<taal>/antwoord_<i>_<taal>-velden die
        # effectief meegestuurd zijn, ongeacht hun indexen (die hoeven niet
        # aaneensluitend te zijn).
        indices = set()
        for key in request.form:
            match = re.match(r"^(?:vraag|antwoord)_(\d+)_\w+$", key)
            if match:
                indices.add(int(match.group(1)))
        bestaande = existing_data.get("items", [])
        items = []
        for i in sorted(indices):
            oud_item = bestaande[i] if i < len(bestaande) else {}
            vraag = _parse_i18n_field(f"vraag_{i}")
            antwoord = _parse_i18n_field(f"antwoord_{i}")
            if any(vraag.values()) or any(antwoord.values()):
                items.append({
                    "vraag": auto_translate_i18n_field(vraag, existing=oud_item.get("vraag")),
                    "antwoord": auto_translate_i18n_field(antwoord, existing=oud_item.get("antwoord")),
                })
        data = {"items": items}

    elif block_type == "stats":
        # Zelfde aanpak als faq hierboven: geen vast maximum, gewoon alle
        # ingediende getal_<i>/stat_label_<i>_<taal>-indexen inlezen.
        indices = set()
        for key in request.form:
            match = re.match(r"^(?:getal|stat_label)_(\d+)(?:_\w+)?$", key)
            if match:
                indices.add(int(match.group(1)))
        bestaande = existing_data.get("items", [])
        items = []
        for i in sorted(indices):
            oud_item = bestaande[i] if i < len(bestaande) else {}
            getal = (request.form.get(f"getal_{i}") or "").strip()
            label = _parse_i18n_field(f"stat_label_{i}")
            if getal or any(label.values()):
                items.append({"getal": getal, "label": auto_translate_i18n_field(label, existing=oud_item.get("label"))})
        data = {"items": items}

    elif block_type == "embed_html":
        html = sanitize_html(request.form.get("html") or "")
        data = {"html": html}

    elif block_type == "documents":
        # Zelfde dynamische-indices-aanpak als faq/stats hierboven, maar dan
        # met een bestand per item (nieuw uploaden, vervangen of behouden -
        # zelfde patroon als image_gallery/columns) i.p.v. enkel tekstvelden.
        # Indices komen zowel uit de labelvelden als uit de file-inputs, want
        # een net toegevoegd item heeft bij de eerste keer opslaan wel al een
        # bestand maar mogelijk nog geen (ingevuld) label.
        bestaande = existing_data.get("items", [])
        indices = set()
        for key in request.form:
            match = re.match(r"^(?:doc_label_|doc_remove_)(\d+)(?:_\w+)?$", key)
            if match:
                indices.add(int(match.group(1)))
        for key in request.files:
            match = re.match(r"^doc_file_(\d+)$", key)
            if match:
                indices.add(int(match.group(1)))

        items = []
        for i in sorted(indices):
            oud_bestand = bestaande[i].get("filename") if i < len(bestaande) else None
            if request.form.get(f"doc_remove_{i}"):
                _delete_uploaded_document(oud_bestand)
                continue

            oud_label = bestaande[i].get("label") if i < len(bestaande) else None
            label = auto_translate_i18n_field(_parse_i18n_field(f"doc_label_{i}"), existing=oud_label)
            nieuw_bestand = _save_uploaded_document(request.files.get(f"doc_file_{i}"))
            if nieuw_bestand:
                _delete_uploaded_document(oud_bestand)
                filename = nieuw_bestand
            else:
                filename = oud_bestand

            if filename:
                items.append({"filename": filename, "label": label})
        data = {"items": items}

    else:
        return {}, "Onbekend bloktype."

    data["weergave"] = _parse_weergave_fields()
    return data, error


@admin_bp.route("/")
@admin_required
def dashboard():
    return render_template(
        "admin/dashboard.html", user=g.user,
        page_count=Page.query.count(), published_page_count=Page.query.filter_by(is_published=True).count(),
        user_count=User.query.count(),
        offer_request_count=OfferRequest.query.count(),
        new_offer_request_count=OfferRequest.query.filter_by(is_handled=False).count(),
    )


@admin_bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.username).all()
    return render_template("admin/users_list.html", user=g.user, users=all_users)


# ---------------------------------------------------------------------------
# Home-pagina instellingen
# ---------------------------------------------------------------------------

@admin_bp.route("/home-settings", methods=["GET", "POST"])
@admin_required
def home_settings():
    settings = SiteSettings.get()
    error = None

    if request.method == "POST":
        instagram_url = (request.form.get("instagram_url") or "").strip()
        facebook_url = (request.form.get("facebook_url") or "").strip()

        if instagram_url and not is_safe_target_url(instagram_url):
            error = "Ongeldige Instagram-link."
        elif facebook_url and not is_safe_target_url(facebook_url):
            error = "Ongeldige Facebook-link."
        else:
            settings.instagram_url = instagram_url or None
            settings.facebook_url = facebook_url or None

            for field in ("photo_1", "photo_2", "photo_3"):
                if request.form.get(f"{field}_remove"):
                    _delete_uploaded_image(getattr(settings, field))
                    setattr(settings, field, None)
                new_photo = _save_uploaded_image(request.files.get(field))
                if new_photo:
                    _delete_uploaded_image(getattr(settings, field))
                    setattr(settings, field, new_photo)

            db.session.commit()
            return redirect(url_for("admin.home_settings"))

    return render_template("admin/home_settings.html", user=g.user, settings=settings, error=error)


# ---------------------------------------------------------------------------
# Pagina's
# ---------------------------------------------------------------------------

@admin_bp.route("/pages")
@admin_required
def pages():
    alle_pagina_s = Page.query.order_by(Page.title).all()
    return render_template("admin/pages_list.html", user=g.user, pages=alle_pagina_s)


@admin_bp.route("/pages/<int:page_id>/preview")
@admin_required
def preview_page(page_id):
    """Toont de pagina precies zoals bezoekers ze zouden zien, ongeacht
    is_published - voor de live-preview-iframe in het bewerkscherm. In
    tegenstelling tot pages.view (de publieke route) is dit enkel voor
    ingelogde admins bereikbaar."""
    page = Page.query.get(page_id)
    if page is None:
        abort(404)
    return render_template("pages/view.html", page=page)


@admin_bp.route("/pages/upload-image", methods=["POST"])
@admin_required
def upload_page_image():
    """Afbeelding-upload voor de rich-text editor: slaat het bestand op en
    geeft de URL terug zodat de editor die inline kan invoegen (in plaats
    van de afbeelding als base64 in de opgeslagen HTML te embedden)."""
    filename = _save_uploaded_image(request.files.get("image"))
    if filename is None:
        return jsonify({"error": "Geen geldige afbeelding ontvangen."}), 400
    return jsonify({"url": url_for("static", filename=f"images/{filename}")})


@admin_bp.route("/pages/add", methods=["GET", "POST"])
@admin_required
def add_page():
    if request.method == "GET":
        return render_template("admin/page_form.html", user=g.user)

    title_i18n = _parse_i18n_field("title")
    slug = _slugify(request.form.get("slug") or title_i18n.get("nl") or title_i18n.get("en") or "")
    is_published = bool(request.form.get("is_published"))
    hero_image = _save_uploaded_image(request.files.get("hero_image"))

    error = None
    if not any(title_i18n.values()):
        error = "Titel is verplicht in minstens één taal."
    elif not slug:
        error = "Slug is verplicht."
    elif Page.query.filter_by(slug=slug).first() is not None:
        error = f"Er bestaat al een pagina met slug '{slug}'. Kies een andere titel of slug."

    if error:
        # hero_image werd hierboven al opgeslagen (indien meegestuurd) vóór
        # deze validatie - zonder opruimen zou dat bestand nergens meer naar
        # verwijzen als de pagina nu niet aangemaakt wordt.
        _delete_uploaded_image(hero_image)
        return render_template(
            "admin/page_form.html", user=g.user, error=error,
            form_title=title_i18n, form_slug=slug, form_is_published=is_published,
        )

    title_i18n = auto_translate_i18n_field(title_i18n)
    title = title_i18n.get("nl") or title_i18n.get("en") or next((v for v in title_i18n.values() if v), "")
    page = Page(title=title, title_i18n=title_i18n, slug=slug, hero_image=hero_image, is_published=is_published)
    db.session.add(page)
    db.session.commit()
    # Meteen doorrollen naar het bewerkscherm: een pagina zonder inhoud
    # heeft weinig nut, en dit is waar die inhoud voortaan opgebouwd wordt.
    return redirect(url_for("admin.edit_page", page_id=page.id))


def _render_page_edit(page, **kwargs):
    return render_template(
        "admin/page_canvas.html", user=g.user, page=page,
        block_types=PAGE_BLOCK_TYPES, block_type_labels=PAGE_BLOCK_TYPE_LABELS,
        **kwargs,
    )


@admin_bp.route("/pages/<int:page_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_page(page_id):
    page = Page.query.get(page_id)
    if page is None:
        return redirect(url_for("admin.pages"))

    if request.method == "GET":
        return _render_page_edit(page)

    title_i18n = _parse_i18n_field("title")
    slug = HOME_PAGE_SLUG if page.slug == HOME_PAGE_SLUG else _slugify(request.form.get("slug") or title_i18n.get("nl") or title_i18n.get("en") or "")
    # De homepage staat altijd op / (main.home negeert is_published) - het
    # publiceren-vinkje wordt voor die pagina niet eens getoond (zie
    # page_canvas.html), dus altijd True i.p.v. het (afwezige) formveld.
    is_published = True if page.slug == HOME_PAGE_SLUG else bool(request.form.get("is_published"))

    error = None
    if not any(title_i18n.values()):
        error = "Titel is verplicht in minstens één taal."
    elif not slug:
        error = "Slug is verplicht."
    elif Page.query.filter(Page.slug == slug, Page.id != page.id).first() is not None:
        error = f"Er bestaat al een andere pagina met slug '{slug}'. Kies een andere titel of slug."

    if error:
        return _render_page_edit(page, error=error, form_title=title_i18n, form_slug=slug, form_is_published=is_published)

    title_i18n = auto_translate_i18n_field(title_i18n, existing=page.title_i18n)
    page.title = title_i18n.get("nl") or title_i18n.get("en") or next((v for v in title_i18n.values() if v), "")
    page.title_i18n = title_i18n
    page.slug = slug
    page.is_published = is_published

    new_image = _save_uploaded_image(request.files.get("hero_image"))
    if new_image:
        _delete_uploaded_image(page.hero_image)
        page.hero_image = new_image

    db.session.commit()
    return redirect(url_for("admin.edit_page", page_id=page.id))


@admin_bp.route("/pages/<int:page_id>/toggle_published", methods=["POST"])
@admin_required
def toggle_page_published(page_id):
    page = Page.query.get(page_id)
    if page is not None and page.slug != HOME_PAGE_SLUG:
        page.is_published = not page.is_published
        db.session.commit()
    return redirect(url_for("admin.pages"))


@admin_bp.route("/pages/<int:page_id>/delete", methods=["POST"])
@admin_required
def delete_page(page_id):
    page = Page.query.get(page_id)
    if page is None:
        return redirect(url_for("admin.pages"))

    if page.slug == HOME_PAGE_SLUG:
        alle_pagina_s = Page.query.order_by(Page.title).all()
        return render_template(
            "admin/pages_list.html", user=g.user, pages=alle_pagina_s,
            error="De homepage kan niet verwijderd worden - pas ze aan via de blokken, of ontkoppel ze niet van slug 'home'.",
        )

    linking_items = NavItem.query.filter_by(page_id=page_id).all()
    if linking_items:
        labels = ", ".join(f"'{i.label}'" for i in linking_items)
        error = (
            f"Deze pagina kan niet verwijderd worden: de navigatie verwijst er nog naar "
            f"via {labels}. Verwijder of wijzig eerst dat navigatie-item op de "
            f"Navigatie-pagina, dan kan de pagina hierna wel verwijderd worden."
        )
        alle_pagina_s = Page.query.order_by(Page.title).all()
        return render_template("admin/pages_list.html", user=g.user, pages=alle_pagina_s, error=error)

    for block in page.blocks:
        for filename in block_afbeeldingsbestanden(block):
            _delete_uploaded_image(filename)
        for filename in block_documentbestanden(block):
            _delete_uploaded_document(filename)
    _delete_uploaded_image(page.hero_image)
    db.session.delete(page)   # cascadeert naar PageBlock-rijen (Page.blocks-relationship)
    db.session.commit()
    return redirect(url_for("admin.pages"))


@admin_bp.route("/pages/<int:page_id>/blocks/add/<block_type>", methods=["GET", "POST"])
@admin_required
def add_page_block(page_id, block_type):
    page = Page.query.get(page_id)
    if page is None or block_type not in PAGE_BLOCK_TYPES:
        abort(404)

    if request.method == "GET":
        return render_template(
            "admin/page_block_form.html", user=g.user, page=page, block=None,
            block_type=block_type, block_type_label=PAGE_BLOCK_TYPE_LABELS[block_type],
        )

    data, error = _parse_block_form(block_type, {})
    if error:
        return render_template(
            "admin/page_block_form.html", user=g.user, page=page, block=None,
            block_type=block_type, block_type_label=PAGE_BLOCK_TYPE_LABELS[block_type],
            error=error, form_data=data,
        )

    blok = PageBlock(page_id=page.id, block_type=block_type, position=_next_block_position(page.id), data=data)
    db.session.add(blok)
    db.session.commit()
    return redirect(url_for("admin.edit_page", page_id=page.id))


@admin_bp.route("/pages/<int:page_id>/blocks/<int:block_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_page_block(page_id, block_id):
    page = Page.query.get(page_id)
    block = PageBlock.query.get(block_id)
    if page is None or block is None or block.page_id != page.id:
        abort(404)

    if request.method == "GET":
        return render_template(
            "admin/page_block_form.html", user=g.user, page=page, block=block,
            block_type=block.block_type, block_type_label=PAGE_BLOCK_TYPE_LABELS[block.block_type],
        )

    data, error = _parse_block_form(block.block_type, block.data)
    if error:
        return render_template(
            "admin/page_block_form.html", user=g.user, page=page, block=block,
            block_type=block.block_type, block_type_label=PAGE_BLOCK_TYPE_LABELS[block.block_type],
            error=error, form_data=data,
        )

    block.data = data
    db.session.commit()
    return redirect(url_for("admin.edit_page", page_id=page.id))


@admin_bp.route("/pages/<int:page_id>/blocks/<int:block_id>/delete", methods=["POST"])
@admin_required
def delete_page_block(page_id, block_id):
    block = PageBlock.query.get(block_id)
    if block is not None and block.page_id == page_id:
        for filename in block_afbeeldingsbestanden(block):
            _delete_uploaded_image(filename)
        for filename in block_documentbestanden(block):
            _delete_uploaded_document(filename)
        db.session.delete(block)
        db.session.commit()
    return redirect(url_for("admin.edit_page", page_id=page_id))


@admin_bp.route("/pages/<int:page_id>/blocks/reorder", methods=["POST"])
@admin_required
def reorder_page_blocks(page_id):
    """AJAX-endpoint voor het slepen (SortableJS) in de blokken-builder,
    zelfde patroon als reorder_nav_items() maar dan voor een platte lijst
    blokken die bij één specifieke pagina horen."""
    data = request.get_json(silent=True) or {}
    updates = data.get("items") or []

    for update in updates:
        block = PageBlock.query.get(update.get("id"))
        if block is None or block.page_id != page_id:
            continue
        block.position = update.get("position", block.position)

    db.session.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Navigatie
# ---------------------------------------------------------------------------

def _collect_descendant_ids(item_id):
    """Verzamelt recursief alle id's van kinderen (en kleinkinderen, ...) van een navitem."""
    ids = []
    for child in NavItem.query.filter_by(parent_id=item_id).all():
        ids.append(child.id)
        ids.extend(_collect_descendant_ids(child.id))
    return ids


def _validate_nav_target(item_type, page_id, route_endpoint, external_url):
    """Geeft een foutmelding terug als het gekozen doel voor dit type ongeldig is, anders None."""
    if item_type in ("category", "divider"):
        return None
    if item_type == "page":
        if not page_id or Page.query.get(page_id) is None:
            return "Kies een geldige pagina."
        return None
    if item_type == "route":
        if not route_endpoint:
            return "Geef een route-eindpunt op (bv. 'main.contact')."
        try:
            url_for(route_endpoint)
        except BuildError:
            return f"Route-eindpunt '{route_endpoint}' bestaat niet of vereist parameters die hier niet ingevuld kunnen worden."
        return None
    if item_type == "external":
        if not external_url:
            return "Geef een externe URL op."
        return None
    return "Ongeldig type."


def _nav_admin_context(error=None):
    top_items = NavItem.query.filter_by(parent_id=None).order_by(NavItem.position).all()
    categories = [i for i in top_items if i.item_type == "category"]
    all_pages = Page.query.order_by(Page.title).all()
    return dict(
        user=g.user, top_items=top_items, categories=categories,
        all_pages=all_pages, error=error,
    )


def _nav_redirect(item_id=None):
    """Redirect naar het navigatie-overzicht, met een anker naar het betrokken
    item zodat de pagina na de herlaad automatisch terug naar dat item scrolt
    (i.p.v. telkens bovenaan te beginnen, wat bij items diep in een lange
    lijst voelt alsof een knop niks deed)."""
    url = url_for("admin.navigation")
    if item_id is not None:
        url += f"#nav-item-{item_id}"
    return redirect(url)


@admin_bp.route("/navigation")
@admin_required
def navigation():
    return render_template("admin/navigation.html", **_nav_admin_context())


@admin_bp.route("/navigation/add", methods=["POST"])
@admin_required
def add_nav_item():
    label = (request.form.get("label") or "").strip()
    item_type = request.form.get("item_type") or ""
    parent_id = request.form.get("parent_id") or None
    parent_id = int(parent_id) if parent_id else None
    page_id = request.form.get("page_id") or None
    page_id = int(page_id) if page_id else None
    route_endpoint = (request.form.get("route_endpoint") or "").strip() or None
    external_url = (request.form.get("external_url") or "").strip() or None
    open_in_new_tab = bool(request.form.get("open_in_new_tab"))

    error = None
    if not label:
        error = "Label is verplicht."
    elif item_type not in NAV_ITEM_TYPES:
        error = "Ongeldig type."
    elif item_type == "category" and parent_id is not None:
        error = "Een categorie kan enkel op het hoofdniveau staan."
    else:
        error = _validate_nav_target(item_type, page_id, route_endpoint, external_url)

    if error:
        return render_template("admin/navigation.html", **_nav_admin_context(error=error))

    max_position = db.session.query(db.func.max(NavItem.position)).filter_by(parent_id=parent_id).scalar() or 0
    item = NavItem(
        label=label, item_type=item_type, parent_id=parent_id,
        page_id=page_id if item_type == "page" else None,
        route_endpoint=route_endpoint if item_type == "route" else None,
        external_url=external_url if item_type == "external" else None,
        open_in_new_tab=open_in_new_tab, position=max_position + 1,
    )
    db.session.add(item)
    db.session.commit()
    return _nav_redirect(item.id)


@admin_bp.route("/navigation/<int:item_id>/edit", methods=["POST"])
@admin_required
def edit_nav_item(item_id):
    item = NavItem.query.get(item_id)
    if item is None:
        return redirect(url_for("admin.navigation"))

    label = (request.form.get("label") or "").strip()
    page_id = request.form.get("page_id") or None
    page_id = int(page_id) if page_id else None
    route_endpoint = (request.form.get("route_endpoint") or "").strip() or None
    external_url = (request.form.get("external_url") or "").strip() or None
    open_in_new_tab = bool(request.form.get("open_in_new_tab"))
    is_visible = bool(request.form.get("is_visible"))

    error = None
    if not label:
        error = "Label is verplicht."
    else:
        error = _validate_nav_target(item.item_type, page_id, route_endpoint, external_url)

    if error:
        return render_template("admin/navigation.html", **_nav_admin_context(error=error))

    item.label = label
    if item.item_type == "page":
        item.page_id = page_id
    elif item.item_type == "route":
        item.route_endpoint = route_endpoint
    elif item.item_type == "external":
        item.external_url = external_url
    item.open_in_new_tab = open_in_new_tab
    item.is_visible = is_visible
    db.session.commit()
    return _nav_redirect(item.id)


@admin_bp.route("/navigation/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_nav_item(item_id):
    item = NavItem.query.get(item_id)
    if item is not None:
        # SQLite handhaaft hier geen foreign keys - kinderen expliciet mee
        # verwijderen i.p.v. op een databank-cascade te vertrouwen.
        descendant_ids = _collect_descendant_ids(item_id)
        if descendant_ids:
            NavItem.query.filter(NavItem.id.in_(descendant_ids)).delete(synchronize_session=False)
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for("admin.navigation"))


@admin_bp.route("/navigation/<int:item_id>/move", methods=["POST"])
@admin_required
def move_nav_item(item_id):
    """Wisselt de positie van dit item met de vorige/volgende sibling (zelfde parent)."""
    item = NavItem.query.get(item_id)
    if item is None:
        return redirect(url_for("admin.navigation"))

    direction = request.form.get("direction")
    siblings = NavItem.query.filter_by(parent_id=item.parent_id).order_by(NavItem.position).all()
    index = next((i for i, s in enumerate(siblings) if s.id == item.id), None)

    if index is not None:
        swap_index = index - 1 if direction == "up" else index + 1
        if 0 <= swap_index < len(siblings):
            other = siblings[swap_index]
            item.position, other.position = other.position, item.position
            db.session.commit()

    return _nav_redirect(item.id)


@admin_bp.route("/navigation/<int:item_id>/move_to_parent", methods=["POST"])
@admin_required
def move_nav_item_to_parent(item_id):
    """Verplaatst dit item naar een andere categorie (of naar het hoofdniveau)."""
    item = NavItem.query.get(item_id)
    if item is None or item.item_type == "category":
        return redirect(url_for("admin.navigation"))

    new_parent_id = request.form.get("parent_id") or None
    new_parent_id = int(new_parent_id) if new_parent_id else None

    if new_parent_id is not None:
        new_parent = NavItem.query.get(new_parent_id)
        if new_parent is None or new_parent.item_type != "category":
            return redirect(url_for("admin.navigation"))

    max_position = db.session.query(db.func.max(NavItem.position)).filter_by(parent_id=new_parent_id).scalar() or 0
    item.parent_id = new_parent_id
    item.position = max_position + 1
    db.session.commit()
    return _nav_redirect(item.id)


@admin_bp.route("/navigation/reorder", methods=["POST"])
@admin_required
def reorder_nav_items():
    """AJAX-endpoint voor het slepen (SortableJS) in de navigatiebeheer-UI.
    Verwacht JSON: {"items": [{"id": int, "parent_id": int|null, "position": int}, ...]}"""
    data = request.get_json(silent=True) or {}
    updates = data.get("items") or []

    category_ids = {i.id for i in NavItem.query.filter_by(item_type="category").all()}

    for update in updates:
        item = NavItem.query.get(update.get("id"))
        if item is None:
            continue
        new_parent_id = update.get("parent_id")
        # Een categorie mag enkel op het hoofdniveau blijven staan.
        if item.item_type == "category" and new_parent_id is not None:
            continue
        # Enkel een bestaande categorie (of het hoofdniveau) is een geldige parent.
        if new_parent_id is not None and new_parent_id not in category_ids:
            continue
        item.parent_id = new_parent_id
        item.position = update.get("position", item.position)

    db.session.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Offerteaanvragen
# ---------------------------------------------------------------------------

@admin_bp.route("/offer-requests")
@admin_required
def offer_requests():
    show_handled = request.args.get("show_handled") == "1"
    query = OfferRequest.query.order_by(OfferRequest.created_at.desc())
    if not show_handled:
        query = query.filter_by(is_handled=False)
    return render_template(
        "admin/offer_requests_list.html", user=g.user,
        offer_requests=query.all(), show_handled=show_handled,
        new_count=OfferRequest.query.filter_by(is_handled=False).count(),
    )


@admin_bp.route("/offer-requests/<int:offer_request_id>/toggle_handled", methods=["POST"])
@admin_required
def toggle_offer_request_handled(offer_request_id):
    offer_request = OfferRequest.query.get(offer_request_id)
    if offer_request is not None:
        offer_request.is_handled = not offer_request.is_handled
        db.session.commit()
    return redirect(url_for("admin.offer_requests", show_handled=request.args.get("show_handled")))
