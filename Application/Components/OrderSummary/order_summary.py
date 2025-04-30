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
    QDialog,
    QLabel,
    QScrollArea,
)
from PyQt5.QtCore import QDate, Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap

from Application.Components.OrderSummary.Recall.view import RecallView


# --- Mock Models for Standalone Running ---
class MockCartModel:
    def get_carts_by_status(self, status=None, date=None):
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
            },
            {
                "order_number": "C1005",
                "time": "2025-03-31 11:05:00",
                "customer_id": 4,
                "status": "voided",
                "total_amount": 30.0,
            },
        ]
        filtered_data = []
        target_date_str = date
        for item in all_data:
            item_date_str = item["time"].split(" ")[0]
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
            },
            {
                "order_no": "O2004",
                "date": "2025-03-31",
                "receipt_no": "R5004",
                "status": "completed",
                "total_amount": 95.0,
            },
        ]
        filtered_data = []
        target_date_str = date
        for item in all_data:
            item_date_str = item["date"]
            date_match = (date is None) or (item_date_str == target_date_str)
            status_match = (status is None) or (item["status"] == status)
            if date_match and status_match:
                if status == "completed" and item["status"] in ["completed", "voided"]:
                    filtered_data.append(item)
                elif item["status"] == status:
                    filtered_data.append(item)
        logger.debug(
            f"[MockOrderModel] get_orders_by_status(status={status}, date={date}) -> returning {len(filtered_data)} items"
        )
        return filtered_data

    def get_order_details(self, order_number):
        # Mock detailed data for demonstration
        mock_details = {
            "O2001": {
                "order_number": "O2001",
                "receipt_number": "R5001",
                "date": "2025-03-31",
                "status": "completed",
                "total_amount": 150.0,
                "items": [
                    {"name": "Item A", "quantity": 2, "price": 50.0},
                    {"name": "Item B", "quantity": 1, "price": 50.0},
                ],
            },
            "O2002": {
                "order_number": "O2002",
                "receipt_number": "R5002",
                "date": "2025-03-31",
                "status": "voided",
                "total_amount": 80.0,
                "items": [
                    {"name": "Item C", "quantity": 1, "price": 80.0},
                ],
            },
            "O2003": {
                "order_number": "O2003",
                "receipt_number": "R5003",
                "date": "2025-03-30",
                "status": "completed",
                "total_amount": 200.0,
                "items": [
                    {"name": "Item D", "quantity": 4, "price": 50.0},
                ],
            },
            "O2004": {
                "order_number": "O2004",
                "receipt_number": "R5004",
                "date": "2025-03-31",
                "status": "completed",
                "total_amount": 95.0,
                "items": [
                    {"name": "Item E", "quantity": 1, "price": 95.0},
                ],
            },
        }
        details = mock_details.get(order_number)
        logger.debug(f"[MockOrderModel] get_order_details({order_number}) -> {details}")
        return details


try:
    from Application.Components.OrderSummary.Carts.modal import CartModel
    from Application.Components.OrderSummary.modal import OrderSummaryModel
except ImportError:
    logging.Logger.warning(
        "Could not import actual models. Using Mock Models for demonstration."
    )
    CartModel = MockCartModel
    OrderSummaryModel = MockOrderSummaryModel


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_icon(icon_path):
    logger.debug(f"Attempting to load icon from: {icon_path}")
    pixmap = QPixmap(icon_path)
    if pixmap.isNull():
        logger.warning(f"Failed to load icon: {icon_path}. Pixmap is null.")
        return QIcon()
    logger.debug(f"Icon loaded successfully: {icon_path}")
    return QIcon(pixmap)


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
        logger.debug(f"Running in PyInstaller bundle, base path: {base_path}")
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
        logger.debug(f"Running in dev mode, base path: {base_path}")
    full_path = os.path.join(base_path, relative_path)
    logger.debug(
        f"Resolved path for '{relative_path}': '{full_path}', Exists: {os.path.exists(full_path)}"
    )
    if not os.path.exists(full_path):
        logger.error(f"Resource path does not exist: {full_path}")
    return full_path


# Custom Dialog for Order Preview
class OrderPreviewDialog(QDialog):
    def __init__(self, order_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Order Preview - {order_data['order_number']}")
        self.setMinimumSize(600, 400)
        self.init_ui(order_data)

    def init_ui(self, order_data):
        layout = QVBoxLayout(self)

        # Order Details Section
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.addWidget(QLabel(f"Order Number: {order_data['order_number']}"))
        details_layout.addWidget(
            QLabel(f"Receipt Number: {order_data['receipt_number']}")
        )
        details_layout.addWidget(QLabel(f"Date: {order_data['date']}"))
        details_layout.addWidget(QLabel(f"Status: {order_data['status']}"))
        details_layout.addWidget(
            QLabel(f"Total Amount: TZS {order_data['total_amount']:.2f}")
        )
        details_widget.setStyleSheet("QLabel { font-size: 14px; padding: 5px; }")
        layout.addWidget(details_widget)

        # Order Items Section
        items_label = QLabel("Order Items:")
        items_label.setStyleSheet(
            "font-weight: bold; font-size: 16px; padding: 10px 0;"
        )
        layout.addWidget(items_label)

        items_table = QTableWidget()
        items_table.setColumnCount(4)
        items_table.setHorizontalHeaderLabels(
            ["Item Name", "Quantity", "Price", "Total"]
        )
        items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        items_table.setRowCount(len(order_data["items"]))
        items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        items_table.setAlternatingRowColors(True)
        items_table.setStyleSheet(
            """
            QTableWidget { background-color: white; border: 1px solid #dee2e6; }
            QHeaderView::section { background-color: #f8f9fa; padding: 4px; }
            QTableWidget::item { padding: 4px; }
            """
        )

        for row, item in enumerate(order_data["items"]):
            item_name = QTableWidgetItem(item["name"])
            quantity = QTableWidgetItem(str(item["quantity"]))
            price = QTableWidgetItem(f"TZS {item['price']:.2f}")
            total = QTableWidgetItem(f"TZS {item['quantity'] * item['price']:.2f}")
            quantity.setTextAlignment(Qt.AlignCenter)
            price.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            items_table.setItem(row, 0, item_name)
            items_table.setItem(row, 1, quantity)
            items_table.setItem(row, 2, price)
            items_table.setItem(row, 3, total)

        scroll_area = QScrollArea()
        scroll_area.setWidget(items_table)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area, stretch=1)

        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #dc3545; color: white; padding: 5px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #c82333; }"
        )
        close_btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)


class OrderSummaryView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window if main_window else QWidget()
        self.cart_model = CartModel()
        self.order_model = OrderSummaryModel()
        self.current_filter = "completed"
        self.filter_buttons = {
            "completed": None,
            "in-cart": None,
            "settled": None,
            "voided": None,
        }
        self.recall_btn = None
        self.settle_btn = None
        self.void_btn = None
        self.preview_btn = None
        self.reprint_btn = None
        self.timer = None

        logger.debug("OrderSummaryView initializing...")
        self.init_ui()
        logger.debug("UI Initialized. Loading initial orders...")
        self.load_orders(use_filter=True)
        self.start_auto_refresh()
        logger.debug("OrderSummaryView initialization complete.")

    def start_auto_refresh(self):
        if self.timer is None:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.auto_refresh_orders)
            self.refresh_interval = 2 * 60 * 1000
            self.timer.start(self.refresh_interval)
            logger.debug(
                f"Auto-refresh timer started with interval: {self.refresh_interval} ms"
            )

    def auto_refresh_orders(self):
        logger.debug("Auto-refresh triggered.")
        self.load_orders(use_filter=True)

    def init_ui(self):
        logger.debug("Initializing UI components")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Filter and Search Section
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(10)

        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy-MM-dd")
        self.date_picker.setStyleSheet(
            "QDateEdit { padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: white; }"
            "QDateEdit::drop-down { border: none; }"
            "QCalendarWidget QToolButton { color: black; }"
        )
        self.date_picker.setMinimumWidth(150)
        self.date_picker.setFixedHeight(35)
        self.date_picker.dateChanged.connect(lambda: self.load_orders(use_filter=True))
        filter_layout.addWidget(self.date_picker)

        filter_button_container = QWidget()
        filter_button_container.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 4px;"
        )
        filter_button_layout = QHBoxLayout(filter_button_container)
        filter_button_layout.setSpacing(0)
        filter_button_layout.setContentsMargins(0, 0, 0, 0)

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

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Order/Receipt No...")
        self.search_bar.setStyleSheet(
            "QLineEdit { padding: 8px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; background-color: white; }"
        )
        self.search_bar.setFixedWidth(220)
        self.search_bar.setFixedHeight(35)
        filter_layout.addWidget(self.search_bar)

        main_layout.addWidget(filter_widget)

        # Action Buttons Section
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 5, 0, 5)
        action_layout.setSpacing(8)

        action_btn_style_base = (
            "QPushButton {{ background-color: #007bff; color: white; padding: 4px 8px; "
            "border-radius: 4px; font-size: 12px; border: none; }}"
            "QPushButton:hover {{ background-color: #0056b3; }}"
            "QPushButton:pressed {{ background-color: #004085; }}"
            "QPushButton:disabled {{ background-color: #6c757d; color: #e9ecef; }}"
        )

        def create_action_button(text, icon_name, callback):
            button = QPushButton(text)
            icon_path = get_resource_path(f"Resources/Images/{icon_name}.png")
            if os.path.exists(icon_path):
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
        self.preview_btn = create_action_button(
            " Preview", "preview", self.on_preview_clicked
        )
        self.reprint_btn = create_action_button(
            " Reprint Receipt", "reprint", self.on_reprint_clicked
        )
        self.reprint_btn.setMinimumWidth(110)

        action_layout.addStretch(1)
        action_layout.addWidget(self.recall_btn)
        action_layout.addWidget(self.settle_btn)
        action_layout.addWidget(self.void_btn)
        action_layout.addWidget(self.preview_btn)
        action_layout.addWidget(self.reprint_btn)

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

        # Table Section
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "",
                "Order/Cart No",
                "Date/Time",
                "Customer ID",
                "Receipt No",
                "Status",
                "Total Amount",
                "Source",
            ]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            """
            QTableWidget { background-color: white; border-radius: 5px; border: 1px solid #dee2e6; gridline-color: #e9ecef; font-size: 13px; }
            QHeaderView::section { background-color: #f8f9fa; padding: 6px; border: none; border-bottom: 1px solid #dee2e6; font-weight: bold; font-size: 13px; }
            QTableWidget::item { padding: 6px; border-bottom: 1px solid #e9ecef; }
            QTableWidget::item:selected { background-color: #cfe2ff; color: black; }
            QTableWidget::item:alternate { background-color: #f8f9fa; }
            QCheckBox { margin-left: 6px; }
            """
        )
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setRowCount(0)
        main_layout.addWidget(self.table, stretch=1)

        logger.debug("UI component initialization finished.")

    def load_orders(self, use_filter=True):
        logger.debug(
            f"Loading orders. use_filter={use_filter}, current_filter='{self.current_filter}'"
        )
        date = self.date_picker.date().toString("yyyy-MM-dd") if use_filter else None

        data = []
        try:
            if self.current_filter == "completed":
                completed_orders = self.order_model.get_orders_by_status(
                    "completed", date
                )
                voided_orders = self.order_model.get_orders_by_status("voided", date)
                data = completed_orders + voided_orders
                
            elif self.current_filter in ["in-cart", "settled", "voided"]:
                data = self.cart_model.get_carts_by_status(self.current_filter, date)
            self.set_orders(data)
            self.update_button_counts()
            self.update_action_buttons()
            self._update_filter_button_styles()
        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def filter_orders(self, status):
        logger.debug(f"Filter button clicked. Changing filter to: {status}")
        self.current_filter = status
        self._update_filter_button_styles()
        self.load_orders(use_filter=True)

    def _update_filter_button_styles(self):
        logger.debug(
            f"Updating filter button styles. Active filter: '{self.current_filter}'"
        )
        base_style = "QPushButton {{ color: black; padding: 6px 12px; border: none; border-right: 1px solid #dee2e6; font-size: 13px; background-color: {}; {} }}"
        active_style = "QPushButton {{ color: white; padding: 6px 12px; border: none; border-right: 1px solid #dee2e6; font-size: 13px; background-color: #007bff; {} }}"
        hover_style = "QPushButton:hover {{ background-color: #e9ecef; }}"
        active_hover_style = "QPushButton:hover {{ background-color: #0056b3; }}"
        pressed_style = "QPushButton:pressed {{ background-color: #adb5bd; }}"

        radius_left = "border-top-left-radius: 4px; border-bottom-left-radius: 4px;"
        radius_right = "border-top-right-radius: 4px; border-bottom-right-radius: 4px; border-right: none;"

        for filter_name, btn in self.filter_buttons.items():
            if btn:
                current_radius = (
                    radius_left
                    if filter_name == "completed"
                    else (radius_right if filter_name == "voided" else "")
                )
                is_active = filter_name == self.current_filter
                style_to_use = active_style if is_active else base_style
                hover_to_use = active_hover_style if is_active else hover_style
                bg_color = "#ffffff" if not is_active else ""
                btn.setStyleSheet(
                    style_to_use.format(bg_color, current_radius)
                    + hover_to_use
                    + pressed_style
                )

    def update_button_counts(self):
        qdate = self.date_picker.date()
        date = qdate.toString("yyyy-MM-dd")
        logger.debug(f"Updating button counts for date: {date}")

        try:
            all_carts_today = self.cart_model.get_carts_by_status(date=date)
            all_orders_today = self.order_model.get_orders_by_status(date=date)

            cart_counts = {"in-cart": 0, "settled": 0, "voided": 0}
            for cart in all_carts_today:
                if cart.get("status") in cart_counts:
                    cart_counts[cart["status"]] += 1

            order_counts = {"completed": 0, "voided": 0}
            for order in all_orders_today:
                status = order.get("status")
                if status == "completed":
                    order_counts["completed"] += 1
                elif status == "voided":
                    order_counts["voided"] += 1

            counts = {
                "completed": order_counts["completed"] + order_counts["voided"],
                "in-cart": cart_counts["in-cart"],
                "settled": cart_counts["settled"],
                "voided": cart_counts["voided"],
            }

            for filter_name, btn in self.filter_buttons.items():
                if btn:
                    title = filter_name.replace("-", " ").title()
                    count = counts.get(filter_name, 0)
                    btn.setText(f"{title} ({count})")
            logger.debug(f"Button counts updated: {counts}")
        except Exception as e:
            logger.error(f"Error updating button counts: {e}", exc_info=True)

    def update_action_buttons(self):
        logger.debug(
            f"Updating action buttons state for filter: '{self.current_filter}'"
        )
        enable_recall = enable_settle = enable_void = enable_preview = (
            enable_reprint
        ) = False

        if self.current_filter == "in-cart":
            enable_recall = enable_settle = enable_void = True
        elif self.current_filter == "completed":
            enable_void = enable_preview = enable_reprint = True
        elif self.current_filter == "settled":
            enable_void = True
        elif self.current_filter == "voided":
            pass

        if self.recall_btn:
            self.recall_btn.setEnabled(enable_recall)
        if self.settle_btn:
            self.settle_btn.setEnabled(enable_settle)
        if self.void_btn:
            self.void_btn.setEnabled(enable_void)
        if self.preview_btn:
            self.preview_btn.setEnabled(enable_preview)
        if self.reprint_btn:
            self.reprint_btn.setEnabled(enable_reprint)

        logger.debug(
            f"Action button states set: "
            f"Recall={self.recall_btn.isEnabled() if self.recall_btn else 'N/A'}, "
            f"Settle={self.settle_btn.isEnabled() if self.settle_btn else 'N/A'}, "
            f"Void={self.void_btn.isEnabled() if self.void_btn else 'N/A'}, "
            f"Preview={self.preview_btn.isEnabled() if self.preview_btn else 'N/A'}, "
            f"Reprint={self.reprint_btn.isEnabled() if self.reprint_btn else 'N/A'}"
        )

    def get_selected_rows(self):
        selected_items = []
        logger.debug(f"Checking {self.table.rowCount()} rows for selection.")
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            order_num_item = self.table.item(row, 1)
            source_item = self.table.item(row, 7)
            if checkbox_widget and order_num_item and source_item:
                layout = checkbox_widget.layout()
                if layout and layout.count():
                    checkbox = layout.itemAt(0).widget()
                    if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                        selected_items.append(
                            {
                                "index": row,
                                "order_number": order_num_item.text(),
                                "source": source_item.text(),
                            }
                        )
        logger.debug(f"Selected items identified: {selected_items}")
        return selected_items

    def on_recall_clicked(self):
        logger.debug("Recall button clicked!")
        selected_items = self.get_selected_rows()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select one or more 'In Cart' items to recall.",
            )
            return
        if len(selected_items) > 1:
            QMessageBox.warning(
                self,
                "Selection Error",
                "Please select only one 'In Cart' item to recall at a time.",
            )
            return
        item = selected_items[0]
        if item["source"] == "Carts" and self.current_filter == "in-cart":
            try:
                recall_view = RecallView(self.main_window, item["order_number"])
                recall_view.show()
                self.load_orders(use_filter=True)
            except Exception as e:
                logger.error(
                    f"Error opening RecallView for {item['order_number']}: {e}",
                    exc_info=True,
                )
                QMessageBox.critical(
                    self, "Error", f"Failed to recall cart {item['order_number']}: {e}"
                )
        else:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Recall is only available for 'In Cart' items.",
            )

    def on_settle_clicked(self):
        logger.debug("Settle button clicked!")
        selected_items = self.get_selected_rows()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select one or more 'In Cart' items to settle.",
            )
            return
        settled_count = 0
        for item in selected_items:
            if item["source"] == "Carts" and self.current_filter == "in-cart":
                try:
                    success = True  # Placeholder for actual settle logic
                    if success:
                        settled_count += 1
                except Exception as e:
                    logger.error(
                        f"Error settling cart {item['order_number']}: {e}",
                        exc_info=True,
                    )
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to settle cart {item['order_number']}: {e}",
                    )
        if settled_count > 0:
            QMessageBox.information(
                self, "Settlement", f"Successfully settled {settled_count} item(s)."
            )
            self.load_orders(use_filter=True)

    def on_void_clicked(self):
        logger.debug("Void button clicked!")
        selected_items = self.get_selected_rows()
        if not selected_items:
            QMessageBox.warning(
                self, "Selection Required", "Please select one or more items to void."
            )
            return
        confirm = QMessageBox.question(
            self,
            "Confirm Void",
            f"Are you sure you want to void {len(selected_items)} selected item(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.No:
            return
        voided_count = 0
        for item in selected_items:
            try:
                if item["source"] in ["Carts", "Orders"]:
                    voided_count += 1  # Placeholder for actual void logic
            except Exception as e:
                logger.error(
                    f"Error voiding item {item['order_number']}: {e}", exc_info=True
                )
                QMessageBox.critical(
                    self, "Error", f"Failed to void item {item['order_number']}: {e}"
                )
        if voided_count > 0:
            QMessageBox.information(
                self, "Void", f"Successfully voided {voided_count} item(s)."
            )
            self.load_orders(use_filter=True)

    def on_preview_clicked(self):
        logger.debug("Preview button clicked!")
        selected_items = self.get_selected_rows()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select one or more 'Completed' items to preview.",
            )
            return
        previewed_count = 0
        for item in selected_items:
            if item["source"] == "Orders" and self.current_filter == "completed":
                order_number = item["order_number"]
                logger.info(f"Attempting preview for order: {order_number}")
                try:
                    # Fetch detailed order data from the model
                    order_details = self.order_model.get_order_details(order_number)
                    if not order_details:
                        logger.warning(
                            f"No detailed data found for order {order_number}"
                        )
                        QMessageBox.warning(
                            self,
                            "No Data",
                            f"No detailed information available for order {order_number}.",
                        )
                        continue

                    # Open the custom preview dialog
                    preview_dialog = OrderPreviewDialog(order_details, self)
                    preview_dialog.exec_()
                    logger.info(f"Preview displayed for order {order_number}")
                    previewed_count += 1
                except Exception as e:
                    logger.error(
                        f"Error previewing order {order_number}: {e}", exc_info=True
                    )
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to preview order {order_number}: {e}",
                    )
            else:
                logger.warning(
                    f"Skipping preview for {item['order_number']} - not a 'Completed' order"
                )
        if previewed_count > 0:
            logger.info(f"Processed preview request for {previewed_count} item(s).")

    def on_reprint_clicked(self):
        logger.debug("Reprint Receipt button clicked!")
        selected_items = self.get_selected_rows()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select one or more 'Completed' or 'Settled' items to reprint.",
            )
            return
        reprinted_count = 0
        for item in selected_items:
            if item["source"] == "Orders":
                try:
                    reprinted_count += 1  # Placeholder for actual reprint logic
                except Exception as e:
                    logger.error(
                        f"Error reprinting receipt for order {item['order_number']}: {e}",
                        exc_info=True,
                    )
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to reprint receipt for order {item['order_number']}: {e}",
                    )
        if reprinted_count > 0:
            logger.info(f"Processed reprint request for {reprinted_count} item(s).")

    def set_orders(self, data):
        logger.debug(f"Populating table with {len(data)} items.")
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for item in data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, checkbox_widget)

            is_order = "receipt_no" in item
            order_number = item.get("order_number") or item.get("order_no", "N/A")
            date_time = item.get("date") or item.get("time", "N/A")
            customer_id = str(item.get("customer_id", "N/A"))
            receipt_no = item.get("receipt_no", "N/A")
            status = item.get("status", "Unknown")
            total_amount = float(item.get("total_amount", 0.0))
            source = "Orders" if is_order else "Carts"

            self.table.setItem(row, 1, QTableWidgetItem(str(order_number)))
            self.table.setItem(row, 2, QTableWidgetItem(str(date_time)))
            self.table.setItem(row, 3, QTableWidgetItem(customer_id))
            self.table.setItem(row, 4, QTableWidgetItem(receipt_no))
            self.table.setItem(row, 5, QTableWidgetItem(status.title()))
            amount_item = QTableWidgetItem(f"{total_amount:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 6, amount_item)
            self.table.setItem(row, 7, QTableWidgetItem(source))

        self.table.setSortingEnabled(True)
        logger.debug(f"Table update complete. Row count: {self.table.rowCount()}")

    def go_back(self):
        logger.debug("Executing go_back method.")
        if hasattr(self.main_window, "stacked_widget"):
            self.main_window.stacked_widget.setCurrentIndex(0)
        else:
            logger.warning(
                "Main window does not have 'stacked_widget'. Cannot go back."
            )

    def closeEvent(self, event):
        logger.debug("Close event triggered for OrderSummaryView.")
        if self.timer and self.timer.isActive():
            self.timer.stop()
            logger.info("Auto-refresh timer stopped.")
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    class DummyMainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Dummy Main Window")
            self.layout = QVBoxLayout(self)
            self.resize(1000, 700)

    main_win = None
    logger.info("Creating OrderSummaryView instance...")
    view = OrderSummaryView(main_win)

    if main_win:
        main_win.setCentralWidget(view)
        main_win.show()
    else:
        view.setWindowTitle("Order Summary View (Standalone)")
        view.resize(900, 600)
        view.show()

    logger.info("Starting Qt application event loop...")
    sys.exit(app.exec_())
