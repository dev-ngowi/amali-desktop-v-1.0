import os
import sys
import logging
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDateEdit,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QFrame,
)
from PyQt5.QtCore import QDate, Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from Helper.db_conn import (
    DatabaseManager,
)  # Assuming db_conn.py is in the same directory

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_icon(icon_path):
    """Loads an icon from the given path."""
    logger.debug(f"Loading icon from: {icon_path}")
    return QIcon(QPixmap(icon_path))


def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
        logger.debug(f"Running in PyInstaller bundle, base path: {base_path}")
    else:
        base_path = os.path.abspath(".")
        logger.debug(f"Running in dev mode, base path: {base_path}")
    full_path = os.path.join(base_path, relative_path)
    logger.debug(
        f"Resolved path for {relative_path}: {full_path}, exists: {os.path.exists(full_path)}"
    )
    return full_path


class OrderSummaryView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.db_manager = DatabaseManager()
        self.current_filter = "completed"
        self.filter_buttons = {
            "completed": None,
            "in_cart": None,
            "settled": None,
            "voided": None,
        }
        logger.debug("OrderSummaryView initialized")
        self.init_ui()
        self.load_orders(use_filter=True)  # Load initial data with 'completed' status
        self.start_auto_refresh()

    def start_auto_refresh(self):
        """Starts the auto-refresh timer."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_refresh_orders)
        self.refresh_interval = 2 * 60 * 1000  # 2 minutes in milliseconds
        self.timer.start(self.refresh_interval)
        logger.debug(
            f"Auto-refresh timer started with interval: {self.refresh_interval} ms"
        )

    def auto_refresh_orders(self):
        """Automatically reloads orders based on the current filter and date."""
        logger.debug("Auto-refreshing orders...")
        self.load_orders(use_filter=True)

    def init_ui(self):
        """Set up the order summary UI to match the provided design."""
        logger.debug("Initializing UI")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Filter and Search Section
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(10)

        # Date Picker
        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy-MM-dd")  # Explicitly set display format
        self.date_picker.setStyleSheet(
            "QDateEdit {"
            "   padding: 8px;"
            "   border: 1px solid #dee2e6;"
            "   border-radius: 4px;"
            "   font-size: 14px;"
            "}"
        )
        self.date_picker.setMinimumSize(150, 35)
        self.date_picker.dateChanged.connect(self.load_orders)
        filter_layout.addWidget(self.date_picker)

        # Button container for centered filter buttons with background
        button_container = QWidget()
        button_container.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 4px;"
        )
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(5, 5, 5, 5)

        # Filter Buttons with click handlers
        all_btn = QPushButton("Completed (0)")
        all_btn.clicked.connect(lambda: self.filter_orders("completed"))
        all_btn.setStyleSheet(
            "background-color: #3498db; color: white; padding: 5px 10px; border-radius: 4px;"
        )
        button_layout.addWidget(all_btn)
        self.filter_buttons["completed"] = all_btn

        in_cart_btn = QPushButton("In Cart (0)")
        in_cart_btn.clicked.connect(lambda: self.filter_orders("in_cart"))
        in_cart_btn.setStyleSheet(
            "background-color: #f39c12; color: white; padding: 5px 10px; border-radius: 4px;"
        )
        button_layout.addWidget(in_cart_btn)
        self.filter_buttons["in_cart"] = in_cart_btn

        settled_btn = QPushButton("Settled (0)")
        settled_btn.clicked.connect(lambda: self.filter_orders("settled"))
        settled_btn.setStyleSheet(
            "background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 4px;"
        )
        button_layout.addWidget(settled_btn)
        self.filter_buttons["settled"] = settled_btn

        voided_btn = QPushButton("Voided (0)")
        voided_btn.clicked.connect(lambda: self.filter_orders("voided"))
        voided_btn.setStyleSheet(
            "background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 4px;"
        )
        button_layout.addWidget(voided_btn)
        self.filter_buttons["voided"] = voided_btn

        # Add stretch before and after button container to center it
        filter_layout.addStretch(1)
        filter_layout.addWidget(button_container)
        filter_layout.addStretch(1)

        # Search Bar
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search")
        search_bar.setStyleSheet(
            "padding: 5px; border: 1px solid #dee2e6; border-radius: 4px;"
        )
        search_bar.setFixedWidth(200)
        filter_layout.addWidget(search_bar)

        # Add filter widget with separators
        main_layout.addWidget(
            QFrame(
                frameShape=QFrame.HLine,
                frameShadow=QFrame.Sunken,
                styleSheet="color: #dee2e6;",
            )
        )
        main_layout.addWidget(filter_widget)
        main_layout.addWidget(
            QFrame(
                frameShape=QFrame.HLine,
                frameShadow=QFrame.Sunken,
                styleSheet="color: #dee2e6;",
            )
        )

        # Action Buttons (Recall, Settle, Void, Reprint Receipt)
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(10, 0, 10, 0)
        action_layout.setSpacing(8)

        button_container = QWidget()
        button_container.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 4px;"
        )
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(5, 5, 5, 5)

        recall_btn = QPushButton("Recall")
        recall_btn.setIcon(load_icon(get_resource_path("Resources/Images/recall.png")))
        recall_btn.setStyleSheet(
            "background-color: #3498db; color: white; padding: 3px 6px; border-radius: 4px; font-size: 12px;"
        )
        recall_btn.setMaximumSize(80, 25)
        button_layout.addWidget(recall_btn)

        settle_btn = QPushButton("Settle")
        settle_btn.setIcon(load_icon(get_resource_path("Resources/Images/settle.png")))
        settle_btn.setStyleSheet(
            "background-color: #3498db; color: white; padding: 3px 6px; border-radius: 4px; font-size: 12px;"
        )
        settle_btn.setMaximumSize(80, 25)
        button_layout.addWidget(settle_btn)

        void_btn = QPushButton("Void")
        void_btn.setIcon(load_icon(get_resource_path("Resources/Images/void.png")))
        void_btn.setStyleSheet(
            "background-color: #3498db; color: white; padding: 3px 6px; border-radius: 4px; font-size: 12px;"
        )
        void_btn.setMaximumSize(80, 25)
        button_layout.addWidget(void_btn)

        reprint_btn = QPushButton("Reprint Receipt")
        reprint_btn.setIcon(
            load_icon(get_resource_path("Resources/Images/reprint.png"))
        )
        reprint_btn.setStyleSheet(
            "background-color: #3498db; color: white; padding: 3px 6px; border-radius: 4px; font-size: 12px;"
        )
        reprint_btn.setMaximumSize(120, 25)
        button_layout.addWidget(reprint_btn)

        action_layout.addStretch(1)
        action_layout.addWidget(button_container)
        action_layout.addStretch(1)

        main_layout.addWidget(
            QFrame(
                frameShape=QFrame.HLine,
                frameShadow=QFrame.Sunken,
                styleSheet="color: #dee2e6;",
            )
        )
        main_layout.addWidget(action_widget)
        main_layout.addWidget(
            QFrame(
                frameShape=QFrame.HLine,
                frameShadow=QFrame.Sunken,
                styleSheet="color: #dee2e6;",
            )
        )

        # Table to display orders
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["", "Order No", "Time", "Receipt No", "Status", "Total Amount"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.verticalHeader().hide()
        self.table.setStyleSheet(
            """
            QTableWidget { background: white; border-radius: 8px; border: 1px solid #dee2e6; }
            QHeaderView::section { background: #e9ecef; padding: 8px; }
            """
        )
        self.table.setMinimumSize(600, 400)  # Ensure visibility
        self.table.setRowCount(0)
        main_layout.addWidget(self.table)
        self.table.show()

        logger.debug("UI initialization complete")

    def load_orders(self, use_filter=True):
        if use_filter:
            qdate = self.date_picker.date()
            date = qdate.toString("yyyy-MM-dd")  # Match database date format
        else:
            date = None  # Show all dates when not using filter

        orders = self.db_manager.get_orders_by_status(
            self.current_filter if use_filter else None, date
        )
        self.set_orders(orders)
        self.update_button_counts()

    def filter_orders(self, status):
        """Handle filter button clicks and update display."""
        logger.debug(f"Filtering orders by status: {status}")
        print(f"Filtering orders by status: {status}")  # Debug print
        self.current_filter = status
        self.load_orders(use_filter=True)

        for filter_name, btn in self.filter_buttons.items():
            if filter_name == status:
                btn.setStyleSheet(
                    "background-color: #3498db; color: white; padding: 5px 10px; border-radius: 4px;"
                )
            else:
                default_styles = {
                    "completed": "background-color: #e9ecef; padding: 5px 10px; border-radius: 4px;",
                    "in_cart": "background-color: #f39c12; color: white; padding: 5px 10px; border-radius: 4px;",
                    "settled": "background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 4px;",
                    "voided": "background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 4px;",
                }
                btn.setStyleSheet(default_styles[filter_name])

    def update_button_counts(self):
        all_orders = self.db_manager.get_orders_by_status(None, None)  # Get all orders
        counts = {
            "completed": len(
                [o for o in all_orders if o["status"].lower() == "completed"]
            ),
            "in_cart": len([o for o in all_orders if o["status"].lower() == "in-cart"]),
            "settled": len([o for o in all_orders if o["status"].lower() == "settled"]),
            "voided": len([o for o in all_orders if o["status"].lower() == "voided"]),
        }

        for filter_name, btn in self.filter_buttons.items():
            btn.setText(
                f"{filter_name.replace('_', ' ').title()} ({counts[filter_name]})"
            )

    def set_orders(self, orders):
        self.table.setRowCount(0)
        for order in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)
            logger.debug(f"Adding row {row} with order: {order}")
            print(f"Adding row {row} with order: {order}")

            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, checkbox_widget)

            # Use 'order_no' instead of 'order_number'
            self.table.setItem(row, 1, QTableWidgetItem(str(order.get("order_no", ""))))

            # Use 'time' to display the time
            self.table.setItem(row, 2, QTableWidgetItem(str(order.get("time", ""))))

            self.table.setItem(
                row, 3, QTableWidgetItem(str(order.get("receipt_no", "")))
            )
            self.table.setItem(row, 4, QTableWidgetItem(str(order.get("status", ""))))
            self.table.setItem(
                row, 5, QTableWidgetItem(f"{order.get('total_amount', 0.0):.2f}")
            )

        logger.debug(f"Table updated with {self.table.rowCount()} rows")
        print(f"Table updated with {self.table.rowCount()} rows")
        self.table.resizeColumnsToContents()
        self.table.viewport().update()
        self.main_window.repaint()

    def go_back(self):
        """Switch back to the dashboard view."""
        logger.debug("Going back to dashboard")
        print("Going back to dashboard")  # Debug print
        self.main_window.stacked_widget.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()  # Replace with your actual main window class
    view = OrderSummaryView(main_window)
    view.show()
    sys.exit(app.exec_())
