"""Passphrase dialogs for first-run setup and unlock."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Shared stylesheet for passphrase dialogs
_DIALOG_STYLE = """
    QDialog {
        background: white;
    }
    QLabel {
        color: #333;
        font-size: 13px;
    }
    QLineEdit {
        padding: 8px 10px;
        font-size: 13px;
        border: 1px solid #C0C0C0;
        border-radius: 3px;
        background: white;
    }
    QLineEdit:focus {
        border: 1px solid #4A7AB5;
    }
    QPushButton {
        padding: 8px 20px;
        font-size: 13px;
        border: 1px solid #C0C0C0;
        border-radius: 3px;
        background: #F5F5F5;
        color: #333;
    }
    QPushButton:hover {
        background: #E8E8E8;
    }
    QPushButton:pressed {
        background: #D8D8D8;
    }
    QPushButton#primaryBtn {
        background: #2B579A;
        color: white;
        border: 1px solid #1E4270;
        font-weight: bold;
    }
    QPushButton#primaryBtn:hover {
        background: #34629F;
    }
    QPushButton#primaryBtn:disabled {
        background: #A0B4CC;
        border: 1px solid #8FA3BB;
    }
"""


class FirstRunDialog(QDialog):
    """Shown on first launch to create a master passphrase."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Closed Ledger — Setup")
        self.setFixedSize(440, 340)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.CustomizeWindowHint
        )
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Title / branding
        title = QLabel("Create Master Passphrase")
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #2B579A; padding-bottom: 4px;"
        )
        layout.addWidget(title)

        # Warning box
        warning_frame = QFrame()
        warning_frame.setStyleSheet(
            "background: #FFF3F3; border: 1px solid #FFCCCC; border-radius: 4px; padding: 8px;"
        )
        wf_layout = QVBoxLayout(warning_frame)
        wf_layout.setContentsMargins(10, 8, 10, 8)
        warning = QLabel(
            "This passphrase encrypts your financial data. "
            "If you lose it, your data CANNOT be recovered. There is no reset."
        )
        warning.setStyleSheet("color: #CC0000; font-size: 12px; font-weight: bold;")
        warning.setWordWrap(True)
        wf_layout.addWidget(warning)
        layout.addWidget(warning_frame)

        # Passphrase input
        pp_label = QLabel("Passphrase (minimum 8 characters):")
        pp_label.setStyleSheet("font-size: 12px; color: #555; font-weight: bold;")
        layout.addWidget(pp_label)
        self._passphrase_input = QLineEdit()
        self._passphrase_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._passphrase_input.setPlaceholderText("Enter passphrase")
        self._passphrase_input.textChanged.connect(self._validate)
        layout.addWidget(self._passphrase_input)

        # Confirm input
        cf_label = QLabel("Confirm passphrase:")
        cf_label.setStyleSheet("font-size: 12px; color: #555; font-weight: bold;")
        layout.addWidget(cf_label)
        self._confirm_input = QLineEdit()
        self._confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_input.setPlaceholderText("Re-enter passphrase")
        self._confirm_input.textChanged.connect(self._validate)
        layout.addWidget(self._confirm_input)

        # Validation message
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #CC0000; font-size: 12px;")
        self._status_label.setFixedHeight(18)
        layout.addWidget(self._status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._ok_button = QPushButton("Create")
        self._ok_button.setObjectName("primaryBtn")
        self._ok_button.setEnabled(False)
        self._ok_button.clicked.connect(self.accept)
        btn_layout.addWidget(self._ok_button)

        layout.addLayout(btn_layout)

    def _validate(self):
        passphrase = self._passphrase_input.text()
        confirm = self._confirm_input.text()

        if len(passphrase) < 8:
            self._status_label.setText("Passphrase must be at least 8 characters.")
            self._ok_button.setEnabled(False)
        elif passphrase != confirm:
            self._status_label.setText("Passphrases do not match.")
            self._ok_button.setEnabled(False)
        else:
            self._status_label.setText("")
            self._ok_button.setEnabled(True)

    def get_passphrase(self) -> str:
        return self._passphrase_input.text()

    def reject(self):
        self._passphrase_input.setText("")
        self._confirm_input.setText("")
        super().reject()

    def accept(self):
        super().accept()


class UnlockDialog(QDialog):
    """Shown on subsequent launches to unlock with existing passphrase."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Closed Ledger — Unlock")
        self.setFixedSize(400, 230)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.CustomizeWindowHint
        )
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel("Unlock Closed Ledger")
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #2B579A; padding-bottom: 4px;"
        )
        layout.addWidget(title)

        pp_label = QLabel("Enter your passphrase to unlock:")
        pp_label.setStyleSheet("font-size: 12px; color: #555;")
        layout.addWidget(pp_label)

        self._passphrase_input = QLineEdit()
        self._passphrase_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._passphrase_input.setPlaceholderText("Passphrase")
        self._passphrase_input.returnPressed.connect(self._try_unlock)
        layout.addWidget(self._passphrase_input)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #CC0000; font-size: 12px; font-weight: bold;")
        self._error_label.setFixedHeight(18)
        layout.addWidget(self._error_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._quit_button = QPushButton("Quit")
        self._quit_button.clicked.connect(self.reject)
        btn_layout.addWidget(self._quit_button)

        self._unlock_button = QPushButton("Unlock")
        self._unlock_button.setObjectName("primaryBtn")
        self._unlock_button.clicked.connect(self._try_unlock)
        btn_layout.addWidget(self._unlock_button)

        layout.addLayout(btn_layout)

        self._accepted = False

    def _try_unlock(self):
        if not self._passphrase_input.text():
            self._error_label.setText("Please enter your passphrase.")
            return
        self._accepted = True
        self.accept()

    def show_error(self, message: str = "Incorrect passphrase"):
        self._error_label.setText(message)
        self._passphrase_input.selectAll()
        self._passphrase_input.setFocus()
        self._accepted = False

    def get_passphrase(self) -> str:
        return self._passphrase_input.text()

    def clear_passphrase(self):
        self._passphrase_input.setText("")

    def reject(self):
        self._passphrase_input.setText("")
        super().reject()
