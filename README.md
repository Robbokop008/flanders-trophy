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
│   └── url_validation.py                       # Validatie van knop-/video-URL's
├── scripts/
│   └── create_admin.py                            # Maakt de eerste admin-gebruiker aan
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

## Nog te doen

Dit is een scaffold, geen afgewerkte site. Voor je dit live zet:

- **Echte inhoud**: alle pagina's, tekst en navigatie zijn leeg/placeholder.
  Bouw de eigenlijke toernooi-informatie op via `/admin/pages` en
  `/admin/navigation`.
- **Eigen huisstijl**: `static/style.css` is 1-op-1 overgenomen van de
  hoofdclubsite als werkend startpunt (de admin-CMS-styling werkt meteen),
  maar de kleuren/lettertype/logo zijn nog de clubkleuren - zie de TODO-
  comment bovenaan dat bestand.
- **Favicon en eigen afbeeldingen**: `static/images/` is leeg (enkel een
  `.gitkeep`); er is nog geen favicon of hero-afbeelding voor de homepage.
- **SECRET_KEY**: genereer een echte, geheime waarde voor `.env` voor je
  in productie draait - `create_app()` weigert anders op te starten met
  `config_name="production"`.
- **Flask-Migrate** voor nette databasemigraties i.p.v. `db.create_all()`.
- **Deployment**: `wsgi.py` is klaar voor een productieserver (bv.
  `gunicorn wsgi:app`), maar er is nog geen hosting/CI ingericht.
