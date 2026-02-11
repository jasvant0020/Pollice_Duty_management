ROLE_HIERARCHY = {
    "developer": 5,
    "master_admin": 4,
    "super_admin": 3,
    "admin": 2,
    "gd_munsi": 1,
    "field_staff": 0,
    "vvip": 0,
}

def has_suspended_parent(user):
    """
    Returns True if ANY parent in hierarchy is suspended
    """

    visited = set()
    current = user

    while current:
        if current.id in visited:
            break
        visited.add(current.id)

        # Operational hierarchy
        if current.role == "field_staff" and current.gd_munsi:
            if not current.gd_munsi.is_active:
                return True
            current = current.gd_munsi
            continue

        if current.role in ["gd_munsi", "vvip"] and current.admin:
            if not current.admin.is_active:
                return True
            current = current.admin
            continue
        
        # Management hierarchy (created_by)
        if current.created_by:
            if not current.created_by.is_active:
                return True
            current = current.created_by
            continue

        break

    return False
