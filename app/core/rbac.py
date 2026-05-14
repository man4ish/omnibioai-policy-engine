def evaluate_rbac(user_roles: list[str], action: str) -> tuple[bool, str]:
    if "admin" in user_roles:
        return True, "admin override"

    if action.startswith("tes.") and "researcher" not in user_roles:
        return False, "missing role: researcher"

    if action.startswith("dataset.") and "data_scientist" not in user_roles:
        return False, "missing role: data_scientist"

    return True, "rbac passed"