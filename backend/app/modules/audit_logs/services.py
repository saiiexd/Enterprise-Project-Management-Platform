import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.audit_logs.models import AuditLog

logger = logging.getLogger("epmp.audit_service")

class AuditLogService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        user_id: uuid.UUID | None,
        organization_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
        db.add(log)
        await db.commit()
        logger.info(
            f"AUDIT LOG: user_id={user_id} org_id={organization_id} action={action} "
            f"resource={resource_type}:{resource_id}"
        )
        return log
