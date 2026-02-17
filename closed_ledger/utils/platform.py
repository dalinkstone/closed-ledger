"""Platform-specific paths and file permissions."""

import os
import sys
import tempfile
from pathlib import Path


def get_app_data_dir() -> Path:
    """Return the platform-appropriate app data directory."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "closed-ledger"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "closed-ledger"
        return Path.home() / "closed-ledger"
    else:
        # Linux / other Unix
        xdg = os.environ.get("XDG_DATA_HOME", "")
        if xdg:
            return Path(xdg) / "closed-ledger"
        return Path.home() / ".local" / "share" / "closed-ledger"


def ensure_app_data_dir() -> Path:
    """Create the app data directory with restrictive permissions if needed."""
    app_dir = get_app_data_dir()
    if not app_dir.exists():
        app_dir.mkdir(parents=True, mode=0o700)
    else:
        # Ensure permissions are correct even if dir already exists
        if sys.platform != "win32":
            os.chmod(app_dir, 0o700)
    return app_dir


def get_db_encrypted_path() -> Path:
    return get_app_data_dir() / "closed-ledger.db.enc"


def get_db_temp_path() -> Path:
    """Return a temp file path with a random name for the decrypted database."""
    fd, path = tempfile.mkstemp(prefix="closed_ledger_", suffix=".db")
    os.close(fd)
    # Set restrictive permissions
    if sys.platform != "win32":
        os.chmod(path, 0o600)
    return Path(path)


def get_salt_path() -> Path:
    return get_app_data_dir() / "salt"


def get_key_check_path() -> Path:
    return get_app_data_dir() / "key_check"


def get_backups_dir() -> Path:
    return get_app_data_dir() / "backups"


def get_config_path() -> Path:
    return get_app_data_dir() / "config.json"
