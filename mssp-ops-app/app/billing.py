"""Module #2 — Value & Billing Justification.

Generates and stores monthly "runs" that snapshot a client's service stack so
you can show what the client actually receives vs. what you charge them. The
gap between delivered value and the amount charged is the price-justification
story (e.g. "you're getting $X of security for $200").

Billing/ops metadata only — no PHI. Margin/value figures are derived from the
services table; runs freeze a snapshot so history stays stable.
"""

import re
from datetime import datetime

from .db import get_connection

# Statuses whose value counts as "delivered now" vs. "roadmap / upsell".
DELIVERED_STATUSES = ("active", "billable")
ROADMAP_STATUSES = ("queued",)

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")  # YYYY-MM


def current_period():
    return datetime.utcnow().strftime("%Y-%m")


def _service_value(svc):
    """What a service line is worth to the client: market_value, falling back
    to resale_price, falling back to 0."""
    if svc.get("market_value") is not None:
        return svc["market_value"]
    if svc.get("resale_price") is not None:
        return svc["resale_price"]
    return 0


# ---------------------------------------------------------------------------
# Generate / preview a run
# ---------------------------------------------------------------------------
def preview_run(client_id):
    """Compute (without saving) the value picture for a client's current stack.

    Returns the per-service lines plus delivered/roadmap totals and a suggested
    charge (sum of billable resale prices) so the UI can pre-fill the amount.
    """
    conn = get_connection()
    try:
        client = conn.execute(
            "SELECT * FROM clients WHERE id = ?", (client_id,)
        ).fetchone()
        if not client:
            return None
        services = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM services WHERE client_id = ? ORDER BY id",
                (client_id,),
            ).fetchall()
        ]
    finally:
        conn.close()

    lines = []
    delivered = 0.0
    roadmap = 0.0
    suggested_charge = 0.0
    for svc in services:
        value = _service_value(svc)
        counted = svc["status"] in DELIVERED_STATUSES
        if counted:
            delivered += value
        elif svc["status"] in ROADMAP_STATUSES:
            roadmap += value
        if svc["status"] == "billable":
            suggested_charge += svc.get("resale_price") or 0
        lines.append(
            {
                "service_name": svc["service_name"],
                "status": svc["status"],
                "resale_price": svc.get("resale_price"),
                "value": value,
                "counted": counted,
            }
        )

    return {
        "client_id": client_id,
        "client_name": client["name"],
        "lines": lines,
        "delivered_value": round(delivered, 2),
        "roadmap_value": round(roadmap, 2),
        "suggested_charge": round(suggested_charge, 2),
    }


def generate_run(client_id, period=None, charged_amount=None, notes=None):
    """Create (or replace) the saved run for a client + month.

    Re-running a period overwrites the prior run for that client so corrections
    are easy. Returns the stored run id. Raises ValueError on bad input.
    """
    period = period or current_period()
    if not _PERIOD_RE.match(period):
        raise ValueError("Period must be in YYYY-MM format.")

    preview = preview_run(client_id)
    if preview is None:
        raise ValueError("Client not found.")

    if charged_amount in (None, ""):
        charged_amount = preview["suggested_charge"]
    try:
        charged_amount = float(charged_amount)
    except (TypeError, ValueError):
        raise ValueError("Charged amount must be a number.")

    conn = get_connection()
    try:
        # UNIQUE(client_id, period): drop any existing run for this month first.
        conn.execute(
            "DELETE FROM billing_runs WHERE client_id = ? AND period = ?",
            (client_id, period),
        )
        cur = conn.execute(
            """INSERT INTO billing_runs
                 (client_id, period, charged_amount, delivered_value,
                  roadmap_value, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                client_id,
                period,
                charged_amount,
                preview["delivered_value"],
                preview["roadmap_value"],
                (notes or "").strip() or None,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        run_id = cur.lastrowid
        for ln in preview["lines"]:
            conn.execute(
                """INSERT INTO billing_run_lines
                     (run_id, service_name, status, resale_price, value, counted)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    ln["service_name"],
                    ln["status"],
                    ln["resale_price"],
                    ln["value"],
                    1 if ln["counted"] else 0,
                ),
            )
        conn.commit()
        return run_id
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read / list / delete runs
# ---------------------------------------------------------------------------
def _shape_run(row):
    run = dict(row)
    run["value_gap"] = round(run["delivered_value"] - run["charged_amount"], 2)
    return run


def list_runs(client_id=None):
    """Saved runs (newest first), with client name and computed value gap."""
    sql = (
        "SELECT r.*, c.name AS client_name FROM billing_runs r "
        "JOIN clients c ON c.id = r.client_id"
    )
    params = []
    if client_id:
        sql += " WHERE r.client_id = ?"
        params.append(client_id)
    sql += " ORDER BY r.period DESC, c.name ASC"

    conn = get_connection()
    try:
        return [_shape_run(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def get_run(run_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT r.*, c.name AS client_name FROM billing_runs r "
            "JOIN clients c ON c.id = r.client_id WHERE r.id = ?",
            (run_id,),
        ).fetchone()
        if not row:
            return None
        run = _shape_run(row)
        run["lines"] = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM billing_run_lines WHERE run_id = ? ORDER BY id",
                (run_id,),
            ).fetchall()
        ]
        return run
    finally:
        conn.close()


def delete_run(run_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM billing_runs WHERE id = ?", (run_id,))
        conn.commit()
    finally:
        conn.close()


def portfolio_summary():
    """Totals across the most recent run of each client — the headline numbers
    for the billing dashboard."""
    runs = list_runs()
    seen = set()
    delivered = charged = roadmap = 0.0
    for run in runs:  # already newest-first, so first per client = latest
        if run["client_id"] in seen:
            continue
        seen.add(run["client_id"])
        delivered += run["delivered_value"]
        charged += run["charged_amount"]
        roadmap += run["roadmap_value"]
    return {
        "clients_with_runs": len(seen),
        "delivered_value": round(delivered, 2),
        "charged_amount": round(charged, 2),
        "value_gap": round(delivered - charged, 2),
        "roadmap_value": round(roadmap, 2),
    }
