"""
extensions.py
-------------
Hier worden Flask-extensies (zoals de database) één keer aangemaakt,
los van app.py en models.py. Dat voorkomt "circular import"-problemen:
zowel app.py als models.py kunnen dit bestand importeren zonder dat ze
elkaar nodig hebben.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(get_remote_address, default_limits=["200 per day", "50 per hour"])
