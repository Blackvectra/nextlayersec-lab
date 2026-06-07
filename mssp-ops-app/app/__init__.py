"""MSSP Ops App — Flask application factory.

Serves a minimal single-page UI plus a small JSON API on localhost. The app is
structured as a package so future modules (billing engine, deliverable
generator, quote/contract generator) can be added as new blueprints/route
groups without disturbing Module #1.
"""

import json
import os

from flask import Flask, jsonify, render_template, request, send_file

from . import registry
from .db import BASE_DIR, init_db

EXPORTS_DIR = os.path.join(BASE_DIR, "exports")  # gitignored


def create_app():
    app = Flask(__name__)

    # Build the database from schema.sql + seed.sql on first run.
    init_db()

    # -----------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")

    # -----------------------------------------------------------------------
    # Dashboard / registry read
    # -----------------------------------------------------------------------
    @app.route("/api/dashboard")
    def api_dashboard():
        status = request.args.get("status") or None
        sort = request.args.get("sort", "name")
        return jsonify(registry.build_dashboard(status=status, sort=sort))

    # -----------------------------------------------------------------------
    # Name-match guard (typo-duplicate check) — called before save
    # -----------------------------------------------------------------------
    @app.route("/api/clients/check-name")
    def api_check_name():
        name = request.args.get("name", "")
        exclude_id = request.args.get("exclude_id", type=int)
        matches = registry.find_similar_names(name, exclude_id=exclude_id)
        return jsonify({"similar": matches})

    # -----------------------------------------------------------------------
    # Clients CRUD
    # -----------------------------------------------------------------------
    @app.route("/api/clients", methods=["POST"])
    def api_create_client():
        data = request.get_json(force=True)
        err = _validate_client(data)
        if err:
            return jsonify({"error": err}), 400
        client_id = registry.create_client(data)
        return jsonify({"id": client_id}), 201

    @app.route("/api/clients/<int:client_id>", methods=["PUT"])
    def api_update_client(client_id):
        data = request.get_json(force=True)
        err = _validate_client(data)
        if err:
            return jsonify({"error": err}), 400
        registry.update_client(client_id, data)
        return jsonify({"ok": True})

    @app.route("/api/clients/<int:client_id>", methods=["DELETE"])
    def api_delete_client(client_id):
        registry.delete_client(client_id)
        return jsonify({"ok": True})

    # -----------------------------------------------------------------------
    # Services CRUD (nested under a client)
    # -----------------------------------------------------------------------
    @app.route("/api/clients/<int:client_id>/services", methods=["POST"])
    def api_create_service(client_id):
        data = request.get_json(force=True)
        err = _validate_service(data)
        if err:
            return jsonify({"error": err}), 400
        service_id = registry.create_service(client_id, data)
        return jsonify({"id": service_id}), 201

    @app.route("/api/services/<int:service_id>", methods=["PUT"])
    def api_update_service(service_id):
        data = request.get_json(force=True)
        err = _validate_service(data)
        if err:
            return jsonify({"error": err}), 400
        registry.update_service(service_id, data)
        return jsonify({"ok": True})

    @app.route("/api/services/<int:service_id>", methods=["DELETE"])
    def api_delete_service(service_id):
        registry.delete_service(service_id)
        return jsonify({"ok": True})

    # -----------------------------------------------------------------------
    # JSON export / import — written to gitignored exports/ dir
    # -----------------------------------------------------------------------
    @app.route("/api/export")
    def api_export():
        payload = registry.export_registry()
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        stamp = payload["exported_at"].replace(":", "").replace(" ", "_")
        path = os.path.join(EXPORTS_DIR, f"registry_{stamp}.export.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        # Stream the file to the browser as a download for off-machine backup.
        return send_file(
            path, as_attachment=True, download_name=os.path.basename(path)
        )

    @app.route("/api/import", methods=["POST"])
    def api_import():
        payload = request.get_json(force=True)
        if not isinstance(payload, dict) or "clients" not in payload:
            return jsonify({"error": "Invalid export file."}), 400
        counts = registry.import_registry(payload, replace=True)
        return jsonify({"ok": True, "imported": counts})

    return app


# ---------------------------------------------------------------------------
# Lightweight server-side validation (mirrors the schema CHECK constraints)
# ---------------------------------------------------------------------------
def _validate_client(data):
    if not data or not (data.get("name") or "").strip():
        return "Client name is required."
    if data.get("status", "prospect") not in registry.CLIENT_STATUSES:
        return "Invalid client status."
    return None


def _validate_service(data):
    if not data or not (data.get("service_name") or "").strip():
        return "Service name is required."
    if data.get("status", "queued") not in registry.SERVICE_STATUSES:
        return "Invalid service status."
    return None
