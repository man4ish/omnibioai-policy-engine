def evaluate_rules(action: str, resource: str) -> tuple[bool, str]:
    # Example dataset protection rules
    if resource.startswith("human_genome") and action == "dataset.delete":
        return False, "protected dataset cannot be deleted"

    # Model registry protection
    if resource == "model_registry" and action == "delete":
        return False, "model registry is immutable"

    return True, "rules passed"