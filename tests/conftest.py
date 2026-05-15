import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_redis():
    return MagicMock()


@pytest.fixture
def policy_cache(mock_redis):
    with patch("app.services.cache.redis") as mock_redis_module:
        mock_redis_module.from_url.return_value = mock_redis
        from app.services.cache import PolicyCache
        cache = PolicyCache(redis_url="redis://localhost")
        cache.redis = mock_redis
        yield cache, mock_redis


@pytest.fixture
def policy_engine(policy_cache):
    cache, mock_redis = policy_cache
    from app.core.engine import PolicyEngine
    engine = PolicyEngine(cache=cache)
    return engine, cache, mock_redis
