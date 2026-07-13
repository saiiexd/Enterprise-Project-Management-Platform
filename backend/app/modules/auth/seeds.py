import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import Role, Permission

logger = logging.getLogger("epmp.seeds")

# Define all permissions
ALL_PERMISSIONS = {
    # Organization Permissions
    "org:view": "View organization details",
    "org:update": "Update organization settings and details",
    "org:delete": "Delete/Archive organization",
    
    # Member Permissions
    "member:view": "View organization members",
    "member:invite": "Invite new members",
    "member:remove": "Remove members from organization",
    "member:update_role": "Change member roles",
    
    # Team Permissions
    "team:view": "View teams",
    "team:create": "Create new teams",
    "team:update": "Update team details",
    "team:delete": "Delete/Archive teams",
    "team:join": "Join a team",
    "team:leave": "Leave a team",
}

# Define Roles and their associated Permission keys
ROLE_PERMISSIONS = {
    "Organization Owner": list(ALL_PERMISSIONS.keys()),
    "Organization Administrator": [
        "org:view", "org:update",
        "member:view", "member:invite", "member:remove", "member:update_role",
        "team:view", "team:create", "team:update", "team:delete", "team:join", "team:leave"
    ],
    "Project Manager": [
        "org:view", "member:view",
        "team:view", "team:join", "team:leave"
    ],
    "Team Lead": [
        "org:view", "member:view",
        "team:view", "team:update", "team:join", "team:leave"
    ],
    "Developer": [
        "org:view", "member:view", "team:view", "team:join", "team:leave"
    ],
    "QA Engineer": [
        "org:view", "member:view", "team:view", "team:join", "team:leave"
    ],
    "Viewer": [
        "org:view", "member:view", "team:view"
    ],
    "Guest": [
        "org:view"
    ]
}

async def seed_roles_and_permissions(db: AsyncSession) -> None:
    logger.info("Seeding roles and permissions...")
    
    # 1. Seed Permissions
    permissions_db = {}
    for name, desc in ALL_PERMISSIONS.items():
        stmt = select(Permission).where(Permission.name == name)
        result = await db.execute(stmt)
        perm = result.scalar_one_or_none()
        if not perm:
            perm = Permission(name=name, description=desc)
            db.add(perm)
            logger.info(f"Created permission: {name}")
        permissions_db[name] = perm
        
    await db.flush()
    
    # 2. Seed Roles
    for role_name, perm_names in ROLE_PERMISSIONS.items():
        stmt = select(Role).where(Role.name == role_name)
        result = await db.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name=role_name, description=f"Default {role_name} role")
            db.add(role)
            logger.info(f"Created role: {role_name}")
            
        # Associate permissions
        role.permissions = [permissions_db[p_name] for p_name in perm_names]
        
    await db.commit()
    logger.info("Roles and permissions seeding completed.")
