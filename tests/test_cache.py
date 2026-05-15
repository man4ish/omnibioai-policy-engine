import json
import hashlib
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def cache_with_mock():
    mock_redis = MagicMock()
    with patch("app.services.cache.redis") as mock_redis_module:
        mock_redis_module.from_url.return_value = mock_redis
        from app.services.cache import PolicyCache
        cache = PolicyCache(redis_url="redis://localhost")
        cache.redis = mock_redis
        yield cache, mock_redis


# ---------------------------------------------------------------------------
# build_key
# ---------------------------------------------------------------------------

def test_build_key_is_deterministic(cache_with_mock):
    cache, _ = cache_with_mock
    key1 = cache.build_key("u1", "read", "resource", {"env": "prod"})
    key2 = cache.build_key("u1", "read", "resource", {"env": "prod"})
    assert key1 == key2


def test_build_key_starts_with_policy_prefix(cache_with_mock):
    cache, _ = cache_with_mock
    key = cache.build_key("u1", "read", "res", {})
    assert key.startswith("policy:")


def test_build_key_different_users_different_keys(cache_with_mock):
    cache, _ = cache_with_mock
    key1 = cache.build_key("u1", "read", "res", {})
    key2 = cache.build_key("u2", "read", "res", {})
    assert key1 != key2


def test_build_key_context_order_insensitive(cache_with_mock):
    cache, _ = cache_with_mock
    key1 = cache.build_key("u1", "read", "res", {"a": 1, "b": 2})
    key2 = cache.build_key("u1", "read", "res", {"b": 2, "a": 1})
    assert key1 == key2


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

def test_get_returns_parsed_dict_on_hit(cache_with_mock):
    cache, mock_redis = cache_with_mock
    data = {"allowed": True, "reason": "ok", "policy_source": "RBAC"}
    mock_redis.get.return_value = json.dumps(data)

    result = cache.get("policy:abc123")

    assert result == data
    mock_redis.get.assert_called_once_with("policy:abc123")


def test_get_returns_none_on_miss(cache_with_mock):
    cache, mock_redis = cache_with_mock
    mock_redis.get.return_value = None

    result = cache.get("policy:missing")

    assert result is None


# ---------------------------------------------------------------------------
# set
# ---------------------------------------------------------------------------

def test_set_stores_json_with_ttl(cache_with_mock):
    cache, mock_redis = cache_with_mock
    data = {"allowed": False, "reason": "denied"}

    cache.set("policy:key1", data, ttl=300)

    mock_redis.setex.assert_called_once_with("policy:key1", 300, json.dumps(data))


def test_set_default_ttl(cache_with_mock):
    cache, mock_redis = cache_with_mock
    cache.set("policy:key2", {"allowed": True, "reason": "ok"})

    args = mock_redis.setex.call_args[0]
    assert args[1] == 300  # default TTL


# ---------------------------------------------------------------------------
# invalidate_user
# ---------------------------------------------------------------------------

def test_invalidate_user_deletes_only_matching_keys(cache_with_mock):
    cache, mock_redis = cache_with_mock
    # Keys that literally contain "u1" trigger deletion; others are skipped
    mock_redis.scan_iter.return_value = iter(["policy:u1_hash", "policy:other_user"])

    cache.invalidate_user("u1")

    mock_redis.scan_iter.assert_called_once_with("policy:*")
    mock_redis.delete.assert_called_once_with("policy:u1_hash")


def test_invalidate_user_no_matching_keys(cache_with_mock):
    cache, mock_redis = cache_with_mock
    mock_redis.scan_iter.return_value = iter(["policy:other_user"])

    cache.invalidate_user("u1")

    mock_redis.delete.assert_not_called()


def test_invalidate_user_no_keys(cache_with_mock):
    cache, mock_redis = cache_with_mock
    mock_redis.scan_iter.return_value = iter([])

    cache.invalidate_user("u1")

    mock_redis.delete.assert_not_called()
