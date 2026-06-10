"""Stage 0 smoke tests: confirm the project imports and config is sane.

More tests (health endpoint, retrieval sanity) are added in later stages.
"""
import config


def test_config_imports():
    assert config.SEED == 42
    assert config.TOP_K >= 1
    assert config.CHUNK_SIZE_TOKENS > config.CHUNK_OVERLAP_TOKENS


def test_set_seeds_runs():
    # Should not raise even without numpy installed.
    config.set_seeds()
    config.set_seeds(123)
