ROLE_PRIORITY = ["rrhh", "ti", "jefatura", "prevencion", "finanzas", "logistica"]


def get_primary_role(user_roles):
    user_set = set(user_roles)
    if "administrador" in user_set:
        for role in ROLE_PRIORITY:
            if role in user_set:
                return role
        return "administrador"
    for role in ROLE_PRIORITY:
        if role in user_set:
            return role
    return None
