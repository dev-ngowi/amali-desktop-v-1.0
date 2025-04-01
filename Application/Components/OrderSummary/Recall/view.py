import os
import sys
import logging
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s",
)
logger = logging.getLogger(__name__)


# Resource path and icon loading functions (unchanged)
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
        logger.debug(f"Running in PyInstaller bundle, base path: {base_path}")
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
        logger.debug(f"Running in dev mode, base path: {base_path}")
    full_path = os.path.join(base_path, relative_path)
    logger.debug(f"Resolved path: '{full_path}', Exists: {os.path.exists(full_path)}")
    return full_path


def load_icon(icon_path):
    logger.debug(f"Attempting to load icon from: {icon_path}")
    pixmap = QPixmap(icon_path)
    if pixmap.isNull():
        logger.warning(f"Failed to load icon: {icon_path}")
        return QIcon()
    return QIcon(pixmap)


# Import your actual CartModel
try:
    from Application.Components.OrderSummary.Carts.modal import CartModel
except ImportError:
    logger.error("Failed to import CartModel. Cannot proceed without actual model.")
    raise


class RecallView(QWidget):
    def __init__(self, main_window, order_number):
        super().__init__()
        self.main_window = main_window
        self.order_number = order_number
        self.cart_model = CartModel()
        self.cart_id = None  # Will be set after fetching cart
        self.items = []  # List to hold current items
        self.total_amount = 0.0  # Track total amount for updates

        logger.debug(f"Initializing RecallView for order_number: {order_number}")
        self.init_ui()
        self.load_cart_details()

    def init_ui(self):
        """Set up the RecallView UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title
        title_label = QLabel(f"Recall Order/Cart: {self.order_number}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Items Table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(
            ["Item ID", "Name", "Unit", "Quantity", "Amount"]
        )
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        self.items_table.verticalHeader().hide()
        self.items_table.setEditTriggers(QTableWidget.DoubleClicked)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setStyleSheet(
            """
            QTableWidget {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #dee2e6;
                gridline-color: #e9ecef;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e9ecef;
            }
            QTableWidget::item:selected {
                background-color: #cfe2ff;
                color: black;
            }
            QTableWidget::item:alternate {
                background-color: #f8f9fa;
            }
            """
        )
        self.items_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.items_table.cellChanged.connect(self.on_item_changed)
        main_layout.addWidget(self.items_table, stretch=1)

        # Add Item Section
        add_item_widget = QWidget()
        add_item_layout = QHBoxLayout(add_item_widget)
        add_item_layout.setSpacing(10)

        self.item_id_input = QLineEdit()
        self.item_id_input.setPlaceholderText("Item ID")
        self.item_id_input.setFixedWidth(100)
        add_item_layout.addWidget(self.item_id_input)

        self.item_name_input = QLineEdit()
        self.item_name_input.setPlaceholderText("Item Name")
        self.item_name_input.setFixedWidth(200)
        add_item_layout.addWidget(self.item_name_input)

        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("Unit (e.g., pcs)")
        self.unit_input.setFixedWidth(80)
        add_item_layout.addWidget(self.unit_input)

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantity")
        self.quantity_input.setFixedWidth(80)
        add_item_layout.addWidget(self.quantity_input)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        self.amount_input.setFixedWidth(80)
        add_item_layout.addWidget(self.amount_input)

        add_btn = QPushButton("Add Item")
        add_btn.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; padding: 4px 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #218838; }"
            "QPushButton:pressed { background-color: #1e7e34; }"
        )
        add_btn.clicked.connect(self.add_item)
        add_item_layout.addWidget(add_btn)

        add_item_layout.addStretch(1)
        main_layout.addWidget(add_item_widget)

        # Action Buttons
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setSpacing(10)

        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #007bff; color: white; padding: 4px 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #0056b3; }"
            "QPushButton:pressed { background-color: #004085; }"
        )
        save_btn.clicked.connect(self.save_changes)
        action_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #6c757d; color: white; padding: 4px 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #5a6268; }"
            "QPushButton:pressed { background-color: #545b62; }"
        )
        cancel_btn.clicked.connect(self.close)
        action_layout.addWidget(cancel_btn)

        settle_btn = QPushButton("Settle Now")
        settle_btn.setStyleSheet(
            "QPushButton { background-color: #ffc107; color: black; padding: 4px 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #e0a800; }"
            "QPushButton:pressed { background-color: #d39e00; }"
        )
        settle_btn.clicked.connect(self.settle_now)
        action_layout.addWidget(settle_btn)

        action_layout.addStretch(1)
        main_layout.addWidget(action_widget)

    def load_cart_details(self):
        """Load the cart details into the table."""
        try:
            carts = self.cart_model.get_carts_by_status(status="in-cart")
            cart = next(
                (c for c in carts if c["order_number"] == self.order_number), None
            )
            if not cart:
                raise ValueError(
                    f"No 'in-cart' cart found with order_number {self.order_number}"
                )

            self.cart_id = cart["cart_id"]
            self.total_amount = cart["total_amount"]

            cart_data = self.cart_model.get_cart(self.cart_id)
            if not cart_data:
                raise ValueError(f"Cart ID {self.cart_id} not found")

            self.items = cart_data["items"]
            logger.debug(
                f"Loaded cart {self.order_number} (ID: {self.cart_id}) with items: {self.items}"
            )
            self.populate_table()
        except Exception as e:
            logger.error(f"Error loading cart details for {self.order_number}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load cart details: {e}")
            self.close()

    def populate_table(self):
        """Populate the items table with current items."""
        self.items_table.setRowCount(0)
        for item in self.items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QTableWidgetItem(str(item["item_id"])))
            self.items_table.setItem(row, 1, QTableWidgetItem(item["name"]))
            self.items_table.setItem(row, 2, QTableWidgetItem(item["unit"]))
            qty_item = QTableWidgetItem(str(item["quantity"]))
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 3, qty_item)
            amount_item = QTableWidgetItem(f"{item['amount']:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 4, amount_item)

    def on_item_changed(self, row, column):
        """Handle changes in the table (e.g., quantity updates)."""
        logger.debug(f"Cell changed at row {row}, column {column}")
        if column == 3:  # Quantity column
            qty_item = self.items_table.item(row, 3)
            amount_item = self.items_table.item(row, 4)
            if not qty_item:
                logger.warning(f"Row {row} has no quantity item.")
                return

            if not amount_item:
                logger.warning(f"Row {row} has no amount item.")
                return

            try:
                qty = int(qty_item.text())
                amount = float(amount_item.text())
                self.items[row]["quantity"] = qty
                self.recalculate_total()
                logger.debug(f"Updated item at row {row}: {self.items[row]}")
            except ValueError as e:
                logger.warning(f"Invalid input at row {row}, column {column}: {e}")
                QMessageBox.warning(
                    self, "Invalid Input", "Please enter a valid integer for quantity."
                )
            except Exception as e:
                logger.error(f"Error processing item change at row {row}: {e}")

    def recalculate_total(self):
        """Recalculate the total_amount based on current items."""
        self.total_amount = sum(item["amount"] for item in self.items)
        logger.debug(f"Recalculated total_amount: {self.total_amount}")

    def add_item(self):
        """Add a new item to the cart."""
        try:
            item_id = int(self.item_id_input.text())
            name = self.item_name_input.text().strip()
            unit = self.unit_input.text().strip()
            quantity = int(self.quantity_input.text())
            amount = float(self.amount_input.text())

            if not name or not unit:
                raise ValueError("Item name and unit cannot be empty.")

            new_item = {
                "item_id": item_id,
                "name": name,
                "unit": unit,
                "quantity": quantity,
                "amount": amount,
            }
            self.items.append(new_item)
            self.recalculate_total()
            self.populate_table()
            self.clear_inputs()
            logger.debug(f"Added new item: {new_item}")
        except ValueError as e:
            logger.warning(f"Error adding item: {e}")
            QMessageBox.warning(self, "Invalid Input", f"Failed to add item: {e}")

    def clear_inputs(self):
        """Clear the add item input fields."""
        self.item_id_input.clear()
        self.item_name_input.clear()
        self.unit_input.clear()
        self.quantity_input.clear()
        self.amount_input.clear()

    def save_changes(self):
        """Save the updated cart items."""
        if not self.cart_id:
            QMessageBox.critical(self, "Error", "Cannot save: Cart ID not set.")
            return

        cart_data = {"total_amount": self.total_amount, "items": self.items}
        try:
            result = self.cart_model.update_cart(self.cart_id, cart_data)
            if result["success"]:
                QMessageBox.information(self, "Success", "Cart updated successfully.")
                self.close()
                if hasattr(self.main_window, "refresh_order_summary"):
                    self.main_window.refresh_order_summary()
            else:
                raise Exception(result["message"])
        except Exception as e:
            logger.error(f"Error saving cart changes: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save changes: {e}")

    def settle_now(self):
        """Save changes and trigger settlement."""
        if not self.cart_id:
            QMessageBox.critical(self, "Error", "Cannot settle: Cart ID not set.")
            return

        cart_data = {
            "total_amount": self.total_amount,
            "items": self.items,
            "status": "settled",  # Update status to settled
        }
        try:
            result = self.cart_model.update_cart(self.cart_id, cart_data)
            if result["success"]:
                logger.info(f"Cart {self.order_number} saved and marked as settled")
                QMessageBox.information(
                    self, "Success", "Cart saved and settlement initiated."
                )
                self.close()
                if hasattr(self.main_window, "settle_cart"):
                    self.main_window.settle_cart(self.order_number)
            else:
                raise Exception(result["message"])
        except Exception as e:
            logger.error(f"Error during settle now: {e}")
            QMessageBox.critical(self, "Error", f"Failed to settle cart: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = RecallView(None, "C1001")  # Test with a sample order number
    view.setWindowTitle("Recall View (Standalone)")
    view.resize(800, 600)
    view.show()
    sys.exit(app.exec_())
