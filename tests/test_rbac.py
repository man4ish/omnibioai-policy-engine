import pytest
from app.core.rbac import evaluate_rbac


# ---------------------------------------------------------------------------
# Admin override
# ---------------------------------------------------------------------------

def test_admin_gets_universal_allow():
    allowed, reason = evaluate_rbac(["admin"], "tes.submit")
    assert allowed is True
    assert reason == "admin override"


def test_admin_with_other_roles_still_overrides():
    allowed, reason = evaluate_rbac(["admin", "viewer"], "dataset.delete")
    assert allowed is True
    assert reason == "admin override"


# ---------------------------------------------------------------------------
# tes.* action — requires "researcher"
# ---------------------------------------------------------------------------

def test_researcher_can_submit_tes_job():
    allowed, reason = evaluate_rbac(["researcher"], "tes.submit")
    assert allowed is True
    assert reason == "rbac passed"


def test_missing_researcher_denied_tes_action():
    allowed, reason = evaluate_rbac(["viewer"], "tes.submit")
    assert allowed is False
    assert "researcher" in reason


def test_data_scientist_cannot_access_tes():
    allowed, reason = evaluate_rbac(["data_scientist"], "tes.run")
    assert allowed is False
    assert "researcher" in reason


# ---------------------------------------------------------------------------
# dataset.* action — requires "data_scientist"
# ---------------------------------------------------------------------------

def test_data_scientist_can_access_dataset():
    allowed, reason = evaluate_rbac(["data_scientist"], "dataset.read")
    assert allowed is True
    assert reason == "rbac passed"


def test_missing_data_scientist_denied_dataset_action():
    allowed, reason = evaluate_rbac(["researcher"], "dataset.write")
    assert allowed is False
    assert "data_scientist" in reason


def test_viewer_denied_dataset_action():
    allowed, reason = evaluate_rbac([], "dataset.delete")
    assert allowed is False


# ---------------------------------------------------------------------------
# Unrelated actions — default allow
# ---------------------------------------------------------------------------

def test_unrelated_action_allowed_for_any_role():
    allowed, reason = evaluate_rbac(["viewer"], "profile.read")
    assert allowed is True
    assert reason == "rbac passed"


def test_empty_roles_allowed_for_unrelated_action():
    allowed, reason = evaluate_rbac([], "ping")
    assert allowed is True
