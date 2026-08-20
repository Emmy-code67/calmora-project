"""
Calmora - Entry point
---------------------
Run with:  python run.py
(or `flask --app run run` / `flask run` after setting FLASK_APP=run.py)
"""

import os
from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
