-- MSSP Ops App — seed data
--
-- Applied ONCE, only when a brand-new database is created on first run.
-- Versioned in Git so the starting dataset is reproducible without committing
-- the live *.db file. Billing/ops metadata only — no PHI.

INSERT INTO clients (name, tenant_domain, primary_contact, status, notes)
VALUES ('Cornerpost Counseling', 'cornerpostcounseling.com', 'Lisa', 'active',
        'Seed client.');

-- Service lines for the seed client (client_id resolved by name to stay robust).
-- market_value = what the line is worth to the client standalone; it powers the
-- Module #2 value-justification story. The numbers below are EXAMPLE placeholders
-- (queued lines are the upsell/roadmap) — edit them to your real pricing.
INSERT INTO services (client_id, service_name, status, resale_price, market_value)
SELECT id, 'Managed Security Service', 'billable', 200, 200
FROM clients WHERE name = 'Cornerpost Counseling';

INSERT INTO services (client_id, service_name, status, market_value)
SELECT id, 'Huntress MDR/EDR', 'queued', 130        -- example value, edit to real
FROM clients WHERE name = 'Cornerpost Counseling';

INSERT INTO services (client_id, service_name, status, market_value)
SELECT id, 'Huntress Security Awareness Training', 'queued', 40   -- example value
FROM clients WHERE name = 'Cornerpost Counseling';

INSERT INTO services (client_id, service_name, status, market_value)
SELECT id, 'Managed Backup', 'queued', 60           -- example value, edit to real
FROM clients WHERE name = 'Cornerpost Counseling';
