"""
routes/pages.py
-----------------
Publieke weergave van door de admin beheerde inhoudspagina's (zie models.Page).
Elke pagina heeft een uniek slug en wordt getoond via /pagina/<slug>, los van
waar ze in de navigatie hangt - verplaatsen in de navbar breekt dus geen link.
"""

from flask import Blueprint, render_template, abort

from models import Page

pages_bp = Blueprint("pages", __name__, url_prefix="/pagina")


@pages_bp.route("/<slug>")
def view(slug):
    page = Page.query.filter_by(slug=slug).first()
    if page is None or not page.is_published:
        abort(404)
    return render_template("pages/view.html", page=page)
