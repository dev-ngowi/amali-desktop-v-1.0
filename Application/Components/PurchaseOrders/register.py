import sys
import random
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logging

from Application.Components.PurchaseOrders.model import PurchaseOrderManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AddPurchaseOrderWindow(QDialog):
    po_added = pyqtSignal()

    def __init__(self, po_manager, parent=None):
        super().__init__(parent)
        self.po_manager = po_manager
        self.setWindowTitle("Add New Purchase Order")
        self.setMinimumSize(600, 500)
        self.items = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        form_widget = QWidget()
        grid_layout = QGridLayout()
        row = 0

        self.order_number_input = QLineEdit()
        self.order_number_input.setReadOnly(True)
        self.order_number_input.setText(self.generate_order_number())

        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.supplier_combo.setInsertPolicy(QComboBox.NoInsert)
        self.supplier_model = QStandardItemModel()
        self.supplier_filter = QSortFilterProxyModel()
        self.supplier_filter.setSourceModel(self.supplier_model)
        self.supplier_filter.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.supplier_combo.setModel(self.supplier_filter)
        self.supplier_combo.lineEdit().textEdited.connect(
            self.supplier_filter.setFilterFixedString
        )

        self.order_date_input = QLineEdit()
        self.order_date_input.setPlaceholderText("YYYY-MM-DD")

        self.expected_delivery_input = QLineEdit()
        self.expected_delivery_input.setPlaceholderText("YYYY-MM-DD")

        self.currency_combo = QComboBox()
        self.currency_combo.setEditable(True)
        self.currency_combo.setInsertPolicy(QComboBox.NoInsert)
        self.currency_model = QStandardItemModel()
        self.currency_filter = QSortFilterProxyModel()
        self.currency_filter.setSourceModel(self.currency_model)
        self.currency_filter.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.currency_combo.setModel(self.currency_filter)
        self.currency_combo.lineEdit().textEdited.connect(
            self.currency_filter.setFilterFixedString
        )

        self.notes_input = QTextEdit()

        grid_layout.addWidget(QLabel("Order Number *"), row, 0)
        grid_layout.addWidget(self.order_number_input, row, 1)
        row += 1
        grid_layout.addWidget(QLabel("Supplier *"), row, 0)
        grid_layout.addWidget(self.supplier_combo, row, 1)
        row += 1
        grid_layout.addWidget(QLabel("Order Date *"), row, 0)
        grid_layout.addWidget(self.order_date_input, row, 1)
        row += 1
        grid_layout.addWidget(QLabel("Expected Delivery"), row, 0)
        grid_layout.addWidget(self.expected_delivery_input, row, 1)
        row += 1
        grid_layout.addWidget(QLabel("Currency *"), row, 0)
        grid_layout.addWidget(self.currency_combo, row, 1)
        row += 1
        grid_layout.addWidget(QLabel("Notes"), row, 0)
        grid_layout.addWidget(self.notes_input, row, 1)

        form_widget.setLayout(grid_layout)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(
            ["Item", "Unit", "Quantity", "Unit Price", "Discount", "Total"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.itemChanged.connect(
            self.update_total
        )  # Connect to update totals
        add_item_btn = QPushButton("Add Item")
        add_item_btn.clicked.connect(self.add_item_row)

        self.total_label = QLabel("Total Amount: 0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_purchase_order)
        save_layout.addWidget(save_btn)

        main_layout.addWidget(form_widget)
        main_layout.addWidget(QLabel("Items *"))
        main_layout.addWidget(self.items_table)
        main_layout.addWidget(add_item_btn)
        main_layout.addWidget(self.total_label)
        main_layout.addStretch()
        main_layout.addLayout(save_layout)
        self.setLayout(main_layout)

        self.load_combo_data()

    def generate_order_number(self):
        random_digits = "".join([str(random.randint(0, 9)) for _ in range(4)])
        return f"PO{random_digits}"

    def load_combo_data(self):
        try:
            suppliers = self.po_manager.get_suppliers()
            self.supplier_model.clear()
            self.supplier_model.appendRow(QStandardItem("Select Supplier"))
            self.supplier_combo.setItemData(0, -1, Qt.UserRole)
            for supplier in suppliers:
                item = QStandardItem(supplier["name"])
                item.setData(supplier["id"], Qt.UserRole)
                self.supplier_model.appendRow(item)
            self.supplier_combo.setCurrentIndex(0)

            currencies = ["USD", "TZS", "KES", "CNY", "AED"]
            self.currency_model.clear()
            for currency in currencies:
                item = QStandardItem(currency)
                self.currency_model.appendRow(item)
            self.currency_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Failed to load combo data: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load data: {str(e)}")

    def add_item_row(self):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        item_combo = QComboBox()
        item_combo.setEditable(True)
        item_combo.setInsertPolicy(QComboBox.NoInsert)
        item_model = QStandardItemModel()
        item_filter = QSortFilterProxyModel()
        item_filter.setSourceModel(item_model)
        item_filter.setFilterCaseSensitivity(Qt.CaseInsensitive)
        item_combo.setModel(item_filter)
        item_combo.lineEdit().textEdited.connect(item_filter.setFilterFixedString)

        items = self.po_manager.get_items()
        item_model.appendRow(QStandardItem("Select Item"))
        item_combo.setItemData(0, -1, Qt.UserRole)
        for item in items:
            item_item = QStandardItem(item["name"])
            item_item.setData(item["id"], Qt.UserRole)
            item_model.appendRow(item_item)
        self.items_table.setCellWidget(row, 0, item_combo)

        unit_combo = QComboBox()
        unit_combo.setEditable(True)
        unit_combo.setInsertPolicy(QComboBox.NoInsert)
        unit_model = QStandardItemModel()
        unit_filter = QSortFilterProxyModel()
        unit_filter.setSourceModel(unit_model)
        unit_filter.setFilterCaseSensitivity(Qt.CaseInsensitive)
        unit_combo.setModel(unit_filter)
        unit_combo.lineEdit().textEdited.connect(unit_filter.setFilterFixedString)

        units = self.po_manager.get_units()
        unit_model.appendRow(QStandardItem("Select Unit"))
        unit_combo.setItemData(0, -1, Qt.UserRole)
        for unit in units:
            unit_item = QStandardItem(unit["name"])
            unit_item.setData(unit["id"], Qt.UserRole)
            unit_model.appendRow(unit_item)
        self.items_table.setCellWidget(row, 1, unit_combo)

        # Initialize items to avoid None
        self.items_table.setItem(row, 2, QTableWidgetItem("1"))
        self.items_table.setItem(row, 3, QTableWidgetItem("0.0"))
        self.items_table.setItem(row, 4, QTableWidgetItem("0.0"))
        self.items_table.setItem(row, 5, QTableWidgetItem("0.0"))
        self.update_total()  # Update total after adding row

    def update_total(self, item=None):
        # Disconnect to prevent recursion
        self.items_table.itemChanged.disconnect(self.update_total)

        total_amount = 0.0
        for row in range(self.items_table.rowCount()):
            try:
                # Safely get text, defaulting to "0" if None
                quantity_item = self.items_table.item(row, 2)
                unit_price_item = self.items_table.item(row, 3)
                discount_item = self.items_table.item(row, 4)

                quantity = float(quantity_item.text() if quantity_item else "0")
                unit_price = float(unit_price_item.text() if unit_price_item else "0")
                discount = float(discount_item.text() if discount_item else "0")

                total = (quantity * unit_price) - discount
                total_item = self.items_table.item(row, 5)
                if total_item is None:
                    total_item = QTableWidgetItem()
                    self.items_table.setItem(row, 5, total_item)
                total_item.setText(f"{total:.2f}")
                total_amount += total
            except (ValueError, AttributeError) as e:
                logger.error(f"Error calculating total for row {row}: {str(e)}")
                total_item = self.items_table.item(row, 5)
                if total_item is None:
                    total_item = QTableWidgetItem()
                    self.items_table.setItem(row, 5, total_item)
                total_item.setText("0.00")

        self.total_label.setText(
            f"Total Amount: {total_amount:.2f} {self.currency_combo.currentText()}"
        )

        # Reconnect signal after updates
        self.items_table.itemChanged.connect(self.update_total)

    def get_po_data(self):
        try:
            if not self.order_number_input.text():
                raise ValueError("Order Number is required")
            if self.supplier_combo.currentData(Qt.UserRole) == -1:
                raise ValueError("Supplier is required")
            if not self.order_date_input.text():
                raise ValueError("Order Date is required")
            if self.items_table.rowCount() == 0:
                raise ValueError("At least one item is required")

            items = []
            for row in range(self.items_table.rowCount()):
                item_combo = self.items_table.cellWidget(row, 0)
                unit_combo = self.items_table.cellWidget(row, 1)
                quantity_item = self.items_table.item(row, 2)
                unit_price_item = self.items_table.item(row, 3)
                discount_item = self.items_table.item(row, 4)
                total_price_item = self.items_table.item(row, 5)

                if (
                    item_combo.currentData(Qt.UserRole) == -1
                    or unit_combo.currentData(Qt.UserRole) == -1
                ):
                    raise ValueError(
                        f"Item and Unit must be selected for row {row + 1}"
                    )

                items.append(
                    {
                        "item_id": item_combo.currentData(Qt.UserRole),
                        "unit_id": unit_combo.currentData(Qt.UserRole),
                        "quantity": int(quantity_item.text() if quantity_item else "0"),
                        "unit_price": float(
                            unit_price_item.text() if unit_price_item else "0"
                        ),
                        "discount": float(
                            discount_item.text() if discount_item else "0"
                        ),
                        "total_price": float(
                            total_price_item.text() if total_price_item else "0"
                        ),
                    }
                )

            return {
                "order_number": self.order_number_input.text(),
                "supplier_id": self.supplier_combo.currentData(Qt.UserRole),
                "order_date": self.order_date_input.text(),
                "expected_delivery_date": self.expected_delivery_input.text() or None,
                "currency": self.currency_combo.currentText(),
                "notes": self.notes_input.toPlainText() or None,
                "items": items,
            }
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
            return None

    def save_purchase_order(self):
        po_data = self.get_po_data()
        if po_data:
            try:
                po_id = self.po_manager.create_purchase_order(
                    po_data["order_number"],
                    po_data["supplier_id"],
                    po_data["order_date"],
                    po_data["items"],
                    po_data["expected_delivery_date"],
                    currency=po_data["currency"],
                    notes=po_data["notes"],
                )
                QMessageBox.information(
                    self, "Success", "Purchase order added successfully"
                )
                self.po_added.emit()
                self.close()
            except Exception as e:
                logger.error(f"Failed to add purchase order: {str(e)}")
                QMessageBox.critical(
                    self, "Error", f"Failed to add purchase order: {str(e)}"
                )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    po_manager = PurchaseOrderManager()
    window = AddPurchaseOrderWindow(po_manager)
    window.show()
    sys.exit(app.exec_())
