"""Paths and file permissions. All data stored within the repo's data/ directory."""

import os
import sys
import tempfile
from pathlib import Path


def _get_project_root() -> Path:
    """Return the repository root (parent of the closed_ledger package)."""
    # This file is at: <repo>/closed_ledger/utils/platform.py
    return Path(__file__).resolve().parent.parent.parent


def get_app_data_dir() -> Path:
    """Return the data directory inside the project root.

    All persistent files (encrypted DB, salt, key_check, config, backups)
    live here. This directory is gitignored so each machine maintains its
    own independent passphrase and encrypted database.
    """
    return _get_project_root() / "data"


def ensure_app_data_dir() -> Path:
    """Create the data directory with restrictive permissions if needed."""
    app_dir = get_app_data_dir()
    if not app_dir.exists():
        app_dir.mkdir(parents=True, mode=0o700)
    else:
        if sys.platform != "win32":
            os.chmod(app_dir, 0o700)
    return app_dir


def get_db_encrypted_path() -> Path:
    return get_app_data_dir() / "closed-ledger.db.enc"


def get_db_temp_path() -> Path:
    """Return a temp file path inside data/ for the decrypted database."""
    data_dir = get_app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix="closed_ledger_", suffix=".db", dir=str(data_dir))
    os.close(fd)
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
