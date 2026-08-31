"""
routes/main.py
---------------
Routes voor het publieke, informatieve deel van de site: home en contact.
"""

from flask import Blueprint, Response, render_template, request, current_app, session, redirect, url_for
from flask_babel import gettext as _
from sqlalchemy import text

from extensions import db, limiter
from models import SiteSettings, Page, PageBlock, HOME_PAGE_SLUG
from utils.i18n import auto_translate_i18n_field
from utils.mail import send_contact_mail

main_bp = Blueprint("main", __name__)

CONTACT_TOPICS = ["General questions", "Registration / Offers", "Referees", "Parade", "During tournament"]


def _get_or_create_home_page():
    """De homepage-tekst (tagline, kerncijfers, "Who can participate?",
    "Magical Moment") is een gewone Page met blokken, precies zoals elke
    andere CMS-pagina - enkel de hero (titel/knoppen), vlaggenrij en
    fotostrook blijven vast onderdeel van templates/index.html (geen
    passende bloktypes voor dat maatwerk-ontwerp). Zo staat de homepage
    gewoon tussen de andere pagina's in het adminpaneel en is alle tekst
    daar op dezelfde manier te bewerken.

    Wordt bij de eerste home-request aangemaakt met de oorspronkelijke
    ontwerptekst als startpunt - een admin past dat nadien vrij aan."""
    page = Page.query.filter_by(slug=HOME_PAGE_SLUG).first()
    if page is not None:
        return page

    page = Page(
        slug=HOME_PAGE_SLUG,
        title="Home",
        title_i18n={"en": "Home"},
        is_published=True,
    )
    db.session.add(page)
    db.session.flush()

    categorieen_url = url_for("pages.view", slug="categories")
    db.session.add_all([
        PageBlock(page_id=page.id, block_type="rich_text", position=1, data={
            "html": {"en": "<p>The biggest international handball tournament in the BeNeLux</p>"},
        }),
        PageBlock(page_id=page.id, block_type="stats", position=2, data={
            "items": [
                {"getal": "1.200+", "label": {"en": "participants every year"}},
                {"getal": "100+", "label": {"en": "teams competing"}},
                {"getal": "300+", "label": {"en": "matches played"}},
            ],
        }),
        PageBlock(page_id=page.id, block_type="rich_text", position=3, data={
            "html": {"en": (
                "<h2>Who can participate?</h2>"
                "<p>FHT is a tournament for Men and Women in the following categories: "
                "U15, U17, U20 and Seniors.</p>"
                f'<p><a href="{categorieen_url}">See all categories &rarr;</a></p>'
            )},
        }),
        PageBlock(page_id=page.id, block_type="rich_text", position=4, data={
            "html": {"en": (
                "<h2>Magical Moment</h2>"
                "<p>Since 2025, the FHT starts with a opening event and Flag Parade on Friday "
                "evening. During this Flag Parade, 1.000 handball players from across Europe "
                "gather to celebrate our sport!</p>"
            )},
        }),
    ])
    db.session.commit()
    return page


def _ensure_home_page_translated(page):
    """Vult ontbrekende NL/FR/DE-vertalingen van de homepage-blokken aan via
    DeepL (zelfde auto_translate_i18n_field als bij het opslaan van een
    gewoon blok in het adminpaneel - zie routes/admin.py). Bij een verse
    installatie staan de blokken hierboven enkel in het Engels; dit vult ze
    de eerste keer dat de homepage bezocht wordt aan tot alle 4 talen.
    Nadien is elk veld al gevuld, dus doet dit verder niets meer (geen
    herhaalde DeepL-aanroepen)."""
    changed = False
    for block in page.blocks:
        if block.block_type == "rich_text":
            html = block.data.get("html")
            if isinstance(html, dict):
                vertaald = auto_translate_i18n_field(html, html=True)
                if vertaald != html:
                    block.data = {**block.data, "html": vertaald}
                    changed = True
        elif block.block_type == "stats":
            items = block.data.get("items") or []
            nieuwe_items = []
            items_changed = False
            for item in items:
                label = item.get("label")
                if isinstance(label, dict):
                    vertaald_label = auto_translate_i18n_field(label)
                    if vertaald_label != label:
                        item = {**item, "label": vertaald_label}
                        items_changed = True
                nieuwe_items.append(item)
            if items_changed:
                block.data = {**block.data, "items": nieuwe_items}
                changed = True
    if changed:
        db.session.commit()


@main_bp.route("/")
def home():
    home_page = _get_or_create_home_page()
    _ensure_home_page_translated(home_page)
    return render_template("index.html", site_settings=SiteSettings.get(), home_page=home_page)


@main_bp.route("/health")
@limiter.exempt
def health():
    """Voor externe uptime-monitoring (bv. UptimeRobot/cron-job.org) - zie
    README.md. Vrijgesteld van de globale rate-limit omdat zo'n monitor er
    regelmatig op pingt."""
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as exc:
        current_app.logger.error(f"Health check faalde: {exc}")
        return {"status": "error"}, 503
    return {"status": "ok"}, 200


@main_bp.route("/robots.txt")
@limiter.exempt
def robots_txt():
    regels = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /login",
        "Disallow: /health",
        f"Sitemap: {url_for('main.sitemap_xml', _external=True)}",
    ]
    return Response("\n".join(regels) + "\n", mimetype="text/plain")


@main_bp.route("/sitemap.xml")
@limiter.exempt
def sitemap_xml():
    """Enkel gepubliceerde pagina's + de vaste publieke routes - geen
    /admin, /login of de taal-/health-/set-language-hulproutes. De homepage
    (slug 'home') staat al apart in VASTE_URLS via main.home; de generieke
    /pagina/<slug>-lus hieronder slaat die dus bewust over (zie ook
    routes/pages.view, dat /pagina/home zelf al 404 geeft)."""
    vaste_urls = [
        {"loc": url_for("main.home", _external=True), "lastmod": None, "priority": "1.0"},
        {"loc": url_for("main.contact", _external=True), "lastmod": None, "priority": "0.5"},
        {"loc": url_for("offers.request_offer", _external=True), "lastmod": None, "priority": "0.8"},
    ]
    pagina_urls = [
        {
            "loc": url_for("pages.view", slug=page.slug, _external=True),
            "lastmod": page.updated_at.strftime("%Y-%m-%d") if page.updated_at else None,
            "priority": "0.7",
        }
        for page in Page.query.filter(Page.is_published.is_(True), Page.slug != HOME_PAGE_SLUG).all()
    ]
    return Response(
        render_template("sitemap.xml", urls=vaste_urls + pagina_urls),
        mimetype="application/xml",
    )


@main_bp.route("/set-language/<lang_code>")
def set_language(lang_code):
    if lang_code in current_app.config["LANGUAGES"]:
        session["lang"] = lang_code

    next_url = request.args.get("next") or ""
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("main.home")
    return redirect(next_url)


@main_bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        topic = request.form.get("topic")
        topic = topic if topic in CONTACT_TOPICS else CONTACT_TOPICS[0]

        if not name or not email or not message or "@" not in email:
            return render_template(
                "contact.html", topics=CONTACT_TOPICS,
                error=_("Please fill in all fields correctly (with a valid email address)."),
                name=name, email=email, message=message, topic=topic,
            )

        try:
            send_contact_mail(name, email, message, topic=topic)
        except Exception as exc:
            # Mail-fout mag de gebruiker niet blokkeren, maar loggen we wel
            current_app.logger.error(f"Kon contactmail niet versturen: {exc}")

        return render_template("contact.html", topics=CONTACT_TOPICS, success=_("Your message has been sent successfully."))

    return render_template("contact.html", topics=CONTACT_TOPICS)
