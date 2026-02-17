"""Database connection manager with encrypt/decrypt lifecycle."""

import glob
import os
import sqlite3
import tempfile

from closed_ledger.security.crypto import decrypt_file, encrypt_file, secure_delete
from closed_ledger.utils.platform import get_db_encrypted_path, get_db_temp_path


class DatabaseManager:
    """Manages the SQLite database with encryption at rest.

    Lifecycle: decrypt .db.enc → open connection → use → close → encrypt → secure-delete temp.
    """

    def __init__(self, encryption_key: bytes):
        self._key = encryption_key
        self._conn: sqlite3.Connection | None = None
        self._temp_path: str | None = None

    def open(self) -> None:
        """Decrypt the database (or create fresh) and open a connection."""
        self._cleanup_stale_temp_files()

        enc_path = get_db_encrypted_path()
        temp_path = get_db_temp_path()
        self._temp_path = str(temp_path)

        if enc_path.exists():
            decrypt_file(str(enc_path), self._temp_path, self._key)
        else:
            # Create a fresh empty database at the temp path
            conn = sqlite3.connect(self._temp_path)
            conn.close()

        self._conn = sqlite3.connect(self._temp_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Commit, close, encrypt back, and secure-delete the temp file."""
        if self._conn is not None:
            try:
                self._conn.commit()
            except Exception:
                pass
            self._conn.close()
            self._conn = None

        if self._temp_path and os.path.exists(self._temp_path):
            enc_path = get_db_encrypted_path()
            encrypt_file(self._temp_path, str(enc_path), self._key)
            secure_delete(self._temp_path)
            # Also clean up WAL and SHM files
            for suffix in ("-wal", "-shm"):
                wal_path = self._temp_path + suffix
                if os.path.exists(wal_path):
                    secure_delete(wal_path)
            self._temp_path = None

    def get_connection(self) -> sqlite3.Connection:
        """Return the active SQLite connection."""
        if self._conn is None:
            raise RuntimeError("Database is not open. Call open() first.")
        return self._conn

    def _cleanup_stale_temp_files(self) -> None:
        """Remove any leftover temp database files from previous crashes."""
        temp_dir = tempfile.gettempdir()
        pattern = os.path.join(temp_dir, "closed_ledger_*.db")
        for stale_file in glob.glob(pattern):
            try:
                secure_delete(stale_file)
                # Clean up WAL/SHM too
                for suffix in ("-wal", "-shm"):
                    wal = stale_file + suffix
                    if os.path.exists(wal):
                        secure_delete(wal)
            except Exception:
                pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
