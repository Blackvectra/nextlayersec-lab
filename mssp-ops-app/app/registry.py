"""Module #1 — Client & Service Registry.

Business logic for clients and their service lines: CRUD, the typo-duplicate
name guard, dashboard rollups (MRR + margin), and JSON export/import.

Margin and MRR are COMPUTED here, never stored. Billing/ops metadata only.
"""

from datetime import datetime

from .db import get_connection

CLIENT_STATUSES = ("active", "prospect", "inactive")
SERVICE_STATUSES = ("queued", "active", "billable")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _levenshtein(a, b):
    """Edit distance between two strings (insert/delete/substitute).

    Small standard-library implementation — used only to warn about likely
    typo-duplicate client names, so performance is a non-issue.
    """
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def find_similar_names(name, exclude_id=None, threshold=2):
    """Return existing client names that are a near-match to ``name``.

    Near-match = case-insensitive equality OR small Levenshtein distance
    (<= threshold). Used to warn before saving a likely typo duplicate
    (e.g. "Cornerpost" vs "CounterPost"). ``exclude_id`` skips the row being
    edited so a client is never flagged against itself.
    """
    name = (name or "").strip()
    if not name:
        return []

    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, name FROM clients").fetchall()
    finally:
        conn.close()

    matches = []
    for row in rows:
        if exclude_id is not None and row["id"] == exclude_id:
            continue
        if _levenshtein(name, row["name"]) <= threshold:
            matches.append(row["name"])
    return matches


# ---------------------------------------------------------------------------
# Clients CRUD
# ---------------------------------------------------------------------------
def list_clients(status=None, sort="name"):
    """Return clients, optionally filtered by status, with sort by name/status."""
    sort_col = "status" if sort == "status" else "name"
    sql = "SELECT * FROM clients"
    params = []
    if status in CLIENT_STATUSES:
        sql += " WHERE status = ?"
        params.append(status)
    sql += f" ORDER BY {sort_col} COLLATE NOCASE ASC"

    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def get_client(client_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM clients WHERE id = ?", (client_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_client(data):
    now = _now()
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO clients
                 (name, tenant_domain, primary_contact, status, notes,
                  created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                data["name"].strip(),
                (data.get("tenant_domain") or "").strip() or None,
                (data.get("primary_contact") or "").strip() or None,
                data.get("status", "prospect"),
                (data.get("notes") or "").strip() or None,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_client(client_id, data):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE clients SET
                 name = ?, tenant_domain = ?, primary_contact = ?,
                 status = ?, notes = ?, updated_at = ?
               WHERE id = ?""",
            (
                data["name"].strip(),
                (data.get("tenant_domain") or "").strip() or None,
                (data.get("primary_contact") or "").strip() or None,
                data.get("status", "prospect"),
                (data.get("notes") or "").strip() or None,
                _now(),
                client_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_client(client_id):
    # Service lines are removed automatically via ON DELETE CASCADE.
    conn = get_connection()
    try:
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Services CRUD
# ---------------------------------------------------------------------------
def list_services(client_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM services WHERE client_id = ? ORDER BY id ASC",
            (client_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create_service(client_id, data):
    now = _now()
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO services
                 (client_id, service_name, status, tool_cost, resale_price,
                  market_value, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                client_id,
                data["service_name"].strip(),
                data.get("status", "queued"),
                _to_money(data.get("tool_cost")),
                _to_money(data.get("resale_price")),
                _to_money(data.get("market_value")),
                (data.get("notes") or "").strip() or None,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_service(service_id, data):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE services SET
                 service_name = ?, status = ?, tool_cost = ?,
                 resale_price = ?, market_value = ?, notes = ?, updated_at = ?
               WHERE id = ?""",
            (
                data["service_name"].strip(),
                data.get("status", "queued"),
                _to_money(data.get("tool_cost")),
                _to_money(data.get("resale_price")),
                _to_money(data.get("market_value")),
                (data.get("notes") or "").strip() or None,
                _now(),
                service_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_service(service_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM services WHERE id = ?", (service_id,))
        conn.commit()
    finally:
        conn.close()


def _to_money(value):
    """Normalize a money field to float or None (empty string -> None)."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Dashboard rollups — MRR and margin counted from BILLABLE services only
# ---------------------------------------------------------------------------
def _service_margin(svc):
    """resale_price - tool_cost, treating missing values as 0."""
    return (svc.get("resale_price") or 0) - (svc.get("tool_cost") or 0)


def build_dashboard(status=None, sort="name"):
    """Assemble the full registry view: every client with its service lines,
    per-client MRR + margin (billable only), and a portfolio rollup.
    """
    clients = list_clients(status=status, sort=sort)

    portfolio_mrr = 0.0
    portfolio_margin = 0.0

    for client in clients:
        services = list_services(client["id"])
        client_mrr = 0.0
        client_margin = 0.0
        for svc in services:
            svc["margin"] = _service_margin(svc)
            # Only BILLABLE services count toward recurring revenue/margin.
            if svc["status"] == "billable":
                client_mrr += svc.get("resale_price") or 0
                client_margin += svc["margin"]
        client["services"] = services
        client["mrr"] = round(client_mrr, 2)
        client["margin"] = round(client_margin, 2)
        portfolio_mrr += client_mrr
        portfolio_margin += client_margin

    return {
        "clients": clients,
        "portfolio": {
            "total_mrr": round(portfolio_mrr, 2),
            "total_margin": round(portfolio_margin, 2),
            "client_count": len(clients),
        },
    }


# ---------------------------------------------------------------------------
# JSON export / import (backup + versioning). Export files are gitignored.
# ---------------------------------------------------------------------------
def export_registry():
    """Return the whole registry as a plain dict ready for JSON serialization."""
    clients = list_clients()
    for client in clients:
        client["services"] = list_services(client["id"])
    return {
        "exported_at": _now(),
        "schema": "mssp-registry-v1",
        "clients": clients,
    }


def import_registry(payload, replace=True):
    """Import a previously exported registry.

    With ``replace=True`` the current clients/services are cleared first so the
    import is an exact restore (default — matches a backup-restore workflow).
    Returns a count of imported clients and services.
    """
    clients = payload.get("clients", [])
    now = _now()

    conn = get_connection()
    try:
        if replace:
            conn.execute("DELETE FROM services")
            conn.execute("DELETE FROM clients")

        n_clients = 0
        n_services = 0
        for c in clients:
            cur = conn.execute(
                """INSERT INTO clients
                     (name, tenant_domain, primary_contact, status, notes,
                      created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    c.get("name"),
                    c.get("tenant_domain"),
                    c.get("primary_contact"),
                    c.get("status", "prospect"),
                    c.get("notes"),
                    c.get("created_at") or now,
                    c.get("updated_at") or now,
                ),
            )
            new_id = cur.lastrowid
            n_clients += 1
            for s in c.get("services", []):
                conn.execute(
                    """INSERT INTO services
                         (client_id, service_name, status, tool_cost,
                          resale_price, market_value, notes,
                          created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        new_id,
                        s.get("service_name"),
                        s.get("status", "queued"),
                        _to_money(s.get("tool_cost")),
                        _to_money(s.get("resale_price")),
                        _to_money(s.get("market_value")),
                        s.get("notes"),
                        s.get("created_at") or now,
                        s.get("updated_at") or now,
                    ),
                )
                n_services += 1
        conn.commit()
        return {"clients": n_clients, "services": n_services}
    finally:
        conn.close()
