# MSSP Ops App

A local, single-operator business-operations app for running a small MSSP.
Zero recurring cost, no cloud — it runs entirely on your laptop and stores data
in a local SQLite file. This is the **foundation + Module&nbsp;1 (Client &
Service Registry)**; it's structured so further modules can be added cleanly.

## Stack

- **Python 3.11+**, standard library where practical
- **SQLite** (file-based, on disk) — built automatically on first run
- **Flask** for a minimal single-page web UI served on `localhost`

## Quick start

```bash
cd mssp-ops-app
python3 -m venv .venv && source .venv/bin/activate    # optional but recommended
pip install -r requirements.txt
python run.py
```

Then open <http://127.0.0.1:5000>. On first launch the app creates `mssp.db`
from `schema.sql`, applies `seed.sql`, and you'll immediately see the seeded
**Cornerpost Counseling** client with its four service lines.

To start over from scratch, stop the app, delete `mssp.db`, and run again.

## Module 1 — Client & Service Registry

- **CRUD** for clients and for the service lines under each client.
- **Typo-duplicate guard:** when adding/editing a client, names that are a
  near-match to an existing client (case-insensitive, small edit distance —
  e.g. "Cornerpost" vs "CounterPost") trigger a warning before saving.
- **Dashboard:** every client with its service lines and statuses, the
  per-client monthly recurring total (MRR) and margin total, and a portfolio
  rollup (total MRR, total margin). **Only services marked `billable` count**
  toward MRR and margin.
- **Filter & sort** the registry by status.
- **Export / import** the whole registry as JSON for backup/versioning. Exports
  are written to `exports/` (gitignored) and downloaded to your browser.

Margin (`resale_price − tool_cost`) is **computed at read time, never stored.**

### Service / client statuses

- Client: `active`, `prospect`, `inactive`
- Service: `queued`, `active`, `billable` (billable = counted in MRR/margin)

## Data handling

- **This repo is private** and versions **code only** — never client or pricing
  data.
- The database (`*.db`/`*.sqlite*`) and all JSON exports (`exports/`,
  `*.export.json`) are **gitignored and never committed**. The structure and
  seed data live in `schema.sql` / `seed.sql` so the schema is reproducible
  without committing the populated database.
- **No PHI, ever.** This app stores **billing/ops metadata only**: client
  business names, tenant domains, contact names, service line names, statuses,
  notes, and dollar amounts. Do not enter patient, clinical, or health data.

## Project layout

```
mssp-ops-app/
├── run.py              # entry point: python run.py
├── schema.sql          # versioned DB structure (no PHI; see header comment)
├── seed.sql            # versioned seed data, applied once on first run
├── requirements.txt
├── README.md
├── .gitignore          # excludes *.db, exports/, *.export.json, etc.
└── app/
    ├── __init__.py     # Flask app factory + JSON API routes
    ├── db.py           # connection + first-run init from schema/seed
    ├── registry.py     # Module 1 logic: CRUD, name guard, rollups, export/import
    ├── templates/index.html
    └── static/{app.js, style.css}
```

## Where future modules plug in

The app is a Flask package with a thin route layer in `app/__init__.py` over a
domain module (`app/registry.py`) and a shared `app/db.py`. Future modules slot
in as sibling domain modules with their own route groups and, where needed,
additional tables added to `schema.sql`:

- a **billing-decision engine** would read the same `services` table and layer
  on rules (e.g. promote `queued`→`billable`, flag thin margins) in a new
  `app/billing.py`;
- a **deliverable generator** and a **quote/contract generator** would each be a
  new domain module that reads client/service rows and renders documents,
  exposed through new routes and a new UI section in the existing single page.

No existing code needs to be rewritten to add them — add a module, add its
routes, extend the schema if it needs new tables.
