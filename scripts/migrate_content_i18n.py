# -*- coding: utf-8 -*-
"""
scripts/migrate_content_i18n.py
----------------------------------
Eenmalige migratie + vertaling: zet de tekstvelden van elk bestaand
PageBlock (rich_text.html, faq.items[].vraag/antwoord, button.label) om van
een platte Engelse string naar een per-taal dict {"en": ..., "nl": ...,
"fr": ..., "de": ...}, zoals het admin-blokformulier en de publieke
blok-templates nu verwachten (zie utils/i18n.py).

De NL/FR/DE-vertalingen hieronder zijn door mij (Claude) vertaald op basis
van de Engelse brontekst die ik zelf eerder voor deze pagina's geschreven
heb (scripts/seed_mvp_content.py / seed_remaining_content.py) - geen
machinevertaling, maar ook geen vervanging voor nazicht door een native
speaker/de club zelf voor ze definitief live gaat.

Idempotent op blokniveau: een blok waarvan 'html'/'label' al een dict is
(al gemigreerd) wordt overgeslagen.

Gebruik:
    python scripts/migrate_content_i18n.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from extensions import db
from models import Page, PageBlock

# slug -> { block_index (0-based, volgorde van page.blocks) : {"en":..., "nl":..., "fr":..., "de":...} }
RICH_TEXT_TRANSLATIONS = {
    "about-flanders-trophy": {
        "nl": "<h2>22ste editie in 2027</h2><p>Internationaal paashandbaltoernooi in Sint-Truiden, van vrijdag 26 maart tot zondag 28 maart 2027, met een optionele vertrekochtend op maandag 29 maart.</p><p>De voorbije twintig jaar is Flanders Trophy uitgegroeid tot een toernooi met een echte internationale reputatie, met ploegen uit Duitsland, Nederland, België, Denemarken en Zwitserland, en historisch ook uit Zweden, Hongarije en Polen.</p><p>In 2026 bracht het toernooi meer dan 100 teams en ruim 1.200 deelnemers samen voor 327 wedstrijden, verspreid over vijf sporthallen in Sint-Truiden &mdash; het grootste internationale handbaltoernooi van de Benelux.</p>",
        "fr": "<h2>22e édition en 2027</h2><p>Tournoi international de handball de Pâques à Sint-Truiden, du vendredi 26 mars au dimanche 28 mars 2027, avec un départ optionnel le lundi matin 29 mars.</p><p>Au cours des vingt dernières années, Flanders Trophy est devenu un tournoi à la réputation véritablement internationale, accueillant des équipes d'Allemagne, des Pays-Bas, de Belgique, du Danemark et de Suisse, et historiquement aussi de Suède, de Hongrie et de Pologne.</p><p>En 2026, le tournoi a réuni plus de 100 équipes et plus de 1 200 participants pour 327 matchs répartis dans cinq salles de sport à Sint-Truiden &mdash; le plus grand tournoi international de handball du Benelux.</p>",
        "de": "<h2>22. Ausgabe im Jahr 2027</h2><p>Internationales Osterhandballturnier in Sint-Truiden, von Freitag, den 26. März, bis Sonntag, den 28. März 2027, mit einer optionalen Abreise am Montagmorgen, den 29. März.</p><p>In den letzten zwanzig Jahren hat sich die Flanders Trophy zu einem Turnier mit echtem internationalem Ansehen entwickelt und Teams aus Deutschland, den Niederlanden, Belgien, Dänemark und der Schweiz sowie historisch auch aus Schweden, Ungarn und Polen empfangen.</p><p>2026 brachte das Turnier mehr als 100 Teams und über 1.200 Teilnehmer für 327 Spiele in fünf Sporthallen in Sint-Truiden zusammen &mdash; das größte internationale Handballturnier der Beneluxstaaten.</p>",
    },
    "accommodation": {
        "nl": "<p>Teams verblijven in eenvoudige groepsaccommodatie met veldbedden &mdash; breng je eigen slaapzak, matje en persoonlijk slaapmateriaal mee. De exacte locaties worden bevestigd dichter bij het toernooi, aangezien locaties jaarlijks kunnen wijzigen.</p><p>Huisregels voor je verblijf:</p><ul><li>Stille uren</li><li>Niet roken binnen</li><li>Alcoholbeleid</li><li>Afval gesorteerd en meegenomen</li><li>Opruimen vóór het vertrek</li><li>Schade is de verantwoordelijkheid van het team</li><li>Sleutels ingeleverd bij vertrek</li><li>Waarborgvoorwaarden</li></ul>",
        "fr": "<p>Les équipes séjournent dans un hébergement de groupe basique avec lits de camp &mdash; apportez votre propre sac de couchage, matelas et matériel de couchage personnel. Les lieux exacts sont confirmés à l'approche du tournoi, les sites pouvant changer d'une année à l'autre.</p><p>Règlement intérieur pour votre séjour :</p><ul><li>Heures de silence</li><li>Interdiction de fumer à l'intérieur</li><li>Politique concernant l'alcool</li><li>Déchets triés et évacués</li><li>Nettoyage avant le départ</li><li>Les dégâts sont de la responsabilité de l'équipe</li><li>Clés remises au départ</li><li>Conditions de la caution</li></ul>",
        "de": "<p>Die Teams übernachten in einfacher Gruppenunterkunft mit Feldbetten &mdash; bringen Sie Ihren eigenen Schlafsack, Ihre Isomatte und persönliche Schlafausrüstung mit. Die genauen Standorte werden näher am Turnier bestätigt, da sich die Austragungsorte von Jahr zu Jahr ändern können.</p><p>Hausordnung für Ihren Aufenthalt:</p><ul><li>Ruhezeiten</li><li>Rauchverbot in Innenräumen</li><li>Alkoholrichtlinie</li><li>Abfall getrennt und entsorgt</li><li>Aufräumen vor der Abreise</li><li>Schäden liegen in der Verantwortung des Teams</li><li>Schlüssel bei der Abreise abgeben</li><li>Kautionsbedingungen</li></ul>",
    },
    "categories": {
        "nl": "<p>Flanders Trophy 2027 verwelkomt teams in de volgende categorieën. De exacte geboortejaren voor 2027 worden dichter bij het toernooi bevestigd.</p><table><thead><tr><th></th><th>Dames</th><th>Heren</th></tr></thead><tbody><tr><td>U15</td><td>&#10003;</td><td>&#10003;</td></tr><tr><td>U17</td><td>&#10003;</td><td>&#10003;</td></tr><tr><td>U20</td><td>&#10003;</td><td>&#10003;</td></tr><tr><td>Senioren</td><td>&#10003;</td><td>&#10003;</td></tr></tbody></table>",
        "fr": "<p>Flanders Trophy 2027 accueille des équipes dans les catégories suivantes. Les années de naissance exactes pour 2027 seront confirmées à l'approche du tournoi.</p><table><thead><tr><th></th><th>Femmes</th><th>Hommes</th></tr></thead><tbody><tr><td>U15</td><td>&#10003;</td><td>&#10003;</td></tr><tr><td>U17</td><td>&#10003;</td><td>&#10003;</td></tr><tr><td>U20</td><td>&#10003;</td><td>&#10003;</td></tr><tr><td>Seniors</td><td>&#10003;</td><td>&#10003;</td></tr></tbody></table>",
        "de": "<p>Die Flanders Trophy 2027 begrüßt Teams in den folgenden Kategorien. Die genauen Geburtsjahrgänge für 2027 werden näher am Turnier bestätigt.</p><table><thead><tr><th></th><th>Frauen</th><th>Männer</th></tr></thead><tbody><tr><td>U15</td><td>&#10003;</td><td>&#10003;</td></tr><tr><td>U17</td><td>&#10003;</td><td>&#10003;</td></tr><tr><td>U20</td><td>&#10003;</td><td>&#10003;</td></tr><tr><td>Senioren</td><td>&#10003;</td><td>&#10003;</td></tr></tbody></table>",
    },
    "check-in": {
        "nl": "<p>Check-in vindt plaats op vrijdag bij je toegewezen accommodatie. De exacte tijden en de check-in-locatie worden samen met je offerte bevestigd.</p><p>Zorg ervoor dat je definitieve teamlijsten en eventueel vereiste documenten klaar zijn bij het inchecken &mdash; details volgen via de pagina Downloads.</p>",
        "fr": "<p>L'enregistrement a lieu le vendredi à votre hébergement attribué. Les horaires exacts et le lieu d'enregistrement sont confirmés avec votre offre.</p><p>Veillez à ce que vos listes d'équipe définitives et tout document requis soient prêts lors de l'enregistrement &mdash; les détails suivront via la page Téléchargements.</p>",
        "de": "<p>Der Check-in findet am Freitag in Ihrer zugewiesenen Unterkunft statt. Die genauen Zeiten und der Check-in-Ort werden zusammen mit Ihrem Angebot bestätigt.</p><p>Bitte stellen Sie sicher, dass Ihre endgültigen Teamlisten und alle erforderlichen Dokumente beim Check-in bereit sind &mdash; Details folgen über die Downloads-Seite.</p>",
    },
    "downloads": {
        "nl": "<p>Alle officiële documenten voor 2027 worden hier verzameld &mdash; niet langer zoeken doorheen nieuwsartikels.</p><ul><li>Toernooireglement</li><li>Accommodatiereglement</li><li>Slaaplijst</li><li>Teamlijst</li><li>Shuttle-informatie</li><li>Parkeerplannen</li><li>Webinarpresentatie</li><li>Weekendgids</li></ul><p>Documenten worden hier toegevoegd zodra ze beschikbaar zijn.</p>",
        "fr": "<p>Tous les documents officiels pour 2027 seront rassemblés ici &mdash; plus besoin de chercher dans les articles d'actualité.</p><ul><li>Règlement du tournoi</li><li>Règlement de l'hébergement</li><li>Liste de couchage</li><li>Liste d'équipe</li><li>Informations sur la navette</li><li>Plans de parking</li><li>Présentation du webinaire</li><li>Guide du week-end</li></ul><p>Les documents sont ajoutés ici au fur et à mesure de leur disponibilité.</p>",
        "de": "<p>Alle offiziellen Dokumente für 2027 werden hier gesammelt &mdash; kein Suchen mehr in Newsartikeln.</p><ul><li>Turnierregeln</li><li>Unterkunftsregeln</li><li>Übernachtungsliste</li><li>Teamliste</li><li>Shuttle-Informationen</li><li>Parkpläne</li><li>Webinar-Präsentation</li><li>Wochenendguide</li></ul><p>Dokumente werden hier ergänzt, sobald sie verfügbar sind.</p>",
    },
    "fair-play": {
        "nl": "<h3>Fair Play Trophy &ndash; Dames</h3><h3>Fair Play Trophy &ndash; Heren</h3><p>Naast de sportieve competitie reikt Flanders Trophy een Fair Play Trophy uit in zowel de Dames- als de Heren-categorie, als erkenning voor het team met het beste sportieve gedrag tijdens het hele weekend. De beoordelingscriteria worden bevestigd dichter bij het toernooi.</p><h3>Pure Fun Trophy</h3><p>Trouw aan het motto van het toernooi &ldquo;Pure Fun &amp; Handball&rdquo;, viert een Pure Fun Trophy ook het team dat de sfeer van het weekend het best belichaamt, zowel op als naast het veld.</p>",
        "fr": "<h3>Fair Play Trophy &ndash; Femmes</h3><h3>Fair Play Trophy &ndash; Hommes</h3><p>Parallèlement à la compétition sportive, Flanders Trophy décerne un Fair Play Trophy dans les catégories Femmes et Hommes, récompensant l'équipe ayant fait preuve du meilleur comportement sportif tout au long du week-end. Les critères de jugement sont confirmés à l'approche du tournoi.</p><h3>Pure Fun Trophy</h3><p>Fidèle à la devise du tournoi &ldquo;Pure Fun &amp; Handball&rdquo;, un Pure Fun Trophy célèbre également l'équipe qui incarne le mieux l'esprit du week-end, sur et en dehors du terrain.</p>",
        "de": "<h3>Fair-Play-Trophäe &ndash; Frauen</h3><h3>Fair-Play-Trophäe &ndash; Männer</h3><p>Neben dem sportlichen Wettkampf vergibt die Flanders Trophy eine Fair-Play-Trophäe sowohl in der Frauen- als auch in der Männerkategorie, die das Team mit dem besten sportlichen Verhalten während des gesamten Wochenendes auszeichnet. Die Bewertungskriterien werden näher am Turnier bestätigt.</p><h3>Pure Fun Trophy</h3><p>Getreu dem Motto des Turniers &ldquo;Pure Fun &amp; Handball&rdquo; feiert eine Pure Fun Trophy zudem das Team, das den Geist des Wochenendes auf und neben dem Feld am besten verkörpert.</p>",
    },
    "flag-parade": {
        "nl": "<p>De Vlaggenparade is een traditie van Flanders Trophy: op vrijdagavond trekken alle deelnemende teams door het stadscentrum van Sint-Truiden achter hun nationale vlag &mdash; zo'n 900 handballers, die samen het toernooiweekend openen.</p><p>Foto's en video's van vorige edities worden hier binnenkort toegevoegd.</p>",
        "fr": "<p>La Parade des drapeaux est une tradition de Flanders Trophy : le vendredi soir, toutes les équipes participantes traversent le centre-ville de Sint-Truiden derrière leur drapeau national &mdash; environ 900 handballeurs, ouvrant ensemble le week-end du tournoi.</p><p>Des photos et vidéos des éditions précédentes seront bientôt ajoutées ici.</p>",
        "de": "<p>Die Flaggenparade ist eine Tradition der Flanders Trophy: Am Freitagabend ziehen alle teilnehmenden Teams hinter ihrer Nationalflagge durch die Innenstadt von Sint-Truiden &mdash; rund 900 Handballer, die gemeinsam das Turnierwochenende eröffnen.</p><p>Fotos und Videos früherer Ausgaben werden hier in Kürze ergänzt.</p>",
    },
    "live-results": {
        "nl": "<p>Tijdens het toernooiweekend worden hier live resultaten gepubliceerd: categorie &rarr; poule &rarr; resultaten &rarr; klassement &rarr; finales, met Gespeeld / Gewonnen / Gelijk / Verloren / Doelpunten / Punten per team.</p><p>Deze pagina wordt actief zodra het toernooiweekend van 2027 begint.</p>",
        "fr": "<p>Pendant le week-end du tournoi, les résultats en direct seront publiés ici : catégorie &rarr; poule &rarr; résultats &rarr; classement &rarr; finales, avec Joués / Gagnés / Nuls / Perdus / Buts / Points par équipe.</p><p>Cette page devient active dès le début du week-end du tournoi 2027.</p>",
        "de": "<p>Während des Turnierwochenendes werden hier Live-Ergebnisse veröffentlicht: Kategorie &rarr; Gruppe &rarr; Ergebnisse &rarr; Rangliste &rarr; Finals, mit Gespielt / Gewonnen / Unentschieden / Verloren / Tore / Punkte pro Team.</p><p>Diese Seite wird aktiv, sobald das Turnierwochenende 2027 beginnt.</p>",
    },
    "locations": {
        "nl": "<p>Wedstrijden vinden verspreid plaats over verschillende sporthallen in en rond Sint-Truiden. In 2026 werd er gespeeld in Trudo, KA/Jodenstraat, Lago, Nieuw-Sint-Truiden en Nieuwerkerken.</p><p>De exacte locaties, adressen, parking en een kaart per hal voor 2027 worden hier gepubliceerd dichter bij het toernooi, aangezien locaties jaarlijks kunnen wijzigen.</p>",
        "fr": "<p>Les matchs se déroulent dans plusieurs salles de sport à Sint-Truiden et ses environs. En 2026, les matchs se sont déroulés à Trudo, KA/Jodenstraat, Lago, Nieuw-Sint-Truiden et Nieuwerkerken.</p><p>Les lieux exacts, adresses, parkings et un plan par salle pour 2027 seront publiés ici à l'approche du tournoi, les sites pouvant changer d'une année à l'autre.</p>",
        "de": "<p>Die Spiele finden verteilt auf mehrere Sporthallen in und um Sint-Truiden statt. 2026 wurde in Trudo, KA/Jodenstraat, Lago, Nieuw-Sint-Truiden und Nieuwerkerken gespielt.</p><p>Die genauen Standorte, Adressen, Parkmöglichkeiten und eine Karte pro Halle für 2027 werden hier näher am Turnier veröffentlicht, da sich die Austragungsorte von Jahr zu Jahr ändern können.</p>",
    },
    "match-schedule": {
        "nl": "<p>Het volledige wedstrijdschema, filterbaar per categorie (Dames/Heren &mdash; U15/U17/U20/Senioren), wordt hier gepubliceerd zodra de loting is gemaakt &mdash; doorgaans in de weken voor het toernooi.</p>",
        "fr": "<p>Le calendrier complet des matchs, filtrable par catégorie (Femmes/Hommes &mdash; U15/U17/U20/Seniors), sera publié ici dès que le tirage au sort sera effectué &mdash; généralement dans les semaines précédant le tournoi.</p>",
        "de": "<p>Der vollständige Spielplan, filterbar nach Kategorie (Frauen/Männer &mdash; U15/U17/U20/Senioren), wird hier veröffentlicht, sobald die Auslosung erfolgt ist &mdash; in der Regel in den Wochen vor dem Turnier.</p>",
    },
    "meals": {
        "nl": "<p><strong>Vrijdag:</strong> avondeten<br><strong>Zaterdag:</strong> ontbijt &amp; avondeten<br><strong>Zondag:</strong> ontbijt &amp; avondeten</p><p>Vegetarische, veganistische en allergievriendelijke maaltijden zijn beschikbaar.</p><p><strong>Speciale maaltijden moeten op voorhand aangevraagd worden. Beschikbaarheid kan niet gegarandeerd worden zonder reservatie.</strong></p>",
        "fr": "<p><strong>Vendredi :</strong> dîner<br><strong>Samedi :</strong> petit-déjeuner &amp; dîner<br><strong>Dimanche :</strong> petit-déjeuner &amp; dîner</p><p>Des repas végétariens, végans et adaptés aux allergies sont disponibles.</p><p><strong>Les repas spéciaux doivent être demandés à l'avance. La disponibilité ne peut être garantie sans réservation.</strong></p>",
        "de": "<p><strong>Freitag:</strong> Abendessen<br><strong>Samstag:</strong> Frühstück &amp; Abendessen<br><strong>Sonntag:</strong> Frühstück &amp; Abendessen</p><p>Vegetarische, vegane und allergikerfreundliche Mahlzeiten sind verfügbar.</p><p><strong>Sondermahlzeiten müssen im Voraus angefragt werden. Ohne Reservierung kann die Verfügbarkeit nicht garantiert werden.</strong></p>",
    },
    "packages-tariffs": {
        "nl": "<p>Elk pakket voor de editie van 2027 omvat toernooideelname, accommodatie en maaltijden voor het weekend. Pakketten verschillen in aantal nachten, type accommodatie en slaapregeling.</p><p>Elk pakket omvat:</p><ul><li>Aantal nachten</li><li>Type accommodatie</li><li>Bed / veldbed / eigen slaapmateriaal</li><li>Maaltijden</li><li>Toernooideelname</li><li>Prijs per deelnemer</li><li>Teamfee (indien van toepassing)</li><li>Waarborg</li></ul><p>Gedetailleerde tarieven voor 2027 worden hier binnenkort gepubliceerd. Vraag ondertussen een offerte op maat aan en wij sturen je de pakketten die bij je team passen.</p>",
        "fr": "<p>Chaque formule pour l'édition 2027 comprend la participation au tournoi, l'hébergement et les repas pour le week-end. Les formules diffèrent par le nombre de nuits, le type d'hébergement et les modalités de couchage.</p><p>Chaque formule comprend :</p><ul><li>Nombre de nuits</li><li>Type d'hébergement</li><li>Lit / lit de camp / matériel de couchage personnel</li><li>Repas</li><li>Participation au tournoi</li><li>Prix par participant</li><li>Frais d'équipe (le cas échéant)</li><li>Caution</li></ul><p>Les tarifs détaillés pour 2027 seront bientôt publiés ici. En attendant, demandez une offre personnalisée et nous vous enverrons les formules adaptées à votre équipe.</p>",
        "de": "<p>Jedes Paket für die Ausgabe 2027 umfasst die Turnierteilnahme, Unterkunft und Verpflegung für das Wochenende. Die Pakete unterscheiden sich in Anzahl der Nächte, Art der Unterkunft und Schlafregelung.</p><p>Jedes Paket umfasst:</p><ul><li>Anzahl der Nächte</li><li>Art der Unterkunft</li><li>Bett / Feldbett / eigene Schlafausrüstung</li><li>Verpflegung</li><li>Turnierteilnahme</li><li>Preis pro Teilnehmer</li><li>Teamgebühr (falls zutreffend)</li><li>Kaution</li></ul><p>Detaillierte Tarife für 2027 werden hier in Kürze veröffentlicht. Fordern Sie in der Zwischenzeit ein persönliches Angebot an, und wir senden Ihnen die zu Ihrem Team passenden Pakete.</p>",
    },
    "previous-editions": {
        "nl": "<h3>Kampioenen 2026</h3><ul><li>Dames U15 &mdash; Plus Kolkman Heeten</li><li>Dames U17 &mdash; DSS</li><li>Dames U20 &mdash; HV Kwiek</li><li>Dames Senioren &mdash; Union Beynoise</li><li>Heren U15 &mdash; Hercules</li><li>Heren U17 &mdash; Hercules</li><li>Heren U20 &mdash; Kahl Kleinostheim</li><li>Heren Senioren &mdash; Union Beynoise</li></ul><p>Meer edities worden hier na verloop van tijd toegevoegd.</p>",
        "fr": "<h3>Champions 2026</h3><ul><li>Femmes U15 &mdash; Plus Kolkman Heeten</li><li>Femmes U17 &mdash; DSS</li><li>Femmes U20 &mdash; HV Kwiek</li><li>Femmes Seniors &mdash; Union Beynoise</li><li>Hommes U15 &mdash; Hercules</li><li>Hommes U17 &mdash; Hercules</li><li>Hommes U20 &mdash; Kahl Kleinostheim</li><li>Hommes Seniors &mdash; Union Beynoise</li></ul><p>D'autres éditions seront ajoutées ici au fil du temps.</p>",
        "de": "<h3>Champions 2026</h3><ul><li>Frauen U15 &mdash; Plus Kolkman Heeten</li><li>Frauen U17 &mdash; DSS</li><li>Frauen U20 &mdash; HV Kwiek</li><li>Frauen Senioren &mdash; Union Beynoise</li><li>Männer U15 &mdash; Hercules</li><li>Männer U17 &mdash; Hercules</li><li>Männer U20 &mdash; Kahl Kleinostheim</li><li>Männer Senioren &mdash; Union Beynoise</li></ul><p>Weitere Ausgaben werden hier im Laufe der Zeit ergänzt.</p>",
    },
    "rankings": {
        "nl": "<p>Volledige eindklassementen per categorie (niet enkel het podium) worden hier gepubliceerd na elk toernooiweekend, samen met het kampioenenoverzicht op de pagina Vorige Edities.</p>",
        "fr": "<p>Les classements finaux complets par catégorie (pas seulement le podium) sont publiés ici après chaque week-end de tournoi, en plus de l'aperçu des champions sur la page Éditions précédentes.</p>",
        "de": "<p>Vollständige Endranglisten pro Kategorie (nicht nur das Podium) werden hier nach jedem Turnierwochenende veröffentlicht, zusammen mit der Meisterübersicht auf der Seite Frühere Ausgaben.</p>",
    },
    "shuttle": {
        "nl": "<p>Shuttle-informatie tussen accommodatie, sporthallen en het stadscentrum wordt hier gepubliceerd dichter bij het toernooi.</p>",
        "fr": "<p>Les informations sur la navette entre l'hébergement, les salles de sport et le centre-ville seront publiées ici à l'approche du tournoi.</p>",
        "de": "<p>Shuttle-Informationen zwischen Unterkunft, Sporthallen und Innenstadt werden hier näher am Turnier veröffentlicht.</p>",
    },
    "teams-groups": {
        "nl": "<p>Zodra clubs hun teams voor 2027 inschrijven, toont deze pagina alle deelnemende teams per categorie, ingedeeld in hun toernooipoules.</p><p>Kom later terug, dichter bij het toernooi, of nadat de inschrijving van je club bevestigd is.</p>",
        "fr": "<p>Une fois que les clubs auront inscrit leurs équipes pour 2027, cette page présentera toutes les équipes participantes par catégorie, réparties dans leurs poules de tournoi.</p><p>Revenez consulter cette page à l'approche du tournoi, ou après confirmation de l'inscription de votre club.</p>",
        "de": "<p>Sobald Vereine ihre Teams für 2027 anmelden, listet diese Seite alle teilnehmenden Teams pro Kategorie auf, eingeteilt in ihre Turniergruppen.</p><p>Schauen Sie näher am Turnier wieder vorbei, oder sobald die Anmeldung Ihres Vereins bestätigt ist.</p>",
    },
    "tournament-format": {
        "nl": "<p>Het toernooiformat volgt dezelfde structuur in alle categorieën:</p><ul><li>Wedstrijden worden zowel op zaterdag als zondag gespeeld.</li><li>Teams spelen eerst een groepsfase.</li><li>Op basis van de resultaten van de groepsfase spelen teams verder in rangschikkingswedstrijden.</li><li>Waar van toepassing per categorie volgen kwart- en halve finales.</li><li>Het weekend wordt afgesloten met de finales op zondag.</li></ul><p>De exacte speeltijden en het minimum aantal wedstrijden per team hangen af van het aantal ingeschreven teams per categorie, en worden bevestigd zodra de inschrijvingen gesloten zijn. Volledige details staan in het Toernooireglement.</p>",
        "fr": "<p>Le format du tournoi suit la même structure dans toutes les catégories :</p><ul><li>Les matchs se jouent le samedi et le dimanche.</li><li>Les équipes disputent d'abord une phase de groupes.</li><li>Sur base des résultats de la phase de groupes, les équipes poursuivent en matchs de classement.</li><li>Le cas échéant selon la catégorie, des quarts et demi-finales suivent.</li><li>Le week-end se termine par les finales le dimanche.</li></ul><p>Les horaires exacts et le nombre minimum de matchs par équipe dépendent du nombre d'équipes inscrites par catégorie, et sont confirmés à la clôture des inscriptions. Tous les détails sont publiés dans le Règlement du tournoi.</p>",
        "de": "<p>Das Turnierformat folgt in allen Kategorien der gleichen Struktur:</p><ul><li>Die Spiele finden sowohl am Samstag als auch am Sonntag statt.</li><li>Die Teams spielen zunächst eine Gruppenphase.</li><li>Basierend auf den Ergebnissen der Gruppenphase spielen die Teams in Platzierungsspielen weiter.</li><li>Je nach Kategorie folgen gegebenenfalls Viertel- und Halbfinale.</li><li>Das Wochenende endet mit den Finals am Sonntag.</li></ul><p>Die genauen Spielzeiten und die Mindestanzahl an Spielen pro Team hängen von der Anzahl der gemeldeten Teams pro Kategorie ab und werden nach Anmeldeschluss bestätigt. Alle Details finden Sie in den Turnierregeln.</p>",
    },
    "travel-parking": {
        "nl": "<p>Reis- en parkeerinformatie &mdash; inclusief busparking per sporthal en shuttledetails &mdash; wordt hier gepubliceerd dichter bij het toernooi.</p><p>Ken je je vervoerswijze al? Laat het ons weten (bus of auto) bij het aanvragen van je offerte.</p>",
        "fr": "<p>Les informations sur les déplacements et le parking &mdash; y compris le parking bus par salle de sport et les détails de la navette &mdash; seront publiées ici à l'approche du tournoi.</p><p>Vous connaissez déjà votre moyen de transport ? Faites-le-nous savoir (bus ou voiture) lors de votre demande d'offre.</p>",
        "de": "<p>Reise- und Parkinformationen &mdash; einschließlich Busparkplätzen pro Sporthalle und Shuttle-Details &mdash; werden hier näher am Turnier veröffentlicht.</p><p>Kennen Sie Ihr Transportmittel bereits? Teilen Sie es uns (Bus oder Auto) bei Ihrer Angebotsanfrage mit.</p>",
    },
    "weekend-program": {
        "nl": "<h3>Vrijdag</h3><ul><li>Aankomst</li><li>Check-in</li><li>Avondeten</li><li>Vlaggenparade</li></ul><h3>Zaterdag</h3><ul><li>Toernooidag 1</li><li>Avondactiviteiten</li></ul><h3>Zondag</h3><ul><li>Toernooidag 2</li><li>Finales</li><li>Prijsuitreikingen</li><li>Mogelijk vertrek op zondagavond</li></ul><h3>Maandag</h3><ul><li>Mogelijk vertrek op maandagochtend</li></ul>",
        "fr": "<h3>Vendredi</h3><ul><li>Arrivée</li><li>Enregistrement</li><li>Dîner</li><li>Parade des drapeaux</li></ul><h3>Samedi</h3><ul><li>Jour 1 du tournoi</li><li>Activités en soirée</li></ul><h3>Dimanche</h3><ul><li>Jour 2 du tournoi</li><li>Finales</li><li>Remises des prix</li><li>Départ possible le dimanche soir</li></ul><h3>Lundi</h3><ul><li>Départ possible le lundi matin</li></ul>",
        "de": "<h3>Freitag</h3><ul><li>Ankunft</li><li>Check-in</li><li>Abendessen</li><li>Flaggenparade</li></ul><h3>Samstag</h3><ul><li>Turniertag 1</li><li>Abendaktivitäten</li></ul><h3>Sonntag</h3><ul><li>Turniertag 2</li><li>Finals</li><li>Siegerehrungen</li><li>Mögliche Abreise am Sonntagabend</li></ul><h3>Montag</h3><ul><li>Mögliche Abreise am Montagmorgen</li></ul>",
    },
}

BUTTON_LABEL_TRANSLATIONS = {
    "packages-tariffs": {
        "nl": "Vraag een offerte op maat aan",
        "fr": "Demandez une offre personnalisée",
        "de": "Fordern Sie ein persönliches Angebot an",
    },
}

FAQ_TRANSLATIONS = [
    {
        "en": ("When can we arrive?", "Arrival is planned for Friday 26 March 2027. Exact check-in times are confirmed closer to the tournament."),
        "nl": ("Wanneer kunnen we aankomen?", "De aankomst is gepland op vrijdag 26 maart 2027. De exacte check-in-tijden worden bevestigd dichter bij het toernooi."),
        "fr": ("Quand pouvons-nous arriver ?", "L'arrivée est prévue le vendredi 26 mars 2027. Les horaires exacts d'enregistrement seront confirmés à l'approche du tournoi."),
        "de": ("Wann können wir ankommen?", "Die Ankunft ist für Freitag, den 26. März 2027, geplant. Die genauen Check-in-Zeiten werden näher am Turnier bestätigt."),
    },
    {
        "en": ("Where do we check in?", "Check-in happens at your assigned accommodation on Friday. You'll receive the exact location together with your confirmed offer."),
        "nl": ("Waar checken we in?", "Inchecken gebeurt bij je toegewezen accommodatie op vrijdag. Je ontvangt de exacte locatie samen met je bevestigde offerte."),
        "fr": ("Où enregistrons-nous notre arrivée ?", "L'enregistrement se fait le vendredi à votre hébergement attribué. Vous recevrez le lieu exact avec votre offre confirmée."),
        "de": ("Wo checken wir ein?", "Der Check-in erfolgt am Freitag in Ihrer zugewiesenen Unterkunft. Den genauen Ort erhalten Sie zusammen mit Ihrem bestätigten Angebot."),
    },
    {
        "en": ("What do we need to bring for sleeping?", "Accommodation is basic group accommodation with camp beds - bring your own sleeping bag, mat and personal sleeping equipment."),
        "nl": ("Wat moeten we meebrengen om te slapen?", "De accommodatie is eenvoudige groepsaccommodatie met veldbedden - breng je eigen slaapzak, matje en persoonlijk slaapmateriaal mee."),
        "fr": ("Que devons-nous apporter pour dormir ?", "L'hébergement est un hébergement de groupe basique avec lits de camp - apportez votre propre sac de couchage, matelas et matériel de couchage personnel."),
        "de": ("Was müssen wir zum Schlafen mitbringen?", "Die Unterkunft ist eine einfache Gruppenunterkunft mit Feldbetten - bringen Sie Ihren eigenen Schlafsack, Ihre Isomatte und persönliche Schlafausrüstung mit."),
    },
    {
        "en": ("Are meals included?", "Yes - Friday dinner, and breakfast and dinner on both Saturday and Sunday are included in your package."),
        "nl": ("Zijn maaltijden inbegrepen?", "Ja - avondeten op vrijdag, en ontbijt en avondeten op zowel zaterdag als zondag zijn inbegrepen in je pakket."),
        "fr": ("Les repas sont-ils inclus ?", "Oui - le dîner du vendredi, ainsi que le petit-déjeuner et le dîner du samedi et du dimanche, sont inclus dans votre formule."),
        "de": ("Sind Mahlzeiten inbegriffen?", "Ja - Abendessen am Freitag sowie Frühstück und Abendessen am Samstag und Sonntag sind in Ihrem Paket enthalten."),
    },
    {
        "en": ("Can you provide vegetarian meals?", "Yes, vegetarian, vegan and allergy-friendly meals are available, but must be requested in advance - availability cannot be guaranteed without reservation."),
        "nl": ("Kunnen jullie vegetarische maaltijden voorzien?", "Ja, vegetarische, veganistische en allergievriendelijke maaltijden zijn beschikbaar, maar moeten op voorhand aangevraagd worden - beschikbaarheid kan niet gegarandeerd worden zonder reservatie."),
        "fr": ("Pouvez-vous proposer des repas végétariens ?", "Oui, des repas végétariens, végans et adaptés aux allergies sont disponibles, mais doivent être demandés à l'avance - la disponibilité ne peut être garantie sans réservation."),
        "de": ("Können Sie vegetarische Mahlzeiten anbieten?", "Ja, vegetarische, vegane und allergikerfreundliche Mahlzeiten sind verfügbar, müssen aber im Voraus angefragt werden - ohne Reservierung kann die Verfügbarkeit nicht garantiert werden."),
    },
    {
        "en": ("Is transport provided?", "Let us know your transport method (bus or car) when you request your offer. Shuttle and parking details will be published under Practical Info closer to the tournament."),
        "nl": ("Wordt er vervoer voorzien?", "Laat ons je vervoerswijze weten (bus of auto) bij het aanvragen van je offerte. Shuttle- en parkeerinformatie wordt gepubliceerd onder Praktische Info dichter bij het toernooi."),
        "fr": ("Le transport est-il assuré ?", "Indiquez-nous votre moyen de transport (bus ou voiture) lors de votre demande d'offre. Les informations sur la navette et le parking seront publiées dans les Infos pratiques à l'approche du tournoi."),
        "de": ("Wird ein Transport bereitgestellt?", "Teilen Sie uns bei Ihrer Angebotsanfrage Ihr Transportmittel (Bus oder Auto) mit. Shuttle- und Parkinformationen werden näher am Turnier unter Praktische Infos veröffentlicht."),
    },
    {
        "en": ("Where can our bus park?", "Parking information per sports hall will be published on the Locations page and in the downloadable Parking Maps."),
        "nl": ("Waar kan onze bus parkeren?", "Parkeerinformatie per sporthal wordt gepubliceerd op de pagina Locaties en in de downloadbare Parkeerplannen."),
        "fr": ("Où notre bus peut-il se garer ?", "Les informations de parking par salle de sport seront publiées sur la page Lieux et dans les Plans de parking téléchargeables."),
        "de": ("Wo kann unser Bus parken?", "Parkinformationen pro Sporthalle werden auf der Seite Standorte und in den herunterladbaren Parkplänen veröffentlicht."),
    },
    {
        "en": ("When is the deposit refunded?", "Deposit conditions are confirmed together with your personalised offer - see your accommodation agreement for the exact terms."),
        "nl": ("Wanneer wordt de waarborg terugbetaald?", "De waarborgvoorwaarden worden bevestigd samen met je offerte op maat - zie je accommodatieovereenkomst voor de exacte voorwaarden."),
        "fr": ("Quand la caution est-elle remboursée ?", "Les conditions de la caution sont confirmées avec votre offre personnalisée - consultez votre contrat d'hébergement pour les conditions exactes."),
        "de": ("Wann wird die Kaution zurückerstattet?", "Die Kautionsbedingungen werden zusammen mit Ihrem persönlichen Angebot bestätigt - die genauen Bedingungen finden Sie in Ihrer Unterkunftsvereinbarung."),
    },
    {
        "en": ("Can we change the number of participants?", "Minor changes are usually possible up to a certain date before the tournament - contact the Tournament Office as soon as your numbers change."),
        "nl": ("Kunnen we het aantal deelnemers wijzigen?", "Kleine wijzigingen zijn meestal mogelijk tot een bepaalde datum vóór het toernooi - neem contact op met het Tornooisecretariaat zodra je aantallen wijzigen."),
        "fr": ("Pouvons-nous modifier le nombre de participants ?", "De légères modifications sont généralement possibles jusqu'à une certaine date avant le tournoi - contactez le secrétariat du tournoi dès que vos effectifs changent."),
        "de": ("Können wir die Teilnehmerzahl ändern?", "Kleinere Änderungen sind in der Regel bis zu einem bestimmten Datum vor dem Turnier möglich - kontaktieren Sie das Turnierbüro, sobald sich Ihre Zahlen ändern."),
    },
    {
        "en": ("Can players participate in multiple teams?", "This depends on the category and eligibility rules - see the Tournament Rules document."),
        "nl": ("Kunnen spelers in meerdere teams spelen?", "Dit hangt af van de categorie- en deelnameregels - zie het document Toernooireglement."),
        "fr": ("Les joueurs peuvent-ils participer dans plusieurs équipes ?", "Cela dépend des règles de catégorie et d'éligibilité - consultez le document Règlement du tournoi."),
        "de": ("Können Spieler in mehreren Teams mitspielen?", "Dies hängt von den Kategorie- und Teilnahmeregeln ab - siehe das Dokument Turnierregeln."),
    },
    {
        "en": ("Which ball size is used?", "Ball sizes per category are listed in the Tournament Rules document."),
        "nl": ("Welke balmaat wordt gebruikt?", "Balmaten per categorie staan vermeld in het document Toernooireglement."),
        "fr": ("Quelle taille de ballon est utilisée ?", "Les tailles de ballon par catégorie sont indiquées dans le document Règlement du tournoi."),
        "de": ("Welche Ballgröße wird verwendet?", "Die Ballgrößen pro Kategorie sind im Dokument Turnierregeln aufgeführt."),
    },
    {
        "en": ("What happens if we cancel?", "Cancellation conditions are part of your offer/accommodation agreement - contact the Tournament Office directly if this applies to you."),
        "nl": ("Wat gebeurt er als we annuleren?", "Annuleringsvoorwaarden maken deel uit van je offerte-/accommodatieovereenkomst - neem rechtstreeks contact op met het Tornooisecretariaat als dit op jou van toepassing is."),
        "fr": ("Que se passe-t-il en cas d'annulation ?", "Les conditions d'annulation font partie de votre offre/contrat d'hébergement - contactez directement le secrétariat du tournoi si cela vous concerne."),
        "de": ("Was passiert, wenn wir stornieren?", "Stornierungsbedingungen sind Teil Ihres Angebots-/Unterkunftsvertrags - kontaktieren Sie bei Bedarf direkt das Turnierbüro."),
    },
]


def migrate_rich_text(page, block):
    if isinstance(block.data.get("html"), dict):
        print(f"  = {page.slug} (rich_text, block {block.id}) al gemigreerd")
        return False
    translations = RICH_TEXT_TRANSLATIONS.get(page.slug)
    if translations is None:
        print(f"  ! {page.slug} (rich_text, block {block.id}) - geen vertaling gevonden, overgeslagen")
        return False
    en_html = block.data.get("html") or ""
    block.data = {**block.data, "html": {"en": en_html, **translations}}
    print(f"  + {page.slug} (rich_text, block {block.id}) gemigreerd + vertaald")
    return True


def migrate_button(page, block):
    if isinstance(block.data.get("label"), dict):
        print(f"  = {page.slug} (button, block {block.id}) al gemigreerd")
        return False
    translations = BUTTON_LABEL_TRANSLATIONS.get(page.slug, {})
    en_label = block.data.get("label") or ""
    block.data = {**block.data, "label": {"en": en_label, "nl": "", "fr": "", "de": "", **translations}}
    print(f"  + {page.slug} (button, block {block.id}) gemigreerd + vertaald")
    return True


def migrate_faq(page, block):
    items = block.data.get("items") or []
    if items and isinstance(items[0].get("vraag"), dict):
        print(f"  = {page.slug} (faq, block {block.id}) al gemigreerd")
        return False
    if len(items) != len(FAQ_TRANSLATIONS):
        print(f"  ! {page.slug} (faq, block {block.id}) - aantal vragen ({len(items)}) komt niet overeen met de vertalingen ({len(FAQ_TRANSLATIONS)}), overgeslagen")
        return False
    new_items = []
    for item, vertaling in zip(items, FAQ_TRANSLATIONS):
        new_items.append({
            "vraag": {"en": item.get("vraag", ""), "nl": vertaling["nl"][0], "fr": vertaling["fr"][0], "de": vertaling["de"][0]},
            "antwoord": {"en": item.get("antwoord", ""), "nl": vertaling["nl"][1], "fr": vertaling["fr"][1], "de": vertaling["de"][1]},
        })
    block.data = {**block.data, "items": new_items}
    print(f"  + {page.slug} (faq, block {block.id}) gemigreerd + vertaald ({len(new_items)} vragen)")
    return True


def run():
    app = create_app("development")
    with app.app_context():
        pages = Page.query.order_by(Page.slug).all()
        changed = 0
        for page in pages:
            for block in page.blocks:
                if block.block_type == "rich_text":
                    changed += migrate_rich_text(page, block)
                elif block.block_type == "button":
                    changed += migrate_button(page, block)
                elif block.block_type == "faq":
                    changed += migrate_faq(page, block)
        db.session.commit()
        print(f"\nKlaar: {changed} blok(ken) gemigreerd naar meertalige content.")


if __name__ == "__main__":
    run()
