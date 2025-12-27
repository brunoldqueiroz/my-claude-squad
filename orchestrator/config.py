"""Centralized configuration for my-claude-squad orchestrator.

Loads configuration from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LangfuseConfig:
    """Langfuse observability configuration."""

    public_key: str | None
    secret_key: str | None
    host: str
    debug: bool
    enabled: bool

    @classmethod
    def from_env(cls) -> "LangfuseConfig":
        """Load Langfuse config from environment variables."""
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")

        return cls(
            public_key=public_key,
            secret_key=secret_key,
            host=os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com"),
            debug=os.getenv("LANGFUSE_DEBUG", "").lower() == "true",
            enabled=bool(public_key and secret_key),
        )

    def mask_secret(self) -> str:
        """Return masked secret key for safe logging."""
        if not self.secret_key:
            return "not set"
        if len(self.secret_key) <= 8:
            return "***"
        return f"{self.secret_key[:4]}...{self.secret_key[-4:]}"


@dataclass
class MemoryConfig:
    """DuckDB memory storage configuration."""

    db_path: Path
    auto_init: bool

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "MemoryConfig":
        """Load memory config from environment variables."""
        if project_root is None:
            project_root = Path(__file__).parent.parent

        db_path_str = os.getenv("SWARM_DB_PATH")
        if db_path_str:
            db_path = Path(db_path_str)
        else:
            db_path = project_root / ".swarm" / "memory.duckdb"

        return cls(
            db_path=db_path,
            auto_init=os.getenv("SWARM_AUTO_INIT", "true").lower() == "true",
        )


@dataclass
class Config:
    """Main configuration container."""

    langfuse: LangfuseConfig
    memory: MemoryConfig
    log_level: str
    environment: str

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "Config":
        """Load all configuration from environment variables."""
        return cls(
            langfuse=LangfuseConfig.from_env(),
            memory=MemoryConfig.from_env(project_root),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            environment=os.getenv("ENVIRONMENT", "development"),
        )


# Singleton config instance
_config: Config | None = None


def get_config(project_root: Path | None = None) -> Config:
    """Get the configuration singleton.

    Args:
        project_root: Optional project root path. Only used on first call.

    Returns:
        The Config instance.
    """
    global _config
    if _config is None:
        _config = Config.from_env(project_root)
    return _config


def reload_config(project_root: Path | None = None) -> Config:
    """Reload configuration from environment.

    Args:
        project_root: Optional project root path.

    Returns:
        The new Config instance.
    """
    global _config
    _config = Config.from_env(project_root)
    return _config
