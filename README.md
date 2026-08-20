# 🌿 Calmora — Mental Health Management Platform

Calmora is a full-stack, portfolio-quality Flask web application for managing
personal mental wellness: mood tracking, journaling, symptom monitoring,
medication management, therapy appointments, and habit tracking — all backed
by interactive analytics, a unified calendar, global search, and an admin
dashboard.

Built with **Flask, SQLAlchemy, SQLite, Flask-Login, Flask-WTF, Bootstrap 5,
Chart.js, and FullCalendar.js**, following an MVC-style architecture with
Flask Blueprints for a modular, beginner-friendly codebase.

---

## ✨ Features

- **Auth & Profiles** — secure registration/login (hashed passwords via
  Werkzeug), Flask-Login sessions, profile editing with avatar upload,
  password changes.
- **Dashboard** — summary cards, 14-day mood trend chart, habit progress,
  upcoming therapy sessions, recent journal entries.
- **Mood Tracker** — log mood type, intensity, stress level, sleep hours,
  notes. Full CRUD + filter by mood type/date range/keyword/stress + sort +
  pagination + CSV/Excel/PDF export.
- **Journal** — rich entries with mood tags, comma-separated keyword tags,
  favorites, full CRUD, search across title/content/tags, export.
- **Symptom Monitoring** — category, severity (1-5 dot scale), duration,
  triggers, full CRUD + filters + export.
- **Medication Management** — dosage/frequency/reminders, daily dose logging
  (taken/missed/skipped), automatic adherence-rate calculation, export.
- **Therapy Appointments** — schedule sessions with status tracking
  (scheduled/completed/cancelled/no-show), export.
- **Habit Tracking** — daily/weekly habits with one-click check-in, automatic
  streak counting and 30-day completion rate, export.
- **Calendar** — FullCalendar month/week/day/list views aggregating every
  module's events with color coding and drag-and-drop rescheduling.
- **Analytics** — Chart.js dashboards: mood trend + stress overlay, mood
  distribution donut, sleep-vs-stress scatter correlation, symptom frequency
  + average severity, habit completion rates & streaks, medication adherence
  bar chart, medication log status pie chart, and plain-language "wellness
  insights" generated from simple, transparent heuristics.
- **Global Search** — one search box across mood notes, journal entries,
  symptoms, medications, and therapy appointments.
- **Notifications** — in-app notification bell with unread counts.
- **Admin Dashboard** — platform-wide stats, user management (activate/
  deactivate, promote/demote, delete), and a searchable system activity log.
- **Light/Dark Theme** — toggle persisted per-user, calming Headspace/Notion/
  Calm/Linear-inspired design system built on CSS variables.

---

## 🗂 Project Structure

```
calmora/
├── run.py                     # entry point
├── config.py                  # environment-based configuration
├── requirements.txt
├── app/
│   ├── __init__.py            # application factory
│   ├── extensions.py          # db, login_manager, csrf, migrate
│   ├── models.py              # all SQLAlchemy models
│   ├── utils.py                # shared helpers (admin_required, activity log, filters)
│   ├── cli.py                  # `flask init-db` / `flask seed-demo`
│   ├── auth/                   # registration, login, profile
│   ├── main/                   # dashboard
│   ├── mood/                   # mood tracker CRUD
│   ├── journal/                # journaling CRUD
│   ├── symptoms/               # symptom monitoring CRUD
│   ├── medications/             # medication + dose log CRUD
│   ├── therapy/                # therapy appointment CRUD
│   ├── habits/                  # habit tracker + check-ins
│   ├── calendar_view/           # FullCalendar page + JSON events API
│   ├── analytics/               # Chart.js data aggregation
│   ├── search/                  # global search
│   ├── admin/                   # admin dashboard & user management
│   ├── export/                  # CSV / Excel / PDF generators
│   ├── static/                  # css/js/img
│   └── templates/               # Jinja2 templates (one folder per module)
└── instance/                    # SQLite database lives here (gitignored)
```

---

## 🚀 Getting Started

### 1. Clone & create a virtual environment

```bash
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize the database & seed demo data

```bash
export FLASK_APP=run.py          # Windows: set FLASK_APP=run.py
flask init-db                    # creates all tables
flask seed-demo                  # creates demo/admin accounts + sample data
```

### 4. Run the app

```bash
python run.py
```

Visit **http://localhost:5000**.

### Demo credentials

| Role  | Username | Password    |
|-------|----------|-------------|
| User  | `demo`   | `Demo1234!` |
| Admin | `admin`  | `Admin123!` |

---

## 🔐 Security Notes

- Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2).
- CSRF protection is enabled globally via Flask-WTF; every form (including
  raw delete/toggle buttons) carries a CSRF token.
- Set a strong `CALMORA_SECRET_KEY` environment variable before any real
  deployment — the default in `config.py` is for local development only.
- All module queries are scoped to `current_user.id`, so users can never
  view or modify each other's data.

---

## 🧠 Educational Notes

This codebase intentionally favors clarity over cleverness:

- **Application factory pattern** (`create_app()`) avoids circular imports
  and makes testing with different configs trivial.
- **Blueprints** keep each feature module self-contained (`routes.py` +
  `forms.py` + its own `templates/` folder).
- **Shared Jinja macros** (`templates/shared/macros.html`) eliminate
  duplication across the six CRUD modules (mood chips, severity dots,
  status badges, pagination, sort links, empty states).
- **`merge_args()`** is a small template global that preserves query-string
  filters across pagination/sorting links — a common real-world pattern.
- Analytics are computed with plain Python (`collections.defaultdict`) so
  the aggregation logic is easy to read and modify, rather than hidden
  behind complex ORM aggregate queries.

---

## 📦 Tech Stack

| Layer      | Technology                                   |
|------------|-----------------------------------------------|
| Backend    | Flask, Flask-Login, Flask-WTF, Flask-Migrate  |
| Database   | SQLite + SQLAlchemy ORM                        |
| Frontend   | Bootstrap 5, Bootstrap Icons, vanilla JS       |
| Charts     | Chart.js                                       |
| Calendar   | FullCalendar.js                                |
| Exports    | openpyxl (Excel), reportlab (PDF), csv (stdlib)|

---

## 📄 License

This project is provided as an educational portfolio piece. Feel free to
fork, adapt, and extend it.
