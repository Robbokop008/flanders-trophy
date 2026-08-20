"""
run.py
------
Startpunt voor lokale development. Draai dit bestand om de site lokaal
te bekijken op http://127.0.0.1:5000

    python run.py
"""

from app import create_app

app = create_app("development")

if __name__ == "__main__":
    app.run(debug=True)
