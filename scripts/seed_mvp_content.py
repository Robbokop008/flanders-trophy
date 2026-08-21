"""
scripts/seed_mvp_content.py
-----------------------------
Vult de MVP-pagina's (nodig voor de opening van de offerteaanvragen voor
2027, zie het herbouwvoorstel) met inhoudsblokken en publiceert ze:
About Flanders Trophy, Categories, Packages & Tariffs, Accommodation,
Meals, Weekend Program, FAQ, Previous Editions en Request Your Offer.

Deze pagina's bestaan al (aangemaakt door scripts/seed_navigation.py) maar
staan nog leeg en ongepubliceerd. Cijfers/citaten die letterlijk uit het
voorstel komen (bv. de 2026-kampioenen) zijn overgenomen; waar het voorstel
zelf nog geen definitieve gegevens geeft (tarieven, exacte locaties,
annulatievoorwaarden, ...) blijft de tekst daar bewust vaag over in plaats
van cijfers te verzinnen.

Idempotent: een pagina die al blokken heeft, wordt overgeslagen (niet
opnieuw gevuld) - zo kan dit script veilig herhaald worden nadat een admin
al inhoud bijgewerkt heeft, zonder die wijzigingen te overschrijven.

Gebruik:
    python scripts/seed_mvp_content.py
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


FAQ_ITEMS = [
    ("When can we arrive?", "Arrival is planned for Friday 26 March 2027. Exact check-in times are confirmed closer to the tournament."),
    ("Where do we check in?", "Check-in happens at your assigned accommodation on Friday. You'll receive the exact location together with your confirmed offer."),
    ("What do we need to bring for sleeping?", "Accommodation is basic group accommodation with camp beds - bring your own sleeping bag, mat and personal sleeping equipment."),
    ("Are meals included?", "Yes - Friday dinner, and breakfast and dinner on both Saturday and Sunday are included in your package."),
    ("Can you provide vegetarian meals?", "Yes, vegetarian, vegan and allergy-friendly meals are available, but must be requested in advance - availability cannot be guaranteed without reservation."),
    ("Is transport provided?", "Let us know your transport method (bus or car) when you request your offer. Shuttle and parking details will be published under Practical Info closer to the tournament."),
    ("Where can our bus park?", "Parking information per sports hall will be published on the Locations page and in the downloadable Parking Maps."),
    ("When is the deposit refunded?", "Deposit conditions are confirmed together with your personalised offer - see your accommodation agreement for the exact terms."),
    ("Can we change the number of participants?", "Minor changes are usually possible up to a certain date before the tournament - contact the Tournament Office as soon as your numbers change."),
    ("Can players participate in multiple teams?", "This depends on the category and eligibility rules - see the Tournament Rules document."),
    ("Which ball size is used?", "Ball sizes per category are listed in the Tournament Rules document."),
    ("What happens if we cancel?", "Cancellation conditions are part of your offer/accommodation agreement - contact the Tournament Office directly if this applies to you."),
]


PAGES = {
    "about-flanders-trophy": [
        ("rich_text", {"html": (
            "<h2>22nd edition in 2027</h2>"
            "<p>International Easter handball tournament in Sint-Truiden, taking place from "
            "Friday 26 March to Sunday 28 March 2027, with an optional exit morning on "
            "Monday 29 March.</p>"
            "<p>Over the past two decades, Flanders Trophy has grown into a tournament with a "
            "genuine international reputation, welcoming teams from Germany, the Netherlands, "
            "Belgium, Denmark and Switzerland, and historically also from Sweden, Hungary and "
            "Poland.</p>"
            "<p>In 2026, the tournament brought together more than 100 teams and over 1,200 "
            "participants for 327 matches spread across five sporting halls in Sint-Truiden "
            "&mdash; the largest international handball tournament in the Benelux.</p>"
        )}),
    ],
    "categories": [
        ("rich_text", {"html": (
            "<p>Flanders Trophy 2027 welcomes teams in the following categories. Exact birth "
            "years for 2027 will be confirmed closer to the tournament.</p>"
            "<table><thead><tr><th></th><th>Women</th><th>Men</th></tr></thead><tbody>"
            "<tr><td>U15</td><td>&#10003;</td><td>&#10003;</td></tr>"
            "<tr><td>U17</td><td>&#10003;</td><td>&#10003;</td></tr>"
            "<tr><td>U20</td><td>&#10003;</td><td>&#10003;</td></tr>"
            "<tr><td>Seniors</td><td>&#10003;</td><td>&#10003;</td></tr>"
            "</tbody></table>"
        )}),
    ],
    "packages-tariffs": [
        ("rich_text", {"html": (
            "<p>Every package for the 2027 edition includes tournament participation, "
            "accommodation and meals for the weekend. Packages differ in number of nights, "
            "type of accommodation and sleeping arrangement.</p>"
            "<p>Each package includes:</p><ul>"
            "<li>Number of nights</li><li>Type of accommodation</li>"
            "<li>Bed / camp bed / bring your own sleeping equipment</li><li>Meals</li>"
            "<li>Tournament participation</li><li>Price per participant</li>"
            "<li>Team fee (where applicable)</li><li>Deposit</li></ul>"
            "<p>Detailed tariffs for 2027 will be published here soon. In the meantime, "
            "request a personalised offer and we'll send you the packages that fit your team.</p>"
        )}),
        ("button", {"label": "Request a personalised offer", "url": "/request-offer", "style": "primary"}),
    ],
    "accommodation": [
        ("rich_text", {"html": (
            "<p>Teams stay in basic group accommodation with camp beds &mdash; bring your own "
            "sleeping bag, mat and personal sleeping equipment. Exact locations are confirmed "
            "closer to the tournament, as venues can change from year to year.</p>"
            "<p>House rules for your stay:</p><ul>"
            "<li>Quiet hours</li><li>No smoking indoors</li><li>Alcohol policy</li>"
            "<li>Waste sorted and removed</li><li>Clean up before check-out</li>"
            "<li>Damage is the responsibility of the team</li><li>Keys handed in at check-out</li>"
            "<li>Deposit conditions</li></ul>"
        )}),
    ],
    "meals": [
        ("rich_text", {"html": (
            "<p><strong>Friday:</strong> dinner<br>"
            "<strong>Saturday:</strong> breakfast &amp; dinner<br>"
            "<strong>Sunday:</strong> breakfast &amp; dinner</p>"
            "<p>Vegetarian, vegan and allergy-friendly meals are available.</p>"
            "<p><strong>Special meals must be requested in advance. Availability cannot be "
            "guaranteed without reservation.</strong></p>"
        )}),
    ],
    "weekend-program": [
        ("rich_text", {"html": (
            "<h3>Friday</h3><ul><li>Arrival</li><li>Check-in</li><li>Dinner</li><li>Flag Parade</li></ul>"
            "<h3>Saturday</h3><ul><li>Tournament Day 1</li><li>Evening activities</li></ul>"
            "<h3>Sunday</h3><ul><li>Tournament Day 2</li><li>Finals</li><li>Award ceremonies</li>"
            "<li>Potential departure on Sunday evening</li></ul>"
            "<h3>Monday</h3><ul><li>Potential departure on Monday morning</li></ul>"
        )}),
    ],
    "faq": [
        ("faq", {"items": [{"vraag": q, "antwoord": a} for q, a in FAQ_ITEMS]}),
    ],
    "previous-editions": [
        ("rich_text", {"html": (
            "<h3>Champions 2026</h3><ul>"
            "<li>Women U15 &mdash; Plus Kolkman Heeten</li>"
            "<li>Women U17 &mdash; DSS</li>"
            "<li>Women U20 &mdash; HV Kwiek</li>"
            "<li>Women Seniors &mdash; Union Beynoise</li>"
            "<li>Men U15 &mdash; Hercules</li>"
            "<li>Men U17 &mdash; Hercules</li>"
            "<li>Men U20 &mdash; Kahl Kleinostheim</li>"
            "<li>Men Seniors &mdash; Union Beynoise</li></ul>"
            "<p>More editions will be added here over time.</p>"
        )}),
    ],
    "request-your-offer": [
        ("rich_text", {"html": (
            "<p>Requesting an offer is the first step for foreign clubs joining Flanders "
            "Trophy &mdash; it is <strong>not the same as a final registration</strong>. Once we "
            "receive your request, our team prepares a personalised offer based on your teams "
            "and preferred package.</p>"
            "<p>To request an offer, please get in touch via the Contact page (choose "
            "'Registration / Offers') with the following details:</p><ul>"
            "<li>Club name and country</li><li>Contact person, email and phone</li>"
            "<li>Number of teams per category (Women/Men &mdash; U15/U17/U20/Seniors)</li>"
            "<li>Expected number of participants</li><li>Preferred package</li>"
            "<li>Arrival and departure dates</li><li>Transport by bus or car</li></ul>"
            "<p>An online request form is coming soon &mdash; until then, use the button below.</p>"
        )}),
        ("button", {"label": "Contact us to request your offer", "url": "/contact", "style": "primary"}),
    ],
}


def run():
    app = create_app("development")
    with app.app_context():
        for slug, blocks in PAGES.items():
            _add_blocks(slug, blocks)
        db.session.commit()
        print("MVP-pagina's ingevuld en gepubliceerd (waar nieuw content toegevoegd is).")


if __name__ == "__main__":
    run()
