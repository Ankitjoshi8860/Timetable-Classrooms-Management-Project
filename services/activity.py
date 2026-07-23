"""Activity logging through the shared database wrapper."""

from services import db


def log_event(
    *,
    entity_type,
    action,
    actor_user_id=None,
    entity_id=None,
    old_value=None,
    new_value=None,
):
    """Record an auditable change for dashboard activity summaries."""
    return db.insert(
        "dbo.activity_log",
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
            "actor_user_id": actor_user_id,
            "created_by": actor_user_id,
            "updated_by": actor_user_id,
        },
    )
