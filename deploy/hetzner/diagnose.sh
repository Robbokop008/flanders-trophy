#!/bin/bash
# Tijdelijk diagnostisch script. Verwijder na gebruik.

echo "=== bestaat/rechten van de virtualenv-python zelf? ==="
ls -la /usr/home/drf93y/virtualenvs/flanders_trophy/bin/python
file /usr/home/drf93y/virtualenvs/flanders_trophy/bin/python 2>&1

echo
echo "=== is het een symlink? waar wijst die naartoe? ==="
readlink -f /usr/home/drf93y/virtualenvs/flanders_trophy/bin/python

echo
echo "=== kan die python direct (niet via shebang) uitgevoerd worden? ==="
/usr/home/drf93y/virtualenvs/flanders_trophy/bin/python --version
echo "exit code: $?"

echo
echo "=== rechten van app.fcgi zelf, opnieuw bevestigen ==="
ls -la /usr/home/drf93y/public_html/flanders-trophy-public/app.fcgi

echo
echo "=== rechten van de virtualenv-map zelf (bin/) ==="
ls -la /usr/home/drf93y/virtualenvs/flanders_trophy/bin/ | head -5

echo
echo "=== rechten van de tussenliggende mappen ==="
ls -ld /usr/home/drf93y/virtualenvs /usr/home/drf93y/virtualenvs/flanders_trophy /usr/home/drf93y/public_html /usr/home/drf93y/public_html/flanders-trophy-public
