"""Main window shell — Quicken-style sidebar, tab bar, stacked content, status bar."""

import json
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QTabBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from closed_ledger.utils.platform import get_config_path


# Tab names in ALL CAPS matching Quicken
TAB_NAMES = [
    "HOME",
    "SPENDING",
    "BILLS & INCOME",
    "PLANNING",
    "INVESTING",
    "PROPERTY & DEBT",
    "REPORTS",
]

# Placeholder account data for the Phase 1 shell — replaced with live data in Phase 2
_PLACEHOLDER_GROUPS = [
    {
        "name": "Banking",
        "total": "$12,199",
        "accounts": [
            ("Family Checking", "$1,491", False),
            ("My Checking", "$2,832", False),
            ("My Savings", "$13,200", False),
            ("My Credit Card", "-$5,325", True),
        ],
    },
    {
        "name": "Investing",
        "total": "$178,094",
        "accounts": [
            ("Brokerage", "$95,164", False),
            ("401(k)", "$82,930", False),
        ],
    },
    {
        "name": "Property & Debt",
        "total": "$518,609",
        "accounts": [
            ("Car Value", "$20,000", False),
            ("House", "$800,000", False),
            ("Auto Loan", "-$18,288", True),
            ("Home Loan", "-$283,043", True),
            ("Loan", "-$339,924", True),
        ],
    },
    {
        "name": "Savings Goals",
        "total": "$4,750",
        "accounts": [
            ("Dream Home Fund", "$4,050", False),
            ("Vacation Fund", "$700", False),
        ],
    },
]


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Closed Ledger")
        self._load_geometry()

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        main_layout.addWidget(self._build_sidebar())

        # --- Sidebar/content separator line ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("color: #D0D0D0;")
        main_layout.addWidget(separator)

        # --- Right panel (tab bar + content) ---
        main_layout.addWidget(self._build_right_panel())

        # --- Status bar ---
        self._build_status_bar()

    # ------------------------------------------------------------------ sidebar
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background: #F5F5F5;")

        outer = QVBoxLayout(sidebar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # -- Header row: disclosure ▾ ACCOUNTS  [refresh] [+] [gear] --
        header = QWidget()
        header.setStyleSheet("background: #EBEBEB; border-bottom: 1px solid #D0D0D0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)
        header_layout.setSpacing(4)

        disclosure = QLabel("\u25BE")  # ▾
        disclosure.setStyleSheet("font-size: 11px; color: #555;")
        header_layout.addWidget(disclosure)

        title = QLabel("ACCOUNTS")
        title.setStyleSheet(
            "font-weight: bold; font-size: 11px; color: #333; letter-spacing: 0.5px;"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()

        for icon_char, tooltip in [
            ("\u21BB", "Refresh"),   # ↻
            ("+", "Add Account"),
            ("\u2699", "Settings"),  # ⚙
        ]:
            btn = QToolButton()
            btn.setText(icon_char)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(
                """
                QToolButton {
                    border: none;
                    color: #555;
                    font-size: 14px;
                    padding: 2px 4px;
                    background: transparent;
                }
                QToolButton:hover {
                    color: #2B579A;
                    background: #D8D8D8;
                    border-radius: 3px;
                }
                """
            )
            btn.setFixedSize(24, 24)
            header_layout.addWidget(btn)

        outer.addWidget(header)

        # -- Scrollable account area --
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea { border: none; background: #F5F5F5; }
            QScrollBar:vertical {
                width: 6px; background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #C0C0C0; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            """
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: #F5F5F5;")
        account_layout = QVBoxLayout(scroll_content)
        account_layout.setContentsMargins(0, 4, 0, 4)
        account_layout.setSpacing(0)

        # -- "All Transactions" link --
        all_txn = QPushButton("All Transactions")
        all_txn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_txn.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 6px 12px;
                font-size: 13px;
                color: #2B579A;
                border: none;
                background: transparent;
                font-weight: bold;
            }
            QPushButton:hover {
                text-decoration: underline;
                background: #E3EDF7;
            }
            """
        )
        account_layout.addWidget(all_txn)

        # -- Account groups (placeholder — replaced with QTreeView in Phase 2) --
        for group in _PLACEHOLDER_GROUPS:
            account_layout.addWidget(
                self._build_group_widget(
                    group["name"], group["total"], group["accounts"]
                )
            )

        account_layout.addStretch()
        scroll.setWidget(scroll_content)
        outer.addWidget(scroll)

        # -- Net Worth footer --
        net_worth_frame = QWidget()
        net_worth_frame.setStyleSheet(
            "background: #EBEBEB; border-top: 1px solid #D0D0D0;"
        )
        nw_layout = QHBoxLayout(net_worth_frame)
        nw_layout.setContentsMargins(12, 8, 12, 4)

        nw_label = QLabel("Net Worth")
        nw_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        nw_layout.addWidget(nw_label)
        nw_layout.addStretch()

        nw_amount = QLabel("$713,652")
        nw_amount.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        nw_layout.addWidget(nw_amount)

        outer.addWidget(net_worth_frame)

        # -- Add Account link --
        add_account = QPushButton("+ Add an Account")
        add_account.setCursor(Qt.CursorShape.PointingHandCursor)
        add_account.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 6px 12px;
                font-size: 12px;
                color: #2B579A;
                border: none;
                background: #F5F5F5;
                border-top: 1px solid #D0D0D0;
            }
            QPushButton:hover {
                text-decoration: underline;
                background: #E3EDF7;
            }
            """
        )
        outer.addWidget(add_account)

        return sidebar

    def _build_group_widget(
        self, name: str, total: str, accounts: list[tuple[str, str, bool]]
    ) -> QWidget:
        """Build a collapsible account group widget for the sidebar placeholder."""
        group_widget = QWidget()
        group_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(group_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Group header row
        group_header = QWidget()
        group_header.setStyleSheet(
            """
            QWidget { background: transparent; }
            QWidget:hover { background: #E3EDF7; }
            """
        )
        gh_layout = QHBoxLayout(group_header)
        gh_layout.setContentsMargins(8, 5, 12, 5)
        gh_layout.setSpacing(4)

        disclosure = QLabel("\u25BE")  # ▾ (expanded)
        disclosure.setStyleSheet("font-size: 10px; color: #666;")
        gh_layout.addWidget(disclosure)

        name_label = QLabel(name)
        name_label.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #333;"
        )
        gh_layout.addWidget(name_label)
        gh_layout.addStretch()

        is_negative = total.startswith("-")
        total_label = QLabel(total)
        total_color = "#CC0000" if is_negative else "#333"
        total_label.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {total_color};"
        )
        gh_layout.addWidget(total_label)

        layout.addWidget(group_header)

        # Individual accounts
        for acct_name, acct_balance, is_neg in accounts:
            row = QWidget()
            row.setStyleSheet(
                """
                QWidget { background: transparent; }
                QWidget:hover { background: #E3EDF7; }
                """
            )
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(28, 3, 12, 3)
            row_layout.setSpacing(6)

            acct_label = QLabel(acct_name)
            acct_label.setStyleSheet("font-size: 12px; color: #333;")
            row_layout.addWidget(acct_label)
            row_layout.addStretch()

            bal_color = "#CC0000" if is_neg else "#333"
            bal_label = QLabel(acct_balance)
            bal_label.setStyleSheet(f"font-size: 12px; color: {bal_color};")
            row_layout.addWidget(bal_label)

            layout.addWidget(row)

        return group_widget

    # -------------------------------------------------------------- right panel
    def _build_right_panel(self) -> QWidget:
        right_panel = QWidget()
        right_panel.setStyleSheet("background: white;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # -- Tab bar container (dark navy blue background) --
        tab_container = QWidget()
        tab_container.setStyleSheet("background: #2B579A;")
        tab_container.setFixedHeight(36)
        tc_layout = QHBoxLayout(tab_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(0)

        self._tab_bar = QTabBar()
        self._tab_bar.setExpanding(False)
        self._tab_bar.setDrawBase(False)
        self._tab_bar.setStyleSheet(
            """
            QTabBar {
                background: #2B579A;
                border: none;
            }
            QTabBar::tab {
                background: #2B579A;
                color: rgba(255, 255, 255, 0.85);
                padding: 8px 14px;
                font-size: 11px;
                font-weight: bold;
                border: none;
                min-width: 60px;
                letter-spacing: 0.5px;
            }
            QTabBar::tab:selected {
                background: #1E4270;
                color: white;
                border-bottom: 2px solid #5BA3E6;
            }
            QTabBar::tab:hover:!selected {
                background: #34629F;
                color: white;
            }
            """
        )

        for name in TAB_NAMES:
            self._tab_bar.addTab(name)

        tc_layout.addWidget(self._tab_bar)
        tc_layout.addStretch()

        right_layout.addWidget(tab_container)

        # -- Stacked content area (white background) --
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: white;")

        display_names = [
            "Overview", "Spending", "Bills & Income", "Planning",
            "Investing", "Property & Debt", "Reports",
        ]

        for display_name in display_names:
            page = QWidget()
            page.setStyleSheet("background: white;")
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(24, 20, 24, 20)

            # Page title
            title = QLabel(display_name)
            title.setStyleSheet(
                "font-size: 22px; font-weight: bold; color: #333; "
                "padding-bottom: 12px; background: white;"
            )
            page_layout.addWidget(title)

            # Separator under title
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color: #E0E0E0;")
            page_layout.addWidget(line)

            # Placeholder content
            placeholder = QLabel(f"Content for {display_name} will appear here.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(
                "font-size: 14px; color: #999; padding-top: 40px; background: white;"
            )
            page_layout.addWidget(placeholder)
            page_layout.addStretch()

            self._stack.addWidget(page)

        self._tab_bar.currentChanged.connect(self._stack.setCurrentIndex)

        right_layout.addWidget(self._stack)
        return right_panel

    # --------------------------------------------------------------- status bar
    def _build_status_bar(self) -> None:
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(
            """
            QStatusBar {
                background: #F0F0F0;
                border-top: 1px solid #D0D0D0;
                font-size: 12px;
                color: #555;
            }
            QStatusBar::item { border: none; }
            """
        )
        self.setStatusBar(self._status_bar)

        # Left section
        self._status_txn_count = QLabel("0 Transactions")
        self._status_txn_count.setStyleSheet("font-size: 12px; color: #555; padding: 2px 8px;")
        self._status_bar.addWidget(self._status_txn_count)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._status_bar.addWidget(spacer)

        # Center — Current Balance
        self._status_current_bal = QLabel("Current Balance:  —")
        self._status_current_bal.setStyleSheet("font-size: 12px; color: #555; padding: 2px 16px;")
        self._status_bar.addWidget(self._status_current_bal)

        # Right — Ending Balance
        self._status_ending_bal = QLabel("Ending Balance:  —")
        self._status_ending_bal.setStyleSheet("font-size: 12px; color: #555; padding: 2px 8px;")
        self._status_bar.addPermanentWidget(self._status_ending_bal)

    # --------------------------------------------------------- geometry persist
    def _load_geometry(self) -> None:
        config_path = get_config_path()
        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                x = config.get("window_x", 100)
                y = config.get("window_y", 100)
                w = config.get("window_width", 1200)
                h = config.get("window_height", 800)
                self.setGeometry(x, y, w, h)
            else:
                self.resize(1200, 800)
        except Exception:
            self.resize(1200, 800)

    def _save_geometry(self) -> None:
        config_path = get_config_path()
        geo = self.geometry()
        config = {}
        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
        except Exception:
            pass

        config["window_x"] = geo.x()
        config["window_y"] = geo.y()
        config["window_width"] = geo.width()
        config["window_height"] = geo.height()

        try:
            with open(str(config_path), "w") as f:
                json.dump(config, f, indent=2)
            if os.name != "nt":
                os.chmod(str(config_path), 0o600)
        except Exception:
            pass

    def closeEvent(self, event):
        self._save_geometry()
        super().closeEvent(event)
