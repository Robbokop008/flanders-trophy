"""
utils/page_blocks.py
----------------------
Kleine helper, gebruikt door routes/admin.py (opruimen bij bewerken/
verwijderen van een blok), die alle afbeeldingsbestanden teruggeeft die
een PageBlock gebruikt - los van hoe dat per block_type in 'data' zit
opgeslagen.
"""


def afbeeldingen_uit_data(block_type, data):
    """Geeft een lijst bestandsnamen (in static/images/) terug die in deze
    'data'-dict van een blok van dit type gebruikt worden. Los van een
    concreet PageBlock-object bruikbaar, zodat de admin-routes ook oude vs.
    nieuwe data kunnen vergelijken vóór het effectief opslaan."""
    data = data or {}
    if block_type == "image_gallery":
        return [i["filename"] for i in data.get("images", []) if i.get("filename")]
    if block_type == "columns":
        return [c["image"] for c in data.get("columns", []) if c.get("image")]
    return []


def block_afbeeldingsbestanden(block):
    """Geeft een lijst bestandsnamen (in static/images/) terug die dit
    blok gebruikt."""
    return afbeeldingen_uit_data(block.block_type, block.data)


def documenten_uit_data(block_type, data):
    """Zelfde als afbeeldingen_uit_data hierboven, maar voor het
    "documents"-blok (PDF/Word/Excel/PowerPoint-uploads) - die bestanden
    staan in static/documents/ (DOCUMENT_UPLOAD_FOLDER), een aparte map van
    de afbeeldingen hierboven, dus een aparte opruim-helper."""
    data = data or {}
    if block_type == "documents":
        return [i["filename"] for i in data.get("items", []) if i.get("filename")]
    return []


def block_documentbestanden(block):
    """Geeft een lijst bestandsnamen (in static/documents/) terug die dit
    blok gebruikt."""
    return documenten_uit_data(block.block_type, block.data)


STYLE_DEFAULTS = {"align": "left", "background": "none", "width": "normaal", "spacing": "normaal"}


def resolve_style(data):
    """Vult het 'weergave'-subveld van een blok aan met standaardwaarden voor
    ontbrekende sleutels - blokken die aangemaakt zijn vóór deze stijlvelden
    bestonden, hebben nog geen 'weergave'-sleutel en tonen zo gewoon hun oude
    (standaard) uiterlijk. Heet bewust niet 'style', want het knop-blok
    gebruikt die sleutel al voor zijn eigen kleur (primary/secondary). Als
    Jinja-global geregistreerd, zie app.py."""
    weergave = (data or {}).get("weergave") or {}
    return {**STYLE_DEFAULTS, **weergave}
