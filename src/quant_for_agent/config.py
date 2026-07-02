from __future__ import annotations

import os
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit


_FALSE_VALUES = {"0", "false", "no", "off"}
_TRUE_VALUES = {"1", "true", "yes", "on"}
_SECRET_KEYS = {"api_key", "secret_key", "password", "smtp_password", "smtp_url", "token"}


def _default_home(environ: Mapping[str, str] = os.environ) -> Path:
    return Path(environ.get("QFA_HOME", Path.home() / ".qfa")).expanduser()


DEFAULT_HOME = _default_home()
DEFAULT_DB_PATH = Path(os.environ.get("QFA_DB", DEFAULT_HOME / "qfa.sqlite3")).expanduser()
DEFAULT_HEALTH_LOG_PATH = Path(
    os.environ.get("QFA_HEALTH_LOG", DEFAULT_HOME / "daemon-health.jsonl")
).expanduser()
DEFAULT_CONFIG_PATH = DEFAULT_HOME / "config.toml"


@dataclass(frozen=True)
class CoreConfig:
    home: Path
    db: Path
    health_log: Path


@dataclass(frozen=True)
class AlpacaConfig:
    api_key: str | None = None
    secret_key: str | None = None
    paper: bool = True
    data_feed: str | None = None

    @classmethod
    def from_env(cls) -> "AlpacaConfig":
        config = load_qfa_config()
        if not config.alpaca.api_key or not config.alpaca.secret_key:
            raise RuntimeError("ALPACA_API_KEY and ALPACA_SECRET_KEY are required")
        return config.alpaca


@dataclass(frozen=True)
class FactorStoreConfig:
    backend: str = "sqlite"
    table: str = "qfa-factor-observations"
    region: str | None = None


@dataclass(frozen=True)
class EmailConfig:
    to: tuple[str, ...] = ()
    smtp_url: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    sender: str | None = None
    tls: bool = True


@dataclass(frozen=True)
class FactorRepositoryConfig:
    repository_paths: tuple[Path, ...] = ()
    max_staleness_seconds: int | None = None


@dataclass(frozen=True)
class QFAConfig:
    core: CoreConfig
    alpaca: AlpacaConfig
    factor_store: FactorStoreConfig
    email: EmailConfig
    factor_repository: FactorRepositoryConfig
    config_path: Path | None = None


def default_config_path(environ: Mapping[str, str] = os.environ) -> Path:
    return Path(environ.get("QFA_CONFIG", _default_home(environ) / "config.toml")).expanduser()


def _get_nested(data: Mapping[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _pick_config(data: Mapping[str, Any], *paths: str) -> Any:
    for path in paths:
        value = _get_nested(data, path)
        if value is not None:
            return value
    return None


def _env(environ: Mapping[str, str], *names: str) -> str | None:
    for name in names:
        value = environ.get(name)
        if value not in (None, ""):
            return value
    return None


def _override(overrides: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        value = overrides.get(name)
        if value is not None:
            return value
    return None


def _bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _path(value: Any, *, base: Path | None = None) -> Path:
    path = Path(str(value)).expanduser()
    if not path.is_absolute() and base is not None:
        path = base / path
    return path


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if isinstance(value, list | tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    raise ValueError("Expected string or list")


def load_config_file(path: Path | None = None, *, explicit: bool = False) -> dict[str, Any]:
    selected = (path or default_config_path()).expanduser()
    if not selected.exists():
        if explicit:
            raise FileNotFoundError(f"qfa config file not found: {selected}")
        return {}
    with selected.open("rb") as handle:
        loaded = tomllib.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("qfa config file must contain a TOML object")
    return loaded


def load_qfa_config(
    *,
    config_path: Path | None = None,
    cli_overrides: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] = os.environ,
) -> QFAConfig:
    overrides = cli_overrides or {}
    env_config_path = environ.get("QFA_CONFIG")
    explicit_config_path = config_path is not None or bool(env_config_path)
    if explicit_config_path:
        raw_config_path = config_path if config_path is not None else env_config_path
        if raw_config_path is None:
            raise FileNotFoundError("qfa config file path was empty")
        selected_config_path = Path(raw_config_path).expanduser()
    else:
        selected_config_path = default_config_path(environ)
    config_file = load_config_file(selected_config_path, explicit=explicit_config_path)
    config_dir = selected_config_path.parent

    configured_home = _pick_config(config_file, "core.home", "qfa.home")
    home_value = _override(overrides, "core.home", "home") or _env(environ, "QFA_HOME") or configured_home
    home = _path(home_value) if home_value is not None else _default_home(environ)

    configured_db = _pick_config(config_file, "core.db", "qfa.db")
    db_value = _override(overrides, "core.db", "db") or _env(environ, "QFA_DB") or configured_db
    db = _path(db_value, base=config_dir) if db_value is not None else home / "qfa.sqlite3"

    configured_health_log = _pick_config(config_file, "core.health_log", "qfa.health_log")
    health_log_value = (
        _override(overrides, "core.health_log", "health_log")
        or _env(environ, "QFA_HEALTH_LOG")
        or configured_health_log
    )
    health_log = (
        _path(health_log_value, base=config_dir)
        if health_log_value is not None
        else home / "daemon-health.jsonl"
    )

    api_key = _override(overrides, "alpaca.api_key") or _env(environ, "ALPACA_API_KEY") or _pick_config(
        config_file, "alpaca.api_key"
    )
    secret_key = (
        _override(overrides, "alpaca.secret_key")
        or _env(environ, "ALPACA_SECRET_KEY")
        or _pick_config(config_file, "alpaca.secret_key")
    )
    paper_value = (
        _override(overrides, "alpaca.paper")
        if _override(overrides, "alpaca.paper") is not None
        else _env(environ, "ALPACA_PAPER")
    )
    if paper_value is None:
        paper_value = _pick_config(config_file, "alpaca.paper")
    data_feed = (
        _override(overrides, "alpaca.data_feed")
        or _env(environ, "ALPACA_DATA_FEED")
        or _pick_config(config_file, "alpaca.data_feed")
    )

    backend = (
        _override(overrides, "factor_store.backend", "features.backend")
        or _env(environ, "QFA_FACTOR_BACKEND", "QFA_FEATURE_BACKEND")
        or _pick_config(config_file, "factor_store.backend", "factors.backend", "features.backend")
        or "sqlite"
    )
    table = (
        _override(overrides, "factor_store.table", "features.table")
        or _env(environ, "QFA_FACTOR_TABLE", "QFA_FEATURE_TABLE")
        or _pick_config(config_file, "factor_store.table", "factors.table", "features.table")
        or "qfa-factor-observations"
    )
    region = (
        _override(overrides, "factor_store.region", "features.region")
        or _env(environ, "QFA_AWS_REGION", "AWS_REGION", "AWS_DEFAULT_REGION")
        or _pick_config(config_file, "factor_store.region", "factors.region", "features.region")
    )

    email_to = (
        _override(overrides, "email.to")
        or _env(environ, "QFA_NOTIFY_EMAIL_TO")
        or _pick_config(config_file, "notifications.email.to", "email.to")
    )
    smtp_url = (
        _override(overrides, "email.smtp_url")
        or _env(environ, "QFA_NOTIFY_EMAIL_SMTP_URL")
        or _pick_config(config_file, "notifications.email.smtp_url", "email.smtp_url")
    )
    smtp_host = _env(environ, "QFA_SMTP_HOST") or _pick_config(config_file, "notifications.email.smtp_host", "email.smtp_host")
    smtp_port = _env(environ, "QFA_SMTP_PORT") or _pick_config(config_file, "notifications.email.smtp_port", "email.smtp_port") or 587
    smtp_username = _env(environ, "QFA_SMTP_USERNAME") or _pick_config(config_file, "notifications.email.smtp_username", "email.smtp_username")
    smtp_password = _env(environ, "QFA_SMTP_PASSWORD") or _pick_config(config_file, "notifications.email.smtp_password", "email.smtp_password")
    sender = _env(environ, "QFA_NOTIFY_EMAIL_FROM") or _pick_config(config_file, "notifications.email.from", "notifications.email.sender", "email.from", "email.sender")
    tls_value = _env(environ, "QFA_SMTP_TLS") or _pick_config(config_file, "notifications.email.tls", "email.tls")

    repo_paths_value = (
        _override(overrides, "factor_repository.repository_paths", "factor_repository.path")
        or _env(environ, "QFA_FACTOR_REPOSITORY_PATHS", "QFA_FACTOR_REPOSITORY")
        or _pick_config(
            config_file,
            "factor_repository.repository_paths",
            "factor_repository.path",
            "factors.repository_paths",
            "factors.repository_path",
        )
    )
    if repo_paths_value is None:
        repo_paths: tuple[Path, ...] = ()
    else:
        repo_paths = tuple(_path(item, base=config_dir) for item in _tuple(repo_paths_value))

    max_staleness = _pick_config(
        config_file, "factor_repository.max_staleness_seconds", "factors.max_staleness_seconds"
    )

    return QFAConfig(
        core=CoreConfig(home=home, db=db, health_log=health_log),
        alpaca=AlpacaConfig(
            api_key=str(api_key) if api_key is not None else None,
            secret_key=str(secret_key) if secret_key is not None else None,
            paper=_bool(paper_value, default=True),
            data_feed=str(data_feed).lower() if data_feed else None,
        ),
        factor_store=FactorStoreConfig(
            backend=str(backend).strip().lower(),
            table=str(table),
            region=str(region) if region else None,
        ),
        email=EmailConfig(
            to=_tuple(email_to),
            smtp_url=str(smtp_url) if smtp_url else None,
            smtp_host=str(smtp_host) if smtp_host else None,
            smtp_port=int(smtp_port),
            smtp_username=str(smtp_username) if smtp_username else None,
            smtp_password=str(smtp_password) if smtp_password else None,
            sender=str(sender) if sender else None,
            tls=_bool(tls_value, default=True),
        ),
        factor_repository=FactorRepositoryConfig(
            repository_paths=repo_paths,
            max_staleness_seconds=int(max_staleness) if max_staleness is not None else None,
        ),
        config_path=selected_config_path if selected_config_path.exists() else None,
    )


def _redact_scalar(value: Any) -> Any:
    if value in (None, ""):
        return value
    text = str(value)
    if "://" in text:
        parts = urlsplit(text)
        if parts.username or parts.password:
            host = parts.hostname or ""
            if parts.port:
                host = f"{host}:{parts.port}"
            return urlunsplit((parts.scheme, f"********@{host}", parts.path, parts.query, parts.fragment))
    return "********" if len(text) <= 4 else f"********{text[-4:]}"


def _redact_dict(payload: Any, parent_key: str = "") -> Any:
    if isinstance(payload, dict):
        result = {}
        for key, value in payload.items():
            key_text = str(key).lower()
            if key_text in _SECRET_KEYS or any(secret in key_text for secret in ("secret", "password", "token")):
                result[key] = _redact_scalar(value)
            else:
                result[key] = _redact_dict(value, key_text)
        return result
    if isinstance(payload, list):
        return [_redact_dict(item, parent_key) for item in payload]
    return payload


def config_to_dict(config: QFAConfig) -> dict[str, Any]:
    def convert(value: Any) -> Any:
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, tuple):
            return [convert(item) for item in value]
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        return value

    return convert(asdict(config))


def redact_config(config: QFAConfig | dict[str, Any]) -> dict[str, Any]:
    payload = config_to_dict(config) if isinstance(config, QFAConfig) else config
    return _redact_dict(payload)
