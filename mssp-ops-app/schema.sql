-- MSSP Ops App — database schema + seed data
--
-- DATA POLICY: This database stores BILLING / OPERATIONS METADATA ONLY.
-- NO PHI (Protected Health Information) is EVER stored here. Permitted data is
-- limited to: client business names, tenant domains, contact names, service
-- line names, statuses, notes, and dollar amounts (tool cost / resale price).
-- Do not add columns that could hold patient, clinical, or health data.
--
-- This file is versioned in Git. The populated *.db file is NOT (see .gitignore).
-- On first run the app builds the database from this file automatically.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- clients: one row per MSSP customer / prospect
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clients (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,                       -- business name
    tenant_domain   TEXT,                                -- e.g. example.com
    primary_contact TEXT,                                -- contact name only
    status          TEXT NOT NULL DEFAULT 'prospect'     -- active|prospect|inactive
                        CHECK (status IN ('active', 'prospect', 'inactive')),
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- services: service lines belonging to a client
-- Margin (resale_price - tool_cost) is COMPUTED at read time, never stored.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS services (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id    INTEGER NOT NULL,
    service_name TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'queued'          -- queued|active|billable
                     CHECK (status IN ('queued', 'active', 'billable')),
    tool_cost    REAL,                                   -- monthly cost to us (nullable)
    resale_price REAL,                                   -- monthly price to client (nullable)
    market_value REAL,                                   -- standalone/retail worth to client (nullable)
    notes        TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_services_client_id ON services (client_id);

-- ---------------------------------------------------------------------------
-- Module #2 — Value & Billing Justification
--
-- Each monthly "run" snapshots a client's service stack so you can show what
-- the client actually receives vs. what you charge them. Billing/ops metadata
-- only — no PHI. delivered_value is the worth of services being provided now
-- (active + billable); charged_amount is what you actually bill. The gap
-- (delivered_value - charged_amount) is the price-justification story.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS billing_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id       INTEGER NOT NULL,
    period          TEXT NOT NULL,                       -- 'YYYY-MM'
    charged_amount  REAL NOT NULL DEFAULT 0,             -- what you actually bill this period
    delivered_value REAL NOT NULL DEFAULT 0,             -- snapshot: worth of active+billable lines
    roadmap_value   REAL NOT NULL DEFAULT 0,             -- snapshot: worth of queued (upsell) lines
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE,
    UNIQUE (client_id, period)                           -- one run per client per month
);

-- Frozen per-service line items for a run (so history is stable even if the
-- live service config later changes).
CREATE TABLE IF NOT EXISTS billing_run_lines (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       INTEGER NOT NULL,
    service_name TEXT NOT NULL,
    status       TEXT NOT NULL,                          -- status at snapshot time
    resale_price REAL,
    value        REAL NOT NULL DEFAULT 0,                -- market_value, falling back to resale_price
    counted      INTEGER NOT NULL DEFAULT 0,             -- 1 if it fed delivered_value
    FOREIGN KEY (run_id) REFERENCES billing_runs (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runs_client_id ON billing_runs (client_id);
CREATE INDEX IF NOT EXISTS idx_run_lines_run_id ON billing_run_lines (run_id);
