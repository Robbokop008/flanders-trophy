"""
routes/pages.py
-----------------
Publieke weergave van door de admin beheerde inhoudspagina's (zie models.Page).
Elke pagina heeft een uniek slug en wordt getoond via /pagina/<slug>, los van
waar ze in de navigatie hangt - verplaatsen in de navbar breekt dus geen link.
"""

from flask import Blueprint, render_template, abort

from extensions import db
from models import Page, PageBlock, HOME_PAGE_SLUG, PRIVACY_POLICY_SLUG

pages_bp = Blueprint("pages", __name__, url_prefix="/pagina")


def ensure_privacy_policy_page():
    """Maakt de privacybeleid-Page aan met placeholder-inhoud als ze nog niet
    bestaat (aangeroepen bij het opstarten - zie app.py). Bewust NIET
    gepubliceerd: de tekst bevat overal "[AAN TE VULLEN]"-placeholders voor
    gegevens die enkel de club zelf kan invullen (organisatienaam, adres,
    contactadres, bewaartermijnen, ...) - pas nadat een admin die aangevuld
    en zelf gepubliceerd heeft, mag de cookiebanner/Google Analytics
    (config.GOOGLE_ANALYTICS_ID) er ook effectief naar linken, zie
    templates/base.html."""
    if Page.query.filter_by(slug=PRIVACY_POLICY_SLUG).first() is not None:
        return

    page = Page(
        slug=PRIVACY_POLICY_SLUG,
        title="Privacy Policy",
        title_i18n={"en": "Privacy Policy"},
        is_published=False,
    )
    db.session.add(page)
    db.session.flush()

    def rich_text(html):
        return PageBlock(page_id=page.id, block_type="rich_text", position=len(page.blocks) + 1, data={"html": {"en": html}})

    db.session.add_all([
        rich_text(
            "<p><strong>Last updated: [AAN TE VULLEN: datum van publicatie]</strong></p>"
            "<p>This privacy policy explains how Flanders Trophy collects, uses and "
            "protects your personal data when you visit this website, use the contact "
            "form, or request an offer.</p>"
        ),
        rich_text(
            "<h2>Who is responsible for your data</h2>"
            "<p><strong>[AAN TE VULLEN: officiële naam van de organisatie]</strong><br>"
            "[AAN TE VULLEN: adres]<br>"
            "Email: [AAN TE VULLEN: contactadres voor privacyvragen]</p>"
        ),
        rich_text(
            "<h2>What data we collect</h2>"
            "<ul>"
            "<li><strong>Contact form:</strong> name, email address and the message you send us.</li>"
            "<li><strong>Offer request form:</strong> club name, country, contact person, "
            "email, phone number, team numbers and any other details you provide.</li>"
            "<li><strong>Language preference:</strong> stored in a functional session "
            "cookie only, no personal data.</li>"
            "<li><strong>Website usage (only if you accept cookies):</strong> pages "
            "visited, approximate location, device and browser type, collected through "
            "Google Analytics.</li>"
            "</ul>"
        ),
        rich_text(
            "<h2>Why we use this data</h2>"
            "<ul>"
            "<li>To answer your questions (contact form).</li>"
            "<li>To prepare and follow up on an offer for your club (offer request form).</li>"
            "<li>To understand how visitors use this website and improve it (Google "
            "Analytics, only with your consent).</li>"
            "</ul>"
        ),
        rich_text(
            "<h2>Cookies</h2>"
            "<table><thead><tr><th>Cookie</th><th>Purpose</th><th>Consent required</th></tr></thead>"
            "<tbody>"
            "<tr><td>session</td><td>Remembers your language choice and other essential "
            "site functionality.</td><td>No (strictly necessary)</td></tr>"
            "<tr><td>_ga, _ga_*</td><td>Google Analytics - measures website usage.</td><td>Yes</td></tr>"
            "</tbody></table>"
            "<p>You can change your cookie choice at any time via the \"Cookie settings\" "
            "link in the footer.</p>"
        ),
        rich_text(
            "<h2>Sharing your data</h2>"
            "<p>We only share your data with:</p>"
            "<ul>"
            "<li><strong>Google</strong> (Google Ireland Limited) - for sending emails via "
            "Gmail, and, if you accept cookies, for website analytics via Google Analytics.</li>"
            "<li>[AAN TE VULLEN: eventuele andere partijen waarmee gegevens gedeeld worden]</li>"
            "</ul>"
            "<p>We do not sell your data to third parties.</p>"
        ),
        rich_text(
            "<h2>How long we keep your data</h2>"
            "<p>[AAN TE VULLEN: bewaartermijn, bv. \"Offerteaanvragen en contactberichten "
            "worden X maanden na de betrokken editie bewaard.\" - vul een termijn in die "
            "overeenstemt met de werkelijke praktijk.]</p>"
        ),
        rich_text(
            "<h2>Your rights</h2>"
            "<p>Under the GDPR, you have the right to access, correct, delete or transfer "
            "your data, and to object to how it is used. To exercise these rights, contact "
            "us at [AAN TE VULLEN: contactadres voor privacyvragen].</p>"
            "<p>If you are not satisfied with our answer, you can file a complaint with the "
            "Belgian Data Protection Authority (Gegevensbeschermingsautoriteit), "
            "Drukpersstraat 35, 1000 Brussels - "
            "<a href=\"https://www.gegevensbeschermingsautoriteit.be\" target=\"_blank\" "
            "rel=\"noopener\">www.gegevensbeschermingsautoriteit.be</a>.</p>"
        ),
        rich_text(
            "<h2>Changes to this policy</h2>"
            "<p>We may update this privacy policy from time to time. The date at the top "
            "of this page shows when it was last changed.</p>"
        ),
    ])
    db.session.commit()


@pages_bp.route("/<slug>")
def view(slug):
    # De homepage-Page (zie routes/main.py _get_or_create_home_page) hoort
    # enkel op / getoond te worden, met haar eigen sjabloon - niet nog eens
    # via dit generieke /pagina/<slug>-pad.
    if slug == HOME_PAGE_SLUG:
        abort(404)
    page = Page.query.filter_by(slug=slug).first()
    if page is None or not page.is_published:
        abort(404)
    return render_template("pages/view.html", page=page)
