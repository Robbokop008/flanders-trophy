"""
scripts/seed_remaining_content.py
------------------------------------
Vult de resterende submenu-pagina's die in scripts/seed_navigation.py als
lege stub zijn aangemaakt, maar (per het herbouwvoorstel) pas tussen
januari en maart écht "af" hoeven te zijn: Tournament Format, Fair Play,
Teams & Groups, Match Schedule, Locations, Flag Parade, Live Results,
Rankings, Check-in, Travel & Parking, Downloads, Shuttle.

Bewust geen concrete data die nu nog niet bestaat (speeltijden, poules,
wedstrijdschema, exacte locaties/adressen, downloadbare bestanden, ...) -
die inhoud hangt af van het aantal ingeschreven teams en de loting, en komt
er pas na de inschrijvingsperiode. In plaats daarvan legt elke pagina uit
wát er komt en wanneer, zodat er geen dode of lege menu-items zijn terwijl
we wachten tot die inhoud er effectief is. "Tournament Rules" zit hier
bewust niet bij: dat moet een downloadbare PDF worden (zie het voorstel),
geen tekstpagina, en er is nog geen PDF om aan te linken.

Zelfde idempotente patroon als scripts/seed_mvp_content.py: een pagina met
al blokken wordt overgeslagen.

Gebruik:
    python scripts/seed_remaining_content.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from extensions import db
from models import Page, PageBlock


def _add_blocks(slug, blocks):
    page = Page.query.filter_by(slug=slug).first()
    if page is None:
        print(f"  ! pagina '{slug}' bestaat niet - draai eerst scripts/seed_navigation.py")
        return
    if page.blocks:
        print(f"  = '{slug}' heeft al inhoud, overgeslagen")
        return

    for position, (block_type, data) in enumerate(blocks, start=1):
        db.session.add(PageBlock(page_id=page.id, block_type=block_type, position=position, data=data))
    page.is_published = True
    print(f"  + inhoud + publicatie: {slug}")


PAGES = {
    "tournament-format": [
        ("rich_text", {"html": (
            "<p>The tournament format follows the same structure across categories:</p><ul>"
            "<li>Matches are played on both Saturday and Sunday.</li>"
            "<li>Teams first play a group stage.</li>"
            "<li>Based on the group stage results, teams continue in ranking matches.</li>"
            "<li>Where applicable per category, quarter-finals and semi-finals follow.</li>"
            "<li>The weekend concludes with the finals on Sunday.</li></ul>"
            "<p>Exact playing times and the minimum number of matches per team depend on the "
            "number of registered teams per category, and are confirmed once registrations "
            "close. Full details are published in the Tournament Rules.</p>"
        )}),
    ],
    "fair-play": [
        ("rich_text", {"html": (
            "<h3>Fair Play Trophy &ndash; Women</h3><h3>Fair Play Trophy &ndash; Men</h3>"
            "<p>Alongside the sporting competition, Flanders Trophy awards a Fair Play Trophy "
            "in both the Women's and Men's categories, recognising the team with the best "
            "sporting conduct throughout the weekend. Judging criteria are confirmed closer "
            "to the tournament.</p>"
            "<h3>Pure Fun Trophy</h3>"
            "<p>True to the tournament's motto &ldquo;Pure Fun &amp; Handball&rdquo;, a Pure Fun "
            "Trophy also celebrates the team that best embodies the spirit of the weekend, on "
            "and off the court.</p>"
        )}),
    ],
    "teams-groups": [
        ("rich_text", {"html": (
            "<p>Once clubs register their teams for 2027, this page will list all "
            "participating teams per category, grouped into their tournament pools.</p>"
            "<p>Check back closer to the tournament, or after your club's registration is "
            "confirmed.</p>"
        )}),
    ],
    "match-schedule": [
        ("rich_text", {"html": (
            "<p>The full match schedule, filterable by category (Women/Men &mdash; "
            "U15/U17/U20/Seniors), will be published here once the draw is made &mdash; "
            "typically in the weeks before the tournament.</p>"
        )}),
    ],
    "locations": [
        ("rich_text", {"html": (
            "<p>Matches are spread across several sporting halls in and around Sint-Truiden. "
            "In 2026, matches were played at Trudo, KA/Jodenstraat, Lago, Nieuw-Sint-Truiden "
            "and Nieuwerkerken.</p>"
            "<p>Exact 2027 locations, addresses, parking and a map per hall will be published "
            "here closer to the tournament, as venues can change from year to year.</p>"
        )}),
    ],
    "flag-parade": [
        ("rich_text", {"html": (
            "<p>The Flag Parade is a Flanders Trophy tradition: on Friday evening, all "
            "participating teams walk through the city centre of Sint-Truiden behind their "
            "national flag &mdash; around 900 handballers, opening the tournament weekend "
            "together.</p>"
            "<p>Photos and video from previous editions will be added here soon.</p>"
        )}),
    ],
    "live-results": [
        ("rich_text", {"html": (
            "<p>During the tournament weekend, live results will be published here: category "
            "&rarr; pool &rarr; results &rarr; ranking &rarr; finals, with Played / Won / Draw / "
            "Lost / Goals / Points per team.</p>"
            "<p>This page becomes active once the 2027 tournament weekend starts.</p>"
        )}),
    ],
    "rankings": [
        ("rich_text", {"html": (
            "<p>Full final rankings per category (not just the podium) are published here "
            "after each tournament weekend, alongside the champions overview on the "
            "Previous Editions page.</p>"
        )}),
    ],
    "check-in": [
        ("rich_text", {"html": (
            "<p>Check-in takes place on Friday at your assigned accommodation. Exact times "
            "and the check-in location are confirmed together with your offer.</p>"
            "<p>Please make sure your final team lists and any required documents are ready "
            "at check-in &mdash; details follow via the Downloads page.</p>"
        )}),
    ],
    "travel-parking": [
        ("rich_text", {"html": (
            "<p>Travel and parking information &mdash; including bus parking per sports hall "
            "and shuttle details &mdash; will be published here closer to the tournament.</p>"
            "<p>Already know your transport method? Let us know (bus or car) when you request "
            "your offer.</p>"
        )}),
    ],
    "downloads": [
        ("rich_text", {"html": (
            "<p>All official documents for 2027 will be collected here &mdash; no more "
            "searching through news articles.</p><ul>"
            "<li>Tournament Rules</li><li>Accommodation Rules</li><li>Sleepover List</li>"
            "<li>Team List</li><li>Shuttle Information</li><li>Parking Maps</li>"
            "<li>Webinar Presentation</li><li>Weekend Guide</li></ul>"
            "<p>Documents are added here as they become available.</p>"
        )}),
    ],
    "shuttle": [
        ("rich_text", {"html": (
            "<p>Shuttle information between accommodation, sports halls and the city centre "
            "will be published here closer to the tournament.</p>"
        )}),
    ],
}


def run():
    app = create_app("development")
    with app.app_context():
        for slug, blocks in PAGES.items():
            _add_blocks(slug, blocks)
        db.session.commit()
        print("Resterende pagina's ingevuld en gepubliceerd (waar nieuw content toegevoegd is).")


if __name__ == "__main__":
    run()
