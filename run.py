"""
Calmora - Entry point
---------------------
Local run:   python run.py
Flask CLI:   export FLASK_APP=run.py && flask init-db
Vercel:      entrypoint is "run:app" (see pyproject.toml [tool.vercel])
             — Vercel imports this module and calls the WSGI `app` object
             directly, it never executes the __main__ block below.
"""

import os
from dotenv import load_dotenv
load_dotenv()
from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
