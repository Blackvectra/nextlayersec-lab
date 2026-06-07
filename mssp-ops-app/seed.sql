-- MSSP Ops App — seed data
--
-- Applied ONCE, only when a brand-new database is created on first run.
-- Versioned in Git so the starting dataset is reproducible without committing
-- the live *.db file. Billing/ops metadata only — no PHI.

INSERT INTO clients (name, tenant_domain, primary_contact, status, notes)
VALUES ('Cornerpost Counseling', 'cornerpostcounseling.com', 'Lisa', 'active',
        'Seed client.');

-- Service lines for the seed client (client_id resolved by name to stay robust).
INSERT INTO services (client_id, service_name, status, resale_price)
SELECT id, 'Managed Security Service', 'billable', 200
FROM clients WHERE name = 'Cornerpost Counseling';

INSERT INTO services (client_id, service_name, status)
SELECT id, 'Huntress MDR/EDR', 'queued'
FROM clients WHERE name = 'Cornerpost Counseling';

INSERT INTO services (client_id, service_name, status)
SELECT id, 'Huntress Security Awareness Training', 'queued'
FROM clients WHERE name = 'Cornerpost Counseling';

INSERT INTO services (client_id, service_name, status)
SELECT id, 'Managed Backup', 'queued'
FROM clients WHERE name = 'Cornerpost Counseling';
