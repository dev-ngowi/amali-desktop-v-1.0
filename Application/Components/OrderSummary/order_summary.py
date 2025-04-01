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
    QSizePolicy,
    QMessageBox,
)
from PyQt5.QtCore import QDate, Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap

from Application.Components.OrderSummary.Recall.view import RecallView


# --- Mock Models for Standalone Running (Replace with your actual imports) ---
class MockCartModel:
    def get_carts_by_status(self, status=None, date=None):
        # Return dummy data matching the expected format
        all_data = [
            {
                "order_number": "C1001",
                "time": "2025-03-31 10:00:00",
                "customer_id": 1,
                "status": "in-cart",
                "total_amount": 50.0,
            },
            {
                "order_number": "C1002",
                "time": "2025-03-31 10:05:00",
                "customer_id": 2,
                "status": "settled",
                "total_amount": 75.5,
            },
            {
                "order_number": "C1003",
                "time": "2025-03-31 10:10:00",
                "customer_id": 1,
                "status": "in-cart",
                "total_amount": 25.0,
            },
            {
                "order_number": "C1004",
                "time": "2025-03-30 11:00:00",
                "customer_id": 3,
                "status": "settled",
                "total_amount": 120.0,
            },  # Yesterday
            {
                "order_number": "C1005",
                "time": "2025-03-31 11:05:00",
                "customer_id": 4,
                "status": "voided",
                "total_amount": 30.0,
            },
        ]
        filtered_data = []
        target_date_str = date  # Already yyyy-MM-dd
        for item in all_data:
            item_date_str = item["time"].split(" ")[0]  # Extract date part
            date_match = (date is None) or (item_date_str == target_date_str)
            status_match = (status is None) or (item["status"] == status)

            if date_match and status_match:
                filtered_data.append(item)
        logger.debug(
            f"[MockCartModel] get_carts_by_status(status={status}, date={date}) -> returning {len(filtered_data)} items"
        )
        return filtered_data


class MockOrderSummaryModel:
    def get_orders_by_status(self, status=None, date=None):
        # Return dummy data matching the expected format
        all_data = [
            {
                "order_no": "O2001",
                "date": "2025-03-31",
                "receipt_no": "R5001",
                "status": "completed",
                "total_amount": 150.0,
            },
            {
                "order_no": "O2002",
                "date": "2025-03-31",
                "receipt_no": "R5002",
                "status": "voided",
                "total_amount": 80.0,
            },
            {
                "order_no": "O2003",
                "date": "2025-03-30",
                "receipt_no": "R5003",
                "status": "completed",
                "total_amount": 200.0,
            },  # Yesterday
            {
                "order_no": "O2004",
                "date": "2025-03-31",
                "receipt_no": "R5004",
                "status": "completed",
                "total_amount": 95.0,
            },
        ]
        filtered_data = []
        target_date_str = date  # Already yyyy-MM-dd
        for item in all_data:
            item_date_str = item["date"]
            date_match = (date is None) or (item_date_str == target_date_str)
            status_match = (status is None) or (item["status"] == status)

            if date_match and status_match:
                # Combine completed/voided if status is 'completed' for the view logic
                if status == "completed" and item["status"] in ["completed", "voided"]:
                    filtered_data.append(item)
                elif item["status"] == status:  # Specific status match otherwise
                    filtered_data.append(item)

        logger.debug(
            f"[MockOrderModel] get_orders_by_status(status={status}, date={date}) -> returning {len(filtered_data)} items"
        )
        return filtered_data


# Use mocks if original imports fail (e.g., running standalone)
try:
    from Application.Components.OrderSummary.Carts.modal import CartModel
    from Application.Components.OrderSummary.modal import OrderSummaryModel
except ImportError:
    logging.Logger.warning(
        "Could not import actual models. Using Mock Models for demonstration."
    )
    CartModel = MockCartModel
    OrderSummaryModel = MockOrderSummaryModel
# --- End of Mock Models ---


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s",  # Added funcName
)
logger = logging.getLogger(__name__)


def load_icon(icon_path):
    """Loads an icon from the given path."""
    logger.debug(f"Attempting to load icon from: {icon_path}")
    pixmap = QPixmap(icon_path)
    if pixmap.isNull():
        logger.warning(f"Failed to load icon: {icon_path}. Pixmap is null.")
        # Return an empty icon or handle the error as appropriate
        return QIcon()
    logger.debug(f"Icon loaded successfully: {icon_path}")
    return QIcon(pixmap)


def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.debug(f"Running in PyInstaller bundle, base path: {base_path}")
    except AttributeError:
        # Not running in a bundle, use the script's directory
        base_path = os.path.abspath(
            os.path.dirname(__file__)
        )  # More robust for finding relative paths
        logger.debug(f"Running in dev mode, base path: {base_path}")

    full_path = os.path.join(base_path, relative_path)
    logger.debug(
        f"Resolved path for '{relative_path}': '{full_path}', Exists: {os.path.exists(full_path)}"
    )
    if not os.path.exists(full_path):
        logger.error(f"Resource path does not exist: {full_path}")
        # Fallback or error handling might be needed here depending on the resource
        # For icons, load_icon handles the null pixmap.
    return full_path


class OrderSummaryView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        # Make main_window optional for standalone running
        self.main_window = (
            main_window if main_window else QWidget()
        )  # Avoid None errors
        self.cart_model = CartModel()  # For carts table
        self.order_model = OrderSummaryModel()  # For orders table
        self.current_filter = "completed"  # Default filter
        self.filter_buttons = {
            "completed": None,
            "in-cart": None,
            "settled": None,
            "voided": None,
        }
        # Action buttons
        self.recall_btn = None
        self.settle_btn = None
        self.void_btn = None
        self.reprint_btn = None
        self.timer = None  # Initialize timer attribute

        logger.debug("OrderSummaryView initializing...")
        self.init_ui()
        logger.debug("UI Initialized. Loading initial orders...")
        # Load initial data with 'completed' status for the current date
        self.load_orders(use_filter=True)
        self.start_auto_refresh()
        logger.debug("OrderSummaryView initialization complete.")

    def start_auto_refresh(self):
        """Starts the auto-refresh timer."""
        if self.timer is None:
            self.timer = QTimer(self)  # Parent it to self
            self.timer.timeout.connect(self.auto_refresh_orders)
            self.refresh_interval = 2 * 60 * 1000  # 2 minutes in milliseconds
            self.timer.start(self.refresh_interval)
            logger.debug(
                f"Auto-refresh timer started with interval: {self.refresh_interval} ms"
            )
        else:
            logger.debug("Auto-refresh timer already running.")

    def auto_refresh_orders(self):
        """Automatically reloads data based on the current filter and date."""
        logger.debug("Auto-refresh triggered.")
        self.load_orders(use_filter=True)

    def init_ui(self):
        """Set up the order summary UI."""
        logger.debug("Initializing UI components")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Add some margins
        main_layout.setSpacing(10)

        # --- Filter and Search Section ---
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)  # No inner margins for this row
        filter_layout.setSpacing(10)

        # Date Picker
        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy-MM-dd")
        self.date_picker.setStyleSheet(
            "QDateEdit { padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: white; }"
            "QDateEdit::drop-down { border: none; }"
            "QCalendarWidget QToolButton { color: black; }"  # Ensure calendar buttons are visible
        )
        self.date_picker.setMinimumWidth(150)
        self.date_picker.setFixedHeight(35)
        self.date_picker.dateChanged.connect(
            lambda: self.load_orders(use_filter=True)
        )  # Ensure filter is used on date change
        filter_layout.addWidget(self.date_picker)

        # Button container for centered filter buttons
        filter_button_container = QWidget()
        filter_button_container.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 4px;"
        )
        filter_button_layout = QHBoxLayout(filter_button_container)
        filter_button_layout.setSpacing(0)  # Join buttons
        filter_button_layout.setContentsMargins(0, 0, 0, 0)

        # Filter Buttons
        btn_style_base = "QPushButton {{ color: black; padding: 6px 12px; border: none; border-right: 1px solid #dee2e6; font-size: 13px; {} }}"
        btn_style_radius_left = (
            "border-top-left-radius: 4px; border-bottom-left-radius: 4px;"
        )
        btn_style_radius_right = "border-top-right-radius: 4px; border-bottom-right-radius: 4px; border-right: none;"
        btn_style_hover = "QPushButton:hover {{ background-color: #e9ecef; }}"
        btn_style_pressed = "QPushButton:pressed {{ background-color: #adb5bd; }}"

        completed_btn = QPushButton("Completed (0)")
        completed_btn.clicked.connect(lambda: self.filter_orders("completed"))
        completed_btn.setStyleSheet(
            btn_style_base.format(btn_style_radius_left)
            + btn_style_hover
            + btn_style_pressed
        )
        filter_button_layout.addWidget(completed_btn)
        self.filter_buttons["completed"] = completed_btn

        in_cart_btn = QPushButton("In Cart (0)")
        in_cart_btn.clicked.connect(lambda: self.filter_orders("in-cart"))
        in_cart_btn.setStyleSheet(
            btn_style_base.format("") + btn_style_hover + btn_style_pressed
        )
        filter_button_layout.addWidget(in_cart_btn)
        self.filter_buttons["in-cart"] = in_cart_btn

        settled_btn = QPushButton("Settled (0)")
        settled_btn.clicked.connect(lambda: self.filter_orders("settled"))
        settled_btn.setStyleSheet(
            btn_style_base.format("") + btn_style_hover + btn_style_pressed
        )
        filter_button_layout.addWidget(settled_btn)
        self.filter_buttons["settled"] = settled_btn

        voided_btn = QPushButton("Voided (0)")
        voided_btn.clicked.connect(lambda: self.filter_orders("voided"))
        voided_btn.setStyleSheet(
            btn_style_base.format(btn_style_radius_right)
            + btn_style_hover
            + btn_style_pressed
        )
        filter_button_layout.addWidget(voided_btn)
        self.filter_buttons["voided"] = voided_btn

        filter_layout.addStretch(1)
        filter_layout.addWidget(filter_button_container)
        filter_layout.addStretch(1)

        # Search Bar
        self.search_bar = QLineEdit()  # Make it accessible via self
        self.search_bar.setPlaceholderText("Search Order/Receipt No...")
        self.search_bar.setStyleSheet(
            "QLineEdit { padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: white; }"
        )
        self.search_bar.setFixedWidth(220)
        self.search_bar.setFixedHeight(35)
        # self.search_bar.textChanged.connect(self.filter_table_by_search) # Add search functionality later if needed
        filter_layout.addWidget(self.search_bar)

        main_layout.addWidget(filter_widget)

        # --- Action Buttons Section ---
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(
            0, 5, 0, 5
        )  # Add vertical spacing around actions
        action_layout.setSpacing(8)

        # Button Styles for Actions
        action_btn_style_base = (
            "QPushButton {{ background-color: #007bff; color: white; padding: 4px 8px; "
            "border-radius: 4px; font-size: 12px; border: none; }}"
            "QPushButton:hover {{ background-color: #0056b3; }}"
            "QPushButton:pressed {{ background-color: #004085; }}"
            "QPushButton:disabled {{ background-color: #6c757d; color: #e9ecef; }}"
        )  # Style for disabled state

        # Define a helper to create action buttons
        def create_action_button(text, icon_name, callback):
            button = QPushButton(text)
            icon_path = get_resource_path(f"Resources/Images/{icon_name}.png")
            if os.path.exists(icon_path):  # Only set icon if path is valid
                button.setIcon(load_icon(icon_path))
            else:
                logger.warning(
                    f"Icon file not found, skipping icon for '{text}': {icon_path}"
                )
            button.setStyleSheet(action_btn_style_base)
            button.setFixedHeight(28)
            button.clicked.connect(callback)
            return button

        self.recall_btn = create_action_button(
            " Recall", "recall", self.on_recall_clicked
        )
        self.settle_btn = create_action_button(
            " Settle", "settle", self.on_settle_clicked
        )
        self.void_btn = create_action_button(" Void", "void", self.on_void_clicked)
        self.reprint_btn = create_action_button(
            " Reprint Receipt", "reprint", self.on_reprint_clicked
        )
        self.reprint_btn.setMinimumWidth(110)  # Give reprint more space

        action_layout.addStretch(1)  # Push buttons to the right
        action_layout.addWidget(self.recall_btn)
        action_layout.addWidget(self.settle_btn)
        action_layout.addWidget(self.void_btn)
        action_layout.addWidget(self.reprint_btn)

        # Add separators
        separator1 = QFrame(
            frameShape=QFrame.HLine,
            frameShadow=QFrame.Sunken,
            styleSheet="color: #dee2e6;",
        )
        separator2 = QFrame(
            frameShape=QFrame.HLine,
            frameShadow=QFrame.Sunken,
            styleSheet="color: #dee2e6;",
        )

        main_layout.addWidget(separator1)
        main_layout.addWidget(action_widget)
        main_layout.addWidget(separator2)

        # --- Table Section ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "",  # Checkbox
                "Order/Cart No",
                "Date/Time",
                "Customer ID",
                "Receipt No",
                "Status",
                "Total Amount",
                "Source",  # 'Carts' or 'Orders'
            ]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox column
        header.setSectionResizeMode(4, QHeaderView.Interactive)  # Allow resize Order No
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Total Amount
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Source
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # Select whole row
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table read-only
        self.table.setAlternatingRowColors(True)  # Improve readability
        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #dee2e6;
                gridline-color: #e9ecef; /* Light grid lines */
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f8f9fa; /* Lighter header */
                padding: 6px;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-weight: bold;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e9ecef; /* Row separator */
            }
            QTableWidget::item:selected {
                background-color: #cfe2ff; /* Selection color */
                color: black;
            }
             QTableWidget::item:alternate {
                 background-color: #f8f9fa; /* Alternate row color */
             }
            QCheckBox { margin-left: 6px; } /* Center checkbox slightly */
            """
        )
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setRowCount(0)
        main_layout.addWidget(self.table, stretch=1)  # Give table remaining space

        logger.debug("UI component initialization finished.")

    def load_orders(self, use_filter=True):
        """Load data based on current filter and date."""
        logger.debug(
            f"Loading orders. use_filter={use_filter}, current_filter='{self.current_filter}'"
        )
        date = None
        if use_filter:
            qdate = self.date_picker.date()
            date = qdate.toString("yyyy-MM-dd")  # Match database date format
            logger.debug(f"Using date filter: {date}")
        else:
            logger.debug("Not using date filter (showing all dates).")

        data = []
        try:
            # Determine data source based on filter
            if self.current_filter == "completed":
                # 'completed' view now shows both 'completed' and 'voided' from Orders table
                completed_orders = self.order_model.get_orders_by_status(
                    "completed", date
                )
                voided_orders = self.order_model.get_orders_by_status("voided", date)
                data = completed_orders + voided_orders
                logger.debug(
                    f"Fetched {len(completed_orders)} completed and {len(voided_orders)} voided orders for date {date}."
                )
            elif self.current_filter in ["in-cart", "settled"]:
                # 'in-cart', 'settled' come from Carts table
                data = self.cart_model.get_carts_by_status(self.current_filter, date)
                logger.debug(
                    f"Fetched {len(data)} carts with status '{self.current_filter}' for date {date}."
                )
            elif self.current_filter == "voided":
                # 'voided' now comes from Carts table based on previous discussion?
                # If 'voided' should ONLY show voided ORDERS, change this logic back.
                # Assuming voided carts are shown here:
                data = self.cart_model.get_carts_by_status("voided", date)
                logger.debug(
                    f"Fetched {len(data)} carts with status 'voided' for date {date}."
                )

            else:
                logger.warning(f"Unknown filter '{self.current_filter}' requested.")

            self.set_orders(data)
            self.update_button_counts()  # Update counts after loading data
            self.update_action_buttons()  # Update button states after loading data
            self._update_filter_button_styles()  # Ensure correct filter button is highlighted

        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def filter_orders(self, status):
        """Handle filter button clicks and update display."""
        logger.debug(f"Filter button clicked. Changing filter to: {status}")
        self.current_filter = status
        self._update_filter_button_styles()  # Update style immediately for responsiveness
        self.load_orders(use_filter=True)  # Reload data with the new filter

    def _update_filter_button_styles(self):
        """Internal method to update the visual style of filter buttons."""
        logger.debug(
            f"Updating filter button styles. Active filter: '{self.current_filter}'"
        )

        base_style = "QPushButton {{ color: black; padding: 6px 12px; border: none; border-right: 1px solid #dee2e6; font-size: 13px; background-color: {}; {} }}"
        active_style = "QPushButton {{ color: white; padding: 6px 12px; border: none; border-right: 1px solid #dee2e6; font-size: 13px; background-color: #007bff; {} }}"  # Active color: blue
        hover_style = "QPushButton:hover {{ background-color: #e9ecef; }}"
        active_hover_style = "QPushButton:hover {{ background-color: #0056b3; }}"  # Darker blue on hover when active
        pressed_style = "QPushButton:pressed {{ background-color: #adb5bd; }}"

        radius_left = "border-top-left-radius: 4px; border-bottom-left-radius: 4px;"
        radius_right = "border-top-right-radius: 4px; border-bottom-right-radius: 4px; border-right: none;"  # No right border on last button

        for filter_name, btn in self.filter_buttons.items():
            if btn:  # Check if button exists
                current_radius = ""
                is_active = filter_name == self.current_filter
                style_to_use = active_style if is_active else base_style
                hover_to_use = active_hover_style if is_active else hover_style
                bg_color = "#ffffff"  # Default background for inactive

                if filter_name == "completed":
                    current_radius = radius_left
                elif filter_name == "voided":
                    current_radius = radius_right  # Also remove right border here

                final_style = (
                    style_to_use.format(
                        bg_color if not is_active else "", current_radius
                    )
                    + hover_to_use
                    + pressed_style
                )
                btn.setStyleSheet(final_style)

    def update_button_counts(self):
        """Update the counts displayed on filter buttons for the selected date."""
        qdate = self.date_picker.date()
        date = qdate.toString("yyyy-MM-dd")
        logger.debug(f"Updating button counts for date: {date}")

        try:
            # Get all relevant data for the date to count statuses
            all_carts_today = self.cart_model.get_carts_by_status(date=date)
            all_orders_today = self.order_model.get_orders_by_status(
                date=date
            )  # Get all orders, filter locally

            cart_counts = {"in-cart": 0, "settled": 0, "voided": 0}
            for cart in all_carts_today:
                status = cart.get("status")
                if status in cart_counts:
                    cart_counts[status] += 1

            order_counts = {"completed": 0, "voided": 0}
            for order in all_orders_today:
                status = order.get("status")
                if status == "completed":
                    order_counts["completed"] += 1
                elif status == "voided":
                    order_counts["voided"] += 1

            # The 'Completed' button shows count of 'completed' AND 'voided' orders.
            # The 'Voided' button shows count of 'voided' carts. (Adjust if needed)
            counts = {
                "completed": order_counts["completed"] + order_counts["voided"],
                "in-cart": cart_counts["in-cart"],
                "settled": cart_counts["settled"],
                "voided": cart_counts["voided"],  # Count from carts
            }

            for filter_name, btn in self.filter_buttons.items():
                if btn:  # Check button exists
                    title = filter_name.replace("-", " ").title()
                    count = counts.get(filter_name, 0)
                    btn.setText(f"{title} ({count})")
            logger.debug(f"Button counts updated: {counts}")

        except Exception as e:
            logger.error(f"Error updating button counts: {e}", exc_info=True)

    def update_action_buttons(self):
        """Enable/disable action buttons based on the current filter."""
        logger.debug(
            f"Updating action buttons state for filter: '{self.current_filter}'"
        )

        # Default states (usually disabled)
        enable_recall = False
        enable_settle = False
        enable_void = False
        enable_reprint = False

        if self.current_filter == "in-cart":
            # In Cart: Enable Recall, Settle, and Void
            enable_recall = True
            enable_settle = True
            enable_void = True
            enable_reprint = False  # Cannot reprint from cart
        elif self.current_filter == "completed":
            # Completed (Orders): Enable Void and Reprint
            enable_recall = False
            enable_settle = False
            enable_void = True  # Can void completed/voided orders shown here
            enable_reprint = True  # Can reprint completed/voided orders shown here
        elif self.current_filter == "settled":
            # Settled (Carts): Enable Void, maybe Reprint? (Assuming reprint needs an Order/Receipt)
            enable_recall = False
            enable_settle = False
            enable_void = True  # Can void settled carts
            enable_reprint = (
                False  # Typically cannot reprint from settled cart directly
            )
        elif self.current_filter == "voided":
            # Voided (Carts or Orders depending on load_orders): Disable all actions on already voided items
            enable_recall = False
            enable_settle = False
            enable_void = False
            enable_reprint = False  # Cannot reprint voided

        # Apply states
        if self.recall_btn:
            self.recall_btn.setEnabled(enable_recall)
        if self.settle_btn:
            self.settle_btn.setEnabled(enable_settle)
        if self.void_btn:
            self.void_btn.setEnabled(enable_void)
        if self.reprint_btn:
            self.reprint_btn.setEnabled(enable_reprint)

        # --- Log the final states ---
        logger.debug(
            f"Action button states set: "
            f"Recall={self.recall_btn.isEnabled() if self.recall_btn else 'N/A'}, "
            f"Settle={self.settle_btn.isEnabled() if self.settle_btn else 'N/A'}, "
            f"Void={self.void_btn.isEnabled() if self.void_btn else 'N/A'}, "
            f"Reprint={self.reprint_btn.isEnabled() if self.reprint_btn else 'N/A'}"
        )

    def get_selected_rows(self):
        """Get the indices and data identifiers of rows with selected checkboxes."""
        selected_items = []  # Store tuples of (row_index, order_number, source)
        logger.debug(f"Checking {self.table.rowCount()} rows for selection.")
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            order_num_item = self.table.item(row, 1)  # Get order number item
            source_item = self.table.item(row, 7)  # Get source item

            if not checkbox_widget or not order_num_item or not source_item:
                logger.warning(
                    f"Row {row}: Missing checkbox widget, order number, or source item. Skipping."
                )
                continue  # Skip row if essential components are missing

            layout = checkbox_widget.layout()
            if not layout or layout.count() == 0:
                logger.warning(
                    f"Row {row}: Checkbox widget has no layout or layout is empty. Skipping."
                )
                continue  # Skip if layout is invalid

            widget_item = layout.itemAt(0)
            if not widget_item:
                logger.warning(
                    f"Row {row}: No widget item found at index 0 in layout. Skipping."
                )
                continue  # Skip if item is invalid

            checkbox = widget_item.widget()
            if not isinstance(checkbox, QCheckBox):
                logger.warning(
                    f"Row {row}: Widget in cell (0) is not a QCheckBox, but {type(checkbox)}. Skipping."
                )
                continue  # Skip if it's not a checkbox

            order_number = order_num_item.text()
            source = source_item.text()
            logger.debug(
                f"Row {row}: Checkbox found. Order='{order_number}', Source='{source}', isChecked={checkbox.isChecked()}"
            )
            if checkbox.isChecked():
                logger.debug(f"Row {row} added to selected items.")
                selected_items.append(
                    {"index": row, "order_number": order_number, "source": source}
                )

        logger.debug(f"Selected items identified: {selected_items}")
        return selected_items

    def on_recall_clicked(self):
        """Handle Recall button click."""
        logger.debug("Recall button clicked!")
        selected_items = self.get_selected_rows()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select one or more 'In Cart' items to recall.",
            )
            logger.warning("Recall action aborted: No items selected.")
            return

        if len(selected_items) > 1:
            QMessageBox.warning(
                self,
                "Selection Error",
                "Please select only one 'In Cart' item to recall at a time.",
            )
            logger.warning("Recall action aborted: Multiple items selected.")
            return

        item = selected_items[0]
        order_number = item["order_number"]
        source = item["source"]

        if source == "Carts" and self.current_filter == "in-cart":
            logger.info(f"Opening RecallView for cart: {order_number}")
            try:
                recall_view = RecallView(self.main_window, order_number)
                recall_view.show()
                # Optionally, make it modal if you want to block interaction with OrderSummaryView
                # recall_view.setModal(True)
                # recall_view.exec_()
                self.load_orders(use_filter=True)  # Refresh after closing (if not modal)
            except Exception as e:
                logger.error(f"Error opening RecallView for {order_number}: {e}", exc_info=True)
                QMessageBox.critical(
                    self, "Error", f"Failed to recall cart {order_number}: {e}"
                )
        else:
            logger.warning(
                f"Skipping recall for item {order_number} (Source: {source}, Filter: {self.current_filter}). Recall only valid for 'In Cart' items."
            )
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Recall is only available for 'In Cart' items.",
            )
    def on_settle_clicked(self):
        """Handle Settle button click."""
        logger.debug("Settle button clicked!")  # Log signal reception
        selected_items = self.get_selected_rows()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select one or more 'In Cart' items to settle.",
            )
            logger.warning("Settle action aborted: No items selected.")
            return

        settled_count = 0
        for item in selected_items:
            order_number = item["order_number"]
            source = item["source"]
            # Ensure settle only applies to items from 'Carts' with 'in-cart' status
            if source == "Carts" and self.current_filter == "in-cart":
                logger.info(f"Attempting settlement for cart: {order_number}")
                try:
                    # --- Add your actual settle logic here ---
                    # This might involve:
                    # 1. Showing a payment dialog.
                    # 2. If payment successful:
                    #    a. Update cart status to 'settled' in CartModel.
                    #    b. Potentially create a corresponding 'completed' record in OrderSummaryModel.
                    #    c. Generate a receipt number.
                    success = True  # Placeholder for payment success
                    if success:
                        logger.info(
                            f"Placeholder: Settle logic executed successfully for cart {order_number}"
                        )
                        # Example: self.cart_model.update_cart_status(order_number, 'settled')
                        # Example: receipt_no = self.order_model.create_order_from_cart(order_number)
                        settled_count += 1
                    else:
                        logger.info(
                            f"Placeholder: Settlement cancelled or failed for cart {order_number}"
                        )
                    # ------------------------------------------
                except Exception as e:
                    logger.error(
                        f"Error settling cart {order_number}: {e}", exc_info=True
                    )
                    QMessageBox.critical(
                        self, "Error", f"Failed to settle cart {order_number}: {e}"
                    )
            else:
                logger.warning(
                    f"Skipping settlement for item {order_number} (Source: {source}, Filter: {self.current_filter}). Settle only valid for 'In Cart' items."
                )

        if settled_count > 0:
            QMessageBox.information(
                self, "Settlement", f"Successfully settled {settled_count} item(s)."
            )
            self.load_orders(use_filter=True)  # Refresh list after action

    def on_void_clicked(self):
        """Handle Void button click."""
        logger.debug("Void button clicked!")  # Log signal reception
        selected_items = self.get_selected_rows()
        if not selected_items:
            QMessageBox.warning(
                self, "Selection Required", "Please select one or more items to void."
            )
            logger.warning("Void action aborted: No items selected.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Void",
            f"Are you sure you want to void {len(selected_items)} selected item(s)? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.No:
            logger.info("Void action cancelled by user.")
            return

        voided_count = 0
        for item in selected_items:
            order_number = item["order_number"]
            source = item["source"]  # 'Carts' or 'Orders'
            logger.info(f"Attempting to void item: {order_number} (Source: {source})")

            try:
                # --- Add your actual void logic here ---
                if source == "Carts":
                    # Voiding an item from the Carts table (e.g., 'in-cart' or 'settled')
                    # Example: self.cart_model.update_cart_status(order_number, 'voided')
                    logger.info(
                        f"Placeholder: Void logic executed for cart {order_number}"
                    )
                    voided_count += 1
                elif source == "Orders":
                    # Voiding an item from the Orders table (e.g., 'completed')
                    # Example: self.order_model.update_order_status(order_number, 'voided')
                    logger.info(
                        f"Placeholder: Void logic executed for order {order_number}"
                    )
                    voided_count += 1
                else:
                    logger.warning(
                        f"Unknown source '{source}' for item {order_number}. Cannot void."
                    )
                # ------------------------------------------
            except Exception as e:
                logger.error(
                    f"Error voiding item {order_number} (Source: {source}): {e}",
                    exc_info=True,
                )
                QMessageBox.critical(
                    self, "Error", f"Failed to void item {order_number}: {e}"
                )

        if voided_count > 0:
            QMessageBox.information(
                self, "Void", f"Successfully voided {voided_count} item(s)."
            )
            self.load_orders(use_filter=True)  # Refresh list after action

    def on_reprint_clicked(self):
        """Handle Reprint Receipt button click."""
        logger.debug("Reprint Receipt button clicked!")  # Log signal reception
        selected_items = self.get_selected_rows()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select one or more 'Completed' or 'Settled' items to reprint.",
            )
            logger.warning("Reprint action aborted: No items selected.")
            return

        reprinted_count = 0
        for item in selected_items:
            order_number = item["order_number"]
            source = item["source"]
            # Ensure reprint only applies to items from 'Orders' (completed or already voided)
            # Or potentially 'Settled' carts if they generate a receipt immediately. Adjust logic as needed.
            if source == "Orders":
                logger.info(f"Attempting reprint for order: {order_number}")
                try:
                    # --- Add your actual reprint logic here ---
                    # Example: receipt_data = self.order_model.get_receipt_details(order_number)
                    # Example: self.printer_service.print_receipt(receipt_data)
                    logger.info(
                        f"Placeholder: Reprint logic executed for order {order_number}"
                    )
                    reprinted_count += 1
                    # ------------------------------------------
                except Exception as e:
                    logger.error(
                        f"Error reprinting receipt for order {order_number}: {e}",
                        exc_info=True,
                    )
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to reprint receipt for order {order_number}: {e}",
                    )
            else:
                logger.warning(
                    f"Skipping reprint for item {order_number} (Source: {source}). Reprint only valid for 'Orders'."
                )

        if reprinted_count > 0:
            # No message needed usually, the print job is the confirmation.
            logger.info(f"Processed reprint request for {reprinted_count} item(s).")
            # No need to refresh list for reprint typically

    def set_orders(self, data):
        """Populate the table with comprehensive data from either carts or orders."""
        logger.debug(f"Populating table with {len(data)} items.")
        self.table.setSortingEnabled(False)  # Disable sorting during population
        self.table.setRowCount(0)  # Clear existing rows

        for item in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # logger.debug(f"Adding row {row} with item: {item}") # Can be verbose

            # Checkbox
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, checkbox_widget)

            # Extract data safely using .get()
            is_order = (
                "receipt_no" in item
            )  # Heuristic to determine source if not explicit
            order_number = item.get("order_number") or item.get("order_no", "N/A")
            date_time = item.get("date") or item.get("time", "N/A")
            customer_id = str(item.get("customer_id", "N/A"))
            receipt_no = item.get("receipt_no", "N/A")  # Will be N/A for carts
            status = item.get("status", "Unknown")
            total_amount = item.get("total_amount", 0.0)
            source = "Orders" if is_order else "Carts"

            # Ensure amount is float for formatting
            try:
                total_amount_float = float(total_amount)
            except (ValueError, TypeError):
                total_amount_float = 0.0
                logger.warning(
                    f"Could not convert total_amount '{total_amount}' to float for order {order_number}"
                )

            # Populate cells
            self.table.setItem(row, 1, QTableWidgetItem(str(order_number)))
            self.table.setItem(row, 2, QTableWidgetItem(str(date_time)))
            self.table.setItem(row, 3, QTableWidgetItem(customer_id))
            self.table.setItem(row, 4, QTableWidgetItem(receipt_no))
            self.table.setItem(
                row, 5, QTableWidgetItem(status.title())
            )  # Capitalize status
            # Format amount as currency (adjust locale/format as needed)
            amount_item = QTableWidgetItem(f"{total_amount_float:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 6, amount_item)
            self.table.setItem(row, 7, QTableWidgetItem(source))

        self.table.setSortingEnabled(True)  # Re-enable sorting
        # self.table.resizeColumnsToContents() # Resize columns after populating
        logger.debug(f"Table update complete. Row count: {self.table.rowCount()}")
        # self.table.viewport().update() # Usually not necessary
        # if self.main_window: self.main_window.repaint() # Repainting parent might not be needed

    def go_back(self):
        """Switch back to the dashboard view (if applicable)."""
        logger.debug("Executing go_back method.")
        if hasattr(self.main_window, "stacked_widget"):
            logger.info("Switching main window stacked_widget to index 0.")
            self.main_window.stacked_widget.setCurrentIndex(0)
        else:
            logger.warning(
                "Main window does not have 'stacked_widget'. Cannot go back."
            )

    def closeEvent(self, event):
        """Ensure timer stops when the widget is closed."""
        logger.debug("Close event triggered for OrderSummaryView.")
        if self.timer and self.timer.isActive():
            self.timer.stop()
            logger.info("Auto-refresh timer stopped.")
        super().closeEvent(event)


# --- Main execution block for testing ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create a dummy main window for testing standalone
    # In your real app, you'd pass your actual main window instance
    class DummyMainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Dummy Main Window")
            self.layout = QVBoxLayout(self)
            # Simulate stacked widget if needed for go_back testing
            # self.stacked_widget = QStackedWidget()
            # self.dashboard = QLabel("Dashboard Placeholder")
            # self.stacked_widget.addWidget(self.dashboard)
            # self.layout.addWidget(self.stacked_widget)
            self.resize(1000, 700)

    # Use dummy main window or None if preferred
    # main_win = DummyMainWindow()
    main_win = None  # Set to None if you don't need main_window reference during init

    logger.info("Creating OrderSummaryView instance...")
    view = OrderSummaryView(main_win)

    if main_win:
        # If using dummy main window, add the view to its layout
        # or add it to the dummy stacked_widget
        # main_win.layout.addWidget(view) # Or add to stack index 1
        main_win.setCentralWidget(view)  # Example if main_win was QMainWindow
        main_win.show()
    else:
        # Show the view directly if no main window context is used
        view.setWindowTitle("Order Summary View (Standalone)")
        view.resize(900, 600)
        view.show()

    logger.info("Starting Qt application event loop...")
    sys.exit(app.exec_())
