"""
wsgi.py
-------
WSGI-instappunt voor productie. Flask's ingebouwde ontwikkelserver
(run.py, app.run(debug=True)) is niet geschikt om live te draaien - een
productieserver zoals gunicorn heeft een WSGI-callable nodig die het bij
het opstarten kan importeren, vandaar dit bestand.

Gebruik (bv. als Render start command):
    gunicorn wsgi:app
"""

from app import create_app

app = create_app("production")
