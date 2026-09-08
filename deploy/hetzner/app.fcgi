#!/usr/home/drf93y/virtualenvs/flanders_trophy/bin/python
"""
app.fcgi
--------
FastCGI-wrapper om deze Flask-app te draaien op Hetzner Webhosting (Apache +
mod_fcgid), waar geen mod_wsgi beschikbaar is - zie de officiële Hetzner-
tutorial "Run Flask app on Webhosting or Managed Server". Apache spreekt dit
bestand aan via de RewriteRule in .htaccess, niet rechtstreeks een gebruiker.

Voor gebruik: pas hieronder <KONSOLEH_GEBRUIKER> aan (2x) en het pad naar de
projectmap, upload dit bestand naast wsgi.py, en zet het uitvoerbaar:
    chmod 744 app.fcgi
"""

import sys

sys.path.insert(0, "/usr/home/drf93y/flanders-trophy")

from flup.server.fcgi import WSGIServer

from wsgi import app as flask_app


class ScriptNameStripper:
    """Apache's RewriteRule stuurt requests via dit script door; zonder
    SCRIPT_NAME leeg te maken denkt Flask dat elke URL onder /app.fcgi/...
    valt, en kloppen url_for()-links en routing niet meer."""

    def __init__(self, wrapped_app):
        self.wrapped_app = wrapped_app

    def __call__(self, environ, start_response):
        environ["SCRIPT_NAME"] = ""
        return self.wrapped_app(environ, start_response)


if __name__ == "__main__":
    WSGIServer(ScriptNameStripper(flask_app)).run()
