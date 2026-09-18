import logging
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        actor: str,
        action: str,
        target: str = None,
        ip_address: str = None,
        details: str = None
    ):
        """
        Records an audit log entry in the database.
        """
        try:
            entry = AuditLog(
                actor=actor or "system",
                action=action,
                target=target,
                ip_address=ip_address or "unknown",
                details=details
            )
            db.add(entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to record audit log: {str(e)}")
            db.rollback()

audit_service = AuditService()
