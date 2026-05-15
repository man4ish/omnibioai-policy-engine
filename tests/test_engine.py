import json
import pytest
from unittest.mock import MagicMock
from app.core.engine import PolicyEngine
from app.models.request import PolicyRequest
from app.models.decision import PolicyDecision


def make_engine(mock_redis=None):
    if mock_redis is None:
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

    from app.services.cache import PolicyCache
    from unittest.mock import patch
    with patch("app.services.cache.redis") as mock_redis_module:
        mock_redis_module.from_url.return_value = mock_redis
        cache = PolicyCache(redis_url="redis://localhost")
        cache.redis = mock_redis
    return PolicyEngine(cache=cache), mock_redis


def basic_request(**kwargs):
    defaults = {
        "user_id": "u1",
        "email": "u1@test.com",
        "roles": ["researcher"],
        "permissions": [],
        "action": "tes.submit",
        "resource": "job_queue",
        "context": {},
    }
    defaults.update(kwargs)
    return PolicyRequest(**defaults)


# ---------------------------------------------------------------------------
# _evaluate_core — RBAC denial
# ---------------------------------------------------------------------------

def test_rbac_deny_stops_evaluation():
    engine, _ = make_engine()
    req = basic_request(roles=[], action="tes.submit")  # no researcher role

    decision = engine._evaluate_core(req)

    assert decision.allowed is False
    assert decision.policy_source == "RBAC"
    assert "researcher" in decision.reason


# ---------------------------------------------------------------------------
# _evaluate_core — ABAC denial
# ---------------------------------------------------------------------------

def test_abac_deny_gpu_access():
    engine, _ = make_engine()
    req = basic_request(
        roles=["researcher"],
        context={"gpu_required": True},  # no gpu_user role
    )

    decision = engine._evaluate_core(req)

    assert decision.allowed is False
    assert decision.policy_source == "ABAC"
    assert "GPU" in decision.reason


def test_abac_deny_hpc_access():
    engine, _ = make_engine()
    req = basic_request(
        roles=["researcher"],
        context={"node": "hpc"},  # no hpc_user role
    )

    decision = engine._evaluate_core(req)

    assert decision.allowed is False
    assert decision.policy_source == "ABAC"
    assert "HPC" in decision.reason


# ---------------------------------------------------------------------------
# _evaluate_core — Rules denial
# ---------------------------------------------------------------------------

def test_rules_deny_protected_dataset_delete():
    engine, _ = make_engine()
    req = basic_request(
        roles=["data_scientist"],
        action="dataset.delete",
        resource="human_genome_v1",
    )

    decision = engine._evaluate_core(req)

    assert decision.allowed is False
    assert decision.policy_source == "RULES"


def test_rules_deny_model_registry_delete():
    engine, _ = make_engine()
    req = basic_request(
        roles=["admin"],
        action="delete",
        resource="model_registry",
    )
    # admin overrides RBAC, ABAC passes, but RULES should deny
    decision = engine._evaluate_core(req)

    assert decision.allowed is False
    assert decision.policy_source == "RULES"


# ---------------------------------------------------------------------------
# _evaluate_core — full allow
# ---------------------------------------------------------------------------

def test_all_checks_pass_returns_allowed():
    engine, _ = make_engine()
    req = basic_request()

    decision = engine._evaluate_core(req)

    assert decision.allowed is True
    assert decision.policy_source == "ALL_PASSED"
    assert decision.reason == "access granted"


# ---------------------------------------------------------------------------
# evaluate — cache-first path
# ---------------------------------------------------------------------------

def test_evaluate_returns_cached_decision():
    mock_redis = MagicMock()
    mock_redis.get.return_value = json.dumps({"allowed": True, "reason": "cached", "context": {}})
    engine, _ = make_engine(mock_redis)

    req = basic_request()
    decision = engine.evaluate(req)

    assert decision.allowed is True
    assert decision.policy_source == "CACHE"
    mock_redis.setex.assert_not_called()


def test_evaluate_cache_miss_computes_and_stores():
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    engine, _ = make_engine(mock_redis)

    req = basic_request()
    decision = engine.evaluate(req)

    assert decision.allowed is True
    mock_redis.setex.assert_called_once()


def test_evaluate_cache_miss_rbac_deny_stores_denial():
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    engine, _ = make_engine(mock_redis)

    req = basic_request(roles=[], action="tes.submit")
    decision = engine.evaluate(req)

    assert decision.allowed is False
    mock_redis.setex.assert_called_once()


# ---------------------------------------------------------------------------
# abac / rules helpers imported via engine
# ---------------------------------------------------------------------------

def test_abac_gpu_with_gpu_user_role_passes():
    engine, _ = make_engine()
    req = basic_request(
        roles=["researcher", "gpu_user"],
        context={"gpu_required": True},
    )
    decision = engine._evaluate_core(req)
    assert decision.allowed is True


def test_abac_hpc_with_hpc_user_role_passes():
    engine, _ = make_engine()
    req = basic_request(
        roles=["researcher", "hpc_user"],
        context={"node": "hpc"},
    )
    decision = engine._evaluate_core(req)
    assert decision.allowed is True
