# Flanders Trophy - Website

Flask-project voor de Flanders Trophy-toernooiwebsite. Dit is een scaffold:
de admin-CMS (pagina's + navigatie) is volledig werkend, met dezelfde opzet
als de hoofdclubsite (Handbal Sint-Truiden), maar de echte toernooi-inhoud
en huisstijl moeten nog ingevuld worden.

## Projectstructuur

```
flanders-trophy/
├── app.py                # Application factory
├── run.py                # Startpunt voor lokale development
├── wsgi.py                 # WSGI-instappunt voor productie (gunicorn wsgi:app)
├── config.py                 # Instellingen (dev/productie, mail, uploads)
├── extensions.py                # db, csrf, limiter - centraal geïnitialiseerd
├── models.py                       # SQLAlchemy-modellen: User, NavItem, Page, PageBlock
├── routes/
│   ├── main.py                        # Home, contact (publiek)
│   ├── auth.py                          # Login/logout (admin-only, geen publieke registratie)
│   ├── pages.py                           # Publieke weergave van CMS-pagina's: /pagina/<slug>
│   └── admin.py                             # Adminpaneel: pagina's + navigatie + gebruikers
├── utils/
│   ├── auth.py                  # @login_required / @admin_required decorators
│   ├── mail.py                     # Contactformulier-mail (Gmail SMTP)
│   ├── sanitize.py                    # Saniteert rich-text HTML (bleach) vóór opslag
│   ├── nav.py                            # Bouwt de navbar-boom op uit NavItem's
│   ├── page_blocks.py                       # Stijl-defaults + afbeeldingen-opruiming per blok
│   ├── i18n.py                                 # Taalkeuze + per-taal velden (auto_translate_i18n_field)
│   ├── translate.py                               # DeepL-wrapper, gebruikt door utils/i18n.py
│   └── url_validation.py                       # Validatie van knop-/video-URL's
├── scripts/
│   ├── create_admin.py                            # Maakt de eerste admin-gebruiker aan
│   └── migrate_page_title_i18n.py                    # Eenmalig: Page.title_i18n toevoegen + vertalen
├── templates/
│   ├── base.html                     # Gedeelde publieke layout (header/nav/footer),
│   │                                    navbar wordt gerenderd uit nav_tree (zie utils/nav.py)
│   ├── index.html                      # Placeholder-homepage
│   ├── pages/view.html                   # Generieke weergave van een CMS-pagina
│   ├── pages/_blocks/                      # Eén template per bloktype (tekst, afbeelding(en),
│   │                                          kolommen, video, knop, citaat, FAQ, statistieken, embed)
│   ├── admin/                                # Adminomgeving, eigen sidebar-shell (niet de
│   │                                            publieke header/footer)
│   │   ├── _shell.html                           # Sidebar-layout, door alle adminpagina's geëxtend
│   │   ├── dashboard.html                          # Welkomstscherm met paginatelling + snelkoppelingen
│   │   ├── pages_list.html / page_form.html /        # Pagina's beheren (incl. Quill-editor
│   │   │   page_canvas.html / page_block_form.html     via static/vendor/quill/)
│   │   ├── navigation.html / _nav_item.html            # Navigatie beheren (boom + drag-and-drop
│   │   │                                                 via static/vendor/sortablejs/)
│   │   └── users_list.html                               # Read-only gebruikerslijst
│   └── errors/                               # 404 / 429
├── static/
│   ├── style.css                        # Sitebrede stylesheet (nog clubkleuren, zie TODO's)
│   ├── js/                                # admin_page_canvas.js / admin_rich_editor.js
│   ├── images/                              # Geüploade pagina-afbeeldingen komen hier terecht
│   └── vendor/                                # Self-hosted front-end libs (geen CDN/build-stap)
│       ├── quill/                                # Rich-text editor voor pagina's
│       └── sortablejs/                             # Drag-and-drop voor navigatiebeheer
├── instance/                              # SQLite-database (niet in git)
├── requirements.txt
└── .env.example                           # Kopieer naar .env, vul zelf in
```

## Hoe de CMS werkt

Admins (gebruikers met `is_admin=True`) beheren de site vanuit `/admin`:

- **Pagina's** (`/admin/pages`): een pagina (`Page`) is een titel + slug +
  optionele hero-afbeelding, en wordt opgebouwd uit een lijst content-
  **blokken** (`PageBlock`), elk van een vast type: tekst (rich text, Quill-
  editor), afbeelding(en), kolommen, video (YouTube/Vimeo), knop, citaat,
  FAQ, statistieken, of vrije HTML/embed. Blokken zijn los versleepbaar om
  te herordenen, en elk blok heeft gedeelde "weergave"-opties (uitlijning,
  achtergrond, breedte, witruimte). Inhoud wordt bij opslaan altijd
  server-side gesaniteerd (`utils/sanitize.py`, via `bleach`) voor er
  `| safe` gerenderd wordt.
- **Navigatie** (`/admin/navigation`): de volledige navbar is data
  (`NavItem`, een zelf-refererende boom) i.p.v. hardcoded in
  `templates/base.html`. Items kunnen linken naar een pagina, een vaste
  Flask-route (bv. `main.contact`), of een externe URL, en kunnen
  gegroepeerd worden in dropdown-categorieën. Herordenen/verplaatsen kan
  via slepen (SortableJS) of de pijltjes/select-alternatieven.

## Meertalige publieke site (EN/NL/FR/DE)

De publieke site ondersteunt 4 talen via Flask-Babel, **sessie-gebaseerd**
(een `lang`-cookie, geen taalprefix in de URL - zie `utils/i18n.py` voor de
afweging). De taalwisselaar in de navbar linkt naar
`/set-language/<code>?next=<pad>`.

- **Site-chrome** (navigatie, knoppen, formulieren, foutmeldingen) is
  vertaald: statische template-strings staan als `{{ _('...') }}` in de
  templates, en databasewaarden die niet door `pybabel extract` gevonden
  worden (`NavItem.label`, `CONTACT_TOPICS`, team-categorielabels,
  vervoerskeuzes) zijn manueel toegevoegd aan `translations/messages.pot`
  (zie de commentaar daar) en dus ook vertaalbaar via diezelfde `_()`. De
  titels van de oorspronkelijke MVP-pagina's staan hier historisch ook nog
  tussen (handmatig vertaald) - zie hieronder waarom nieuwere paginatitels
  dat pad niet meer gebruiken.
- **CMS-paginatitels en -inhoud** (de content-blokken: rich text,
  FAQ-antwoorden, ...) worden per taal opgeslagen op `Page.title_i18n`
  resp. in elk `PageBlock.data`-veld (zie `utils/i18n.py`), en **automatisch
  aangevuld via de DeepL API** zodra een admin een pagina/blok opslaat met
  minstens 1 taal ingevuld (zie `utils/translate.py`,
  `utils/i18n.auto_translate_i18n_field`, en het inpluggen ervan in
  `routes/admin.py`). Dit vereist een `DEEPL_API_KEY` in `.env`
  (`.env.example`) - zonder key blijft opslaan gewoon werken, enkel zonder
  automatische vertaling (een leeg gebleven taalveld valt dan terug op de
  eerst ingevulde taal, zie `utils/i18n.resolve_i18n_field`). Bestaande
  pagina's zijn eenmalig gemigreerd/vertaald via
  `scripts/migrate_page_title_i18n.py`.
- **Vertalingen bijwerken/uitbreiden**: pas de `{{ _('...') }}`-strings aan
  of voeg toe, draai dan
  `pybabel extract -F babel.cfg -o translations/messages.pot .`,
  update de 3 `translations/<taal>/LC_MESSAGES/messages.po`-bestanden met de
  nieuwe/gewijzigde `msgid`'s (denk ook aan de manueel toegevoegde
  DB-string-`msgid`'s als je daar iets aan wijzigt), en compileer met
  `pybabel compile -d translations`.

## Lokaal opstarten

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # vul je eigen SECRET_KEY/Gmail-gegevens in
python run.py
```

Site draait dan op **http://127.0.0.1:5000**

## Eerste admin-gebruiker aanmaken

Er is bewust geen publieke registratiepagina op deze site. Maak je eerste
admin-login aan met:

```bash
python scripts/create_admin.py
```

Dit vraagt interactief naar gebruikersnaam/e-mail/wachtwoord (of geef ze
mee als argumenten, zie de docstring bovenaan het script). Opnieuw draaien
met dezelfde gebruikersnaam werkt het wachtwoord van die gebruiker bij
i.p.v. een duplicaat aan te maken. Log daarna in via `/login`.

## Databasebackup

`scripts/backup_db.py` maakt een backup van de SQLite-database: een lokale
kopie in `instance/backups/` (de laatste 14 dagelijkse backups blijven
bewaard, oudere worden automatisch opgeruimd) én een off-server kopie via
e-mail naar `GMAIL_USER` (zie `utils/mail.send_backup_mail`), zodat een
probleem met de server zelf niet ook de enige backup meeneemt.

Draai dit dagelijks via een scheduled task, bv. op PythonAnywhere's
"Tasks"-tabblad:

```bash
python3.x /home/<gebruiker>/flanders-trophy/scripts/backup_db.py
```

Let op: het gratis PythonAnywhere-plan laat doorgaans 1 dagelijkse taak toe;
op een betaald plan kan dit vaker. Het script ondersteunt enkel SQLite (de
huidige productiedatabase) - bij een `DATABASE_URL` naar Postgres stopt het
met een duidelijke melding, want een Postgres-backup vraagt een andere
aanpak (bv. `pg_dump`).

## Foutlogging &amp; monitoring

In productie schrijft de app naar een draaiend logbestand,
`instance/logs/app.log` (max 1 MB × 5 bestanden, zie `app.py`). Onverwachte
serverfouten (HTTP 500) tonen bezoekers een nette foutpagina
(`templates/errors/500.html`) en komen mét volledige traceback in dat
logbestand terecht.

`GET /health` geeft `{"status": "ok"}` (200) terug zolang de database
bereikbaar is, anders `{"status": "error"}` (503) - bedoeld om extern te
laten pingen door een gratis uptime-monitor zoals
[UptimeRobot](https://uptimerobot.com) of [cron-job.org](https://cron-job.org),
zodat een crash of downtime opvalt zonder dat iemand het toevallig moet
melden.

## Nog te doen

Dit is een scaffold, geen afgewerkte site. Voor je dit live zet:

- **Echte inhoud**: alle pagina's, tekst en navigatie zijn leeg/placeholder.
  Bouw de eigenlijke toernooi-informatie op via `/admin/pages` en
  `/admin/navigation`.
- **Logo en favicon**: `static/style.css` is overgenomen van de hoofdclubsite
  als werkend startpunt; de blauw/gele kleuren zijn bewust behouden
  (beslissing 2026-08-21), maar er is nog geen Flanders Trophy-logo of
  favicon. `static/images/` is leeg (enkel een `.gitkeep`). Zodra die er
  zijn: favicon toevoegen en de kleurvariabelen in `:root`
  (`static/style.css`) vervangen als het logo een ander kleurenschema vraagt.
- **SECRET_KEY**: genereer een echte, geheime waarde voor `.env` voor je
  in productie draait - `create_app()` weigert anders op te starten met
  `config_name="production"`.
- **Flask-Migrate** voor nette databasemigraties i.p.v. `db.create_all()`.
- **Deployment**: `wsgi.py` is klaar voor een productieserver (bv.
  `gunicorn wsgi:app`), maar er is nog geen hosting/CI ingericht.
