"""Entry point: build the DB on first run and serve the UI on localhost.

    python run.py

Then open http://127.0.0.1:5000 in your browser. Bound to localhost only —
this is a single-operator local tool, not a network service.
"""

from app import create_app

if __name__ == "__main__":
    app = create_app()
    # host=127.0.0.1 keeps it off the network; debug stays off for a real tool.
    app.run(host="127.0.0.1", port=5000, debug=False)
