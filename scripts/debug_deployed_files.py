# -*- coding: utf-8 -*-
"""
scripts/debug_deployed_files.py
------------------------------------
Alleen-lezend diagnosescript: controleert of de bestanden die effectief op
de server staan de verwachte "offerteknop volgt offer_status"-code bevatten
(zie utils/nav.py, templates/base.html, static/style.css) en of er een
verouderde __pycache__/*.pyc naast utils/nav.py ligt die nieuwere .py-code
zou kunnen overschaduwen.

Wijzigt niets aan bestanden of database.

Gebruik:
    python scripts/debug_deployed_files.py
"""

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _check(relative_path, marker):
    pad = ROOT / relative_path
    if not pad.exists():
        print(f"{relative_path}: BESTAAT NIET op {pad}")
        return
    inhoud = pad.read_text(encoding="utf-8", errors="replace")
    mtime = datetime.fromtimestamp(pad.stat().st_mtime)
    print(
        f"{relative_path}: {pad.stat().st_size} bytes, laatst gewijzigd {mtime}, "
        f"marker {marker!r} gevonden: {marker in inhoud}"
    )


def _check_pycache():
    pycache = ROOT / "utils" / "__pycache__"
    if not pycache.exists():
        print("utils/__pycache__: bestaat niet.")
        return
    nav_source_mtime = (ROOT / "utils" / "nav.py").stat().st_mtime
    for bestand in sorted(pycache.glob("nav.*.pyc")):
        pyc_mtime = bestand.stat().st_mtime
        ouder_dan_source = pyc_mtime < nav_source_mtime
        print(
            f"utils/__pycache__/{bestand.name}: gewijzigd {datetime.fromtimestamp(pyc_mtime)} "
            f"({'OUDER dan nav.py - zou geen probleem mogen zijn, Python checkt de brontijd' if ouder_dan_source else 'nieuwer dan of gelijk aan nav.py'})"
        )


if __name__ == "__main__":
    _check("utils/nav.py", "offer_request_url")
    _check("templates/base.html", "nav-link-disabled")
    _check("static/style.css", "nav-link-disabled")
    _check_pycache()
