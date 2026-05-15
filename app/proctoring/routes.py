from flask import request, jsonify
from . import proctoring_bp
from app import db
from app.models import ActivityLog


@proctoring_bp.route("/log-event", methods=["POST"])
def log_event():
    """
    Receives suspicious activity events from JavaScript via AJAX.
    Expected JSON: { "attempt_id": 1, "event_type": "tab_switch" }
    """
    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400

    attempt_id = data.get("attempt_id")
    event_type = data.get("event_type")

    # Only accept these three event types — nothing else
    allowed = {"tab_switch", "idle", "fast_submit"}
    if not attempt_id or event_type not in allowed:
        return jsonify({"status": "error", "message": "Invalid"}), 400

    log = ActivityLog(attempt_id=attempt_id, event_type=event_type)
    db.session.add(log)
    db.session.commit()

    return jsonify({"status": "ok", "event": event_type}), 200