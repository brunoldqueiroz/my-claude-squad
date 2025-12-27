"""Tests for orchestrator/config.py - Configuration loading."""

import pytest

from orchestrator.config import (
    Config,
    LangfuseConfig,
    MemoryConfig,
    get_config,
    reload_config,
)


class TestLangfuseConfig:
    """Tests for LangfuseConfig."""

    def test_from_env_with_all_keys(self, monkeypatch):
        """Config loads correctly when all keys are set."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test-123")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test-456")
        monkeypatch.setenv("LANGFUSE_HOST", "https://custom.langfuse.com")
        monkeypatch.setenv("LANGFUSE_DEBUG", "true")

        config = LangfuseConfig.from_env()

        assert config.public_key == "pk-test-123"
        assert config.secret_key == "sk-test-456"
        assert config.host == "https://custom.langfuse.com"
        assert config.debug is True

    def test_from_env_with_defaults(self, monkeypatch):
        """Config uses defaults when optional keys are missing."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
        monkeypatch.delenv("LANGFUSE_HOST", raising=False)
        monkeypatch.delenv("LANGFUSE_DEBUG", raising=False)

        config = LangfuseConfig.from_env()

        assert config.host == "https://us.cloud.langfuse.com"
        assert config.debug is False

    def test_from_env_without_keys(self, monkeypatch):
        """Config has None for optional keys when not set."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        config = LangfuseConfig.from_env()

        assert config.public_key is None
        assert config.secret_key is None

    def test_enabled_with_both_keys(self, monkeypatch):
        """enabled returns True when both keys are set."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        config = LangfuseConfig.from_env()

        assert config.enabled is True

    def test_enabled_missing_public_key(self, monkeypatch):
        """enabled returns False when public key is missing."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        config = LangfuseConfig.from_env()

        assert config.enabled is False

    def test_enabled_missing_secret_key(self, monkeypatch):
        """enabled returns False when secret key is missing."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        config = LangfuseConfig.from_env()

        assert config.enabled is False


class TestMemoryConfig:
    """Tests for MemoryConfig."""

    def test_from_env_with_custom_path(self, monkeypatch):
        """Config uses custom path when SWARM_DB_PATH is set."""
        monkeypatch.setenv("SWARM_DB_PATH", "/custom/path/memory.duckdb")

        config = MemoryConfig.from_env()

        assert str(config.db_path) == "/custom/path/memory.duckdb"

    def test_from_env_with_default_path(self, monkeypatch):
        """Config uses default path when SWARM_DB_PATH is not set."""
        monkeypatch.delenv("SWARM_DB_PATH", raising=False)

        config = MemoryConfig.from_env()

        # Default path is set to project_root/.swarm/memory.duckdb
        assert config.db_path is not None
        assert str(config.db_path).endswith(".swarm/memory.duckdb")

    def test_auto_init_default(self, monkeypatch):
        """auto_init defaults to True."""
        monkeypatch.delenv("SWARM_DB_PATH", raising=False)

        config = MemoryConfig.from_env()

        assert config.auto_init is True


class TestConfig:
    """Tests for Config container."""

    def test_from_env_creates_all_configs(self, monkeypatch):
        """Config.from_env creates langfuse and memory configs."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        config = Config.from_env()

        assert isinstance(config.langfuse, LangfuseConfig)
        assert isinstance(config.memory, MemoryConfig)


class TestConfigSingleton:
    """Tests for config singleton behavior."""

    def test_get_config_returns_same_instance(self, monkeypatch):
        """get_config returns the same instance on multiple calls."""
        # Reset singleton first
        import orchestrator.config

        orchestrator.config._config = None

        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_reload_config_creates_new_instance(self, monkeypatch):
        """reload_config creates a new config instance."""
        import orchestrator.config

        orchestrator.config._config = None

        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-first")
        config1 = get_config()

        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-second")
        config2 = reload_config()

        assert config1 is not config2
        assert config2.langfuse.public_key == "pk-second"
