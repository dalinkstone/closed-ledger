"""Encryption, key derivation, and secure file operations."""

import base64
import hashlib
import os
import sys

from cryptography.fernet import Fernet, InvalidToken

CANARY_STRING = b"CLOSED_LEDGER_KEY_CHECK"


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a passphrase using PBKDF2-HMAC-SHA256.

    Returns a base64url-encoded 32-byte key suitable for Fernet.
    """
    raw_key = hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        salt,
        iterations=600_000,
    )
    return base64.urlsafe_b64encode(raw_key)


def generate_salt() -> bytes:
    """Generate a random 32-byte salt."""
    return os.urandom(32)


def encrypt_file(source_path: str, dest_path: str, key: bytes) -> None:
    """Read source file, encrypt with Fernet, write to dest_path with 0o600 permissions."""
    f = Fernet(key)
    with open(source_path, "rb") as src:
        plaintext = src.read()
    ciphertext = f.encrypt(plaintext)
    with open(dest_path, "wb") as dst:
        dst.write(ciphertext)
    if sys.platform != "win32":
        os.chmod(dest_path, 0o600)


def decrypt_file(source_path: str, dest_path: str, key: bytes) -> None:
    """Read encrypted file, decrypt with Fernet, write to dest_path with 0o600 permissions."""
    f = Fernet(key)
    with open(source_path, "rb") as src:
        ciphertext = src.read()
    plaintext = f.decrypt(ciphertext)
    with open(dest_path, "wb") as dst:
        dst.write(plaintext)
    if sys.platform != "win32":
        os.chmod(dest_path, 0o600)


def secure_delete(file_path: str) -> None:
    """Overwrite file with random bytes, then delete it. No-op if file doesn't exist."""
    if not os.path.exists(file_path):
        return
    file_size = os.path.getsize(file_path)
    if file_size > 0:
        with open(file_path, "wb") as f:
            f.write(os.urandom(file_size))
            f.flush()
            os.fsync(f.fileno())
    os.remove(file_path)


def create_key_check(key: bytes, path: str) -> None:
    """Encrypt the canary string and write to path for passphrase verification."""
    f = Fernet(key)
    token = f.encrypt(CANARY_STRING)
    with open(path, "wb") as fh:
        fh.write(token)
    if sys.platform != "win32":
        os.chmod(path, 0o600)


def verify_key_check(key: bytes, path: str) -> bool:
    """Decrypt the canary file and verify it matches. Returns False on wrong key."""
    try:
        f = Fernet(key)
        with open(path, "rb") as fh:
            token = fh.read()
        plaintext = f.decrypt(token)
        return plaintext == CANARY_STRING
    except (InvalidToken, Exception):
        return False
