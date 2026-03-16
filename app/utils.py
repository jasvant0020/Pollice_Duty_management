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
    Returns True if any user above in hierarchy is suspended
    """

    # GD Munsi → Admin
    if user.role == "gd_munsi" and user.admin:
        return not user.admin.is_active

    # Field Staff → GD → Admin
    if user.role == "field_staff" and user.gd_munsi:
        if not user.gd_munsi.is_active:
            return True
        if user.gd_munsi.admin and not user.gd_munsi.admin.is_active:
            return True

    # VVIP → Admin
    if user.role == "vvip" and user.admin:
        return not user.admin.is_active

    return False
