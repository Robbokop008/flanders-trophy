"""
scripts/generate_hero_outline.py
---------------------------------
Genereert static/images/flanders-outline.png: de "Flanders"-contourtekst
(rand van de letters, doorzichtig midden) op de homepage-hero
(templates/index.html, .hp-hero-title-outline).

Waarom een vaste afbeelding i.p.v. live tekst met CSS/SVG-stroke? Op
sommige toestellen (bv. Android/Chrome) faket de browser zelf een vet
lettergewicht wanneer het systeemlettertype dat gewicht niet echt heeft, en
dat botst met een eigen contourlijn (-webkit-text-stroke of SVG <text> +
stroke) tot een rommelige, kruisende lijn - en dat verschilt per toestel/
lettertype, dus was niet consistent op te lossen met CSS alleen. Dit script
rendert de contour éénmalig in een browser waar hij wél correct is (een
gewoon systeemlettertype op deze ontwikkelmachine volstaat, want het
resultaat is nadien gewoon een afbeelding - elk toestel toont exact
hetzelfde, ongeacht zijn eigen lettertype).

Enkel nodig bij een ontwerpwijziging (andere tekst/kleur/lettertype) - niet
bij het gewoon draaien van de site. Vereist playwright (niet in
requirements.txt, want enkel een ontwerp-hulpmiddel, geen site-dependency):

    pip install playwright
    playwright install chromium
    python scripts/generate_hero_outline.py
"""

import os

from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE_DIR, "static", "images", "flanders-outline.png")

HTML = """
<!doctype html>
<html>
<head>
<style>
  html, body { margin: 0; background: transparent; }
  #word {
    display: inline-block;
    padding: 40px;
    font-family: "Segoe UI", system-ui, -apple-system, Roboto, sans-serif;
    font-weight: 700;
    font-style: italic;
    font-size: 380px;
    line-height: 1;
    color: transparent;
    -webkit-text-stroke: 7px #ffffff;
    white-space: nowrap;
  }
</style>
</head>
<body><span id="word">Flanders</span></body>
</html>
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 2200, "height": 700})
        page.set_content(HTML)
        page.locator("#word").screenshot(path=OUT_PATH, omit_background=True)
        browser.close()
    print(f"Geschreven: {OUT_PATH}")


if __name__ == "__main__":
    main()
