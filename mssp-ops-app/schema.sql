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
    notes        TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_services_client_id ON services (client_id);
