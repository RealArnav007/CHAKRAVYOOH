"""
RBAC Permission Registry — B19
Defines granular action permissions per role.
"""

# Role -> List of permitted actions
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "SUPER_ADMIN": ["*"],  # Wildcard — all permissions
    "COMMANDER": [
        "incident.read",
        "incident.update",
        "incident.dispatch",
        "incident.resolve",
        "resource.read",
        "resource.update",
        "zone.read",
        "audit.read",
        "user.read",
    ],
    "RESPONDER": [
        "incident.read",
        "incident.dispatch",
        "resource.read",
    ],
    "ANALYST": [
        "incident.read",
        "zone.read",
        "audit.read",
        "resource.read",
    ],
    "VIEWER": [
        "incident.read",
        "zone.read",
    ],
}


def has_permission(role: str, action: str) -> bool:
    """Check if a role is permitted to perform the given action."""
    perms = ROLE_PERMISSIONS.get(role, [])
    return "*" in perms or action in perms
