"""Application entry point: passphrase gate → database → main window."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from closed_ledger.db.connection import DatabaseManager
from closed_ledger.db.schema import initialize_schema
from closed_ledger.db.seed import seed_database
from closed_ledger.security.crypto import (
    create_key_check,
    derive_key,
    generate_salt,
    verify_key_check,
)
from closed_ledger.security.passphrase import FirstRunDialog, UnlockDialog
from closed_ledger.ui.main_window import MainWindow
from closed_ledger.utils.platform import (
    ensure_app_data_dir,
    get_key_check_path,
    get_salt_path,
)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv

    do_seed = "--seed" in argv

    app = QApplication(argv)
    app.setApplicationName("Closed Ledger")

    # Ensure app data directory exists with proper permissions
    ensure_app_data_dir()

    salt_path = get_salt_path()
    key_check_path = get_key_check_path()

    is_first_run = not salt_path.exists() or not key_check_path.exists()

    encryption_key = None

    if is_first_run:
        encryption_key = _handle_first_run(salt_path, key_check_path)
    else:
        encryption_key = _handle_unlock(salt_path, key_check_path)

    if encryption_key is None:
        # User cancelled
        return 0

    # Open the database
    db_manager = DatabaseManager(encryption_key)
    try:
        db_manager.open()
    except Exception as e:
        QMessageBox.critical(None, "Database Error", f"Failed to open database:\n{type(e).__name__}")
        return 1

    # Initialize schema (safe to call every time due to IF NOT EXISTS)
    try:
        conn = db_manager.get_connection()
        initialize_schema(conn)
    except Exception as e:
        QMessageBox.critical(None, "Schema Error", f"Failed to initialize schema:\n{type(e).__name__}")
        db_manager.close()
        return 1

    # Seed if requested
    if do_seed:
        try:
            seed_database(conn)
        except Exception as e:
            QMessageBox.warning(None, "Seed Warning", f"Seeding encountered an issue:\n{type(e).__name__}")

    # Show main window
    window = MainWindow()
    window.show()

    exit_code = app.exec()

    # Clean up: encrypt and secure-delete temp database
    db_manager.close()

    return exit_code


def _handle_first_run(salt_path, key_check_path) -> bytes | None:
    """Show FirstRunDialog, create salt and key_check, return encryption key."""
    dialog = FirstRunDialog()
    if dialog.exec() != FirstRunDialog.DialogCode.Accepted:
        return None

    passphrase = dialog.get_passphrase()

    # Generate salt and derive key
    salt = generate_salt()

    # Write salt with restrictive permissions
    with open(str(salt_path), "wb") as f:
        f.write(salt)
    import os
    if sys.platform != "win32":
        os.chmod(str(salt_path), 0o600)

    key = derive_key(passphrase, salt)

    # Clear passphrase from memory
    passphrase = ""

    # Create key check canary
    create_key_check(key, str(key_check_path))

    return key


def _handle_unlock(salt_path, key_check_path) -> bytes | None:
    """Show UnlockDialog, verify passphrase, return encryption key."""
    # Load salt
    with open(str(salt_path), "rb") as f:
        salt = f.read()

    dialog = UnlockDialog()

    while True:
        result = dialog.exec()
        if result != UnlockDialog.DialogCode.Accepted:
            return None

        passphrase = dialog.get_passphrase()
        key = derive_key(passphrase, salt)

        # Clear passphrase from memory
        passphrase = ""
        dialog.clear_passphrase()

        if verify_key_check(key, str(key_check_path)):
            return key
        else:
            dialog.show_error("Incorrect passphrase")
