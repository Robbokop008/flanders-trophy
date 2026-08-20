"""
models.py
---------
Alle database-modellen, als SQLAlchemy ORM-klassen.

Dit is de generieke CMS-kern die overgenomen is van de hoofdclubsite:
- User: admin-authenticatie (geen publieke zelfregistratie op deze site).
- NavItem: de navbar als data (zelf-refererende boom).
- Page / PageBlock: door de admin opgebouwde inhoudspagina's.

Club-specifieke modellen (Team, NieuwsBericht, Evenement, Sponsor,
webshop, inschrijvingen, GDPR-verzoeken, ...) horen hier bewust niet bij -
dit is een scaffold voor de Flanders Trophy-toernooiwebsite, niet de club.
"""

from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


# ---------------------------------------------------------------------------
# Gebruikers
# ---------------------------------------------------------------------------

class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    membership_status = db.Column(db.String(30), default="Bronze", nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    def __repr__(self):
        return f"<User {self.username}>"


# ---------------------------------------------------------------------------
# Navigatie
# ---------------------------------------------------------------------------

NAV_ITEM_TYPES = ["category", "divider", "page", "route", "external"]


class NavItem(db.Model):
    """
    Eén item in de navbar. Zelf-refererende boom via parent_id:
    - "category": een dropdown-opener op het hoofdniveau (parent_id is None),
      heeft kinderen.
    - "divider": een niet-klikbaar groepslabel binnen een dropdown, geen
      link, geen kinderen.
    - "page": link naar een Page (page_id).
    - "route": link naar een vaste Flask-eindpunt-naam (route_endpoint),
      voor bestemmingen die code-gedreven blijven (bv. "main.contact").
    - "external": link naar een vrije URL (external_url).

    page_id is een echte foreign key (i.p.v. een losse tekst-slug): zo kan
    een Page niet verwijderd worden zolang er nog een NavItem naar verwijst
    (zie admin_required route delete_page) - een admin kan via de UI dus
    nooit een kapotte menu-link achterlaten.
    """
    __tablename__ = "nav_items"

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("nav_items.id"), nullable=True)
    label = db.Column(db.String(100), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    item_type = db.Column(db.String(20), nullable=False)

    page_id = db.Column(db.Integer, db.ForeignKey("pages.id"), nullable=True)
    route_endpoint = db.Column(db.String(150), nullable=True)
    external_url = db.Column(db.String(500), nullable=True)

    open_in_new_tab = db.Column(db.Boolean, nullable=False, default=False)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)

    children = db.relationship(
        "NavItem", backref=db.backref("parent", remote_side=[id]), order_by="NavItem.position"
    )
    page = db.relationship("Page")

    def __repr__(self):
        return f"<NavItem {self.label} ({self.item_type})>"


# ---------------------------------------------------------------------------
# Pagina's (CMS)
# ---------------------------------------------------------------------------

class Page(db.Model):
    """Een door de admin beheerde inhoudspagina, getoond via /pagina/<slug>.
    De inhoud zelf zit in PageBlock-rijen (zie hieronder); body_html is
    legacy (van vóór de blokken-page-builder) en wordt niet meer gebruikt
    door nieuwe/bewerkte pagina's."""
    __tablename__ = "pages"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body_html = db.Column(db.Text, nullable=False, default="")
    hero_image = db.Column(db.String(255))   # bestandsnaam in static/images/
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blocks = db.relationship(
        "PageBlock", order_by="PageBlock.position", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Page {self.slug}>"


PAGE_BLOCK_TYPES = [
    "rich_text", "image_gallery", "columns", "video", "button",
    "quote", "faq", "stats", "embed_html",
]


class PageBlock(db.Model):
    """Eén content-blok binnen een Page, getoond in volgorde van position.
    De vorm van 'data' hangt af van block_type - zie utils/page_blocks.py
    en de bloksjablonen in templates/pages/_blocks/ en
    templates/admin/page_block_form.html voor de exacte sleutels per type."""
    __tablename__ = "page_blocks"

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey("pages.id"), nullable=False)
    block_type = db.Column(db.String(20), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    data = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PageBlock {self.block_type} (page {self.page_id}, pos {self.position})>"
