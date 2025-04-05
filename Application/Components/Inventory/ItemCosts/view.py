import sys
import logging
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from Application.Components.Inventory.ItemCosts.model import CostStockViewManager

# Suppress Wayland warning
os.environ["QT_LOGGING_RULES"] = "qt5ct.debug=false"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CostStockView(QWidget):
    def __init__(self):
        super().__init__()
        self.item_type_manager = CostStockViewManager()
        try:
            self.available_units = self.item_type_manager.get_units()["data"]
            self.available_taxes = self.item_type_manager.get_taxes()["data"]
        except Exception as e:
            logger.error(f"Error loading units or taxes: {e}")
            self.available_units = []
            self.available_taxes = []
            QMessageBox.critical(self, "Error", f"Failed to load units or taxes: {e}")
            return
        self.original_data = {}  # To store original data for comparison
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        header_layout = QHBoxLayout()

        # Search bar only
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Items")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedWidth(200)
        header_layout.addWidget(self.search_input)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "",
                "ITEM NAME",
                "STOCK",
                "MIN QUANTITY",
                "MAX QUANTITY",
                "PURCHASE RATE",
                "SELLING RATE",
                "TAX",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(
            QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed
        )
        # Style the table
        self.table.setStyleSheet(
            """
            QTableWidget {
                border: 1px solid #d3d3d3;
                gridline-color: #d3d3d3;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d3d3d3;
                font-weight: bold;
            }
        """
        )
        layout.addWidget(self.table)

        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.update_selected_items)
        layout.addWidget(self.update_button, alignment=Qt.AlignLeft)
        self.setLayout(layout)
        self.populate_table()

    def populate_table(self):
        """Populate the table with cost and stock data"""
        result = self.item_type_manager.get_cost_stock_data()
        if not result["success"]:
            QMessageBox.critical(self, "Error", result["message"])
            return

        data = result["data"]
        self.table.setRowCount(len(data))
        self.original_data.clear()

        for row, item in enumerate(data):
            item_id = item["item_id"]
            self.original_data[item_id] = item.copy()

            # Checkbox
            checkbox = QCheckBox()
            self.table.setCellWidget(row, 0, checkbox)

            # Item Name (Store item_id in UserRole)
            name_item = QTableWidgetItem(item["item_name"])
            name_item.setData(Qt.UserRole, item_id)
            name_item.setFlags(
                name_item.flags() & ~Qt.ItemIsEditable
            )  # Make item name non-editable
            self.table.setItem(row, 1, name_item)

            # Stock
            stock_item = QTableWidgetItem(str(item["stock_quantity"] or "0.00"))
            self.table.setItem(row, 2, stock_item)

            # Min Quantity
            min_qty_item = QTableWidgetItem(str(item["min_quantity"] or "0.00"))
            self.table.setItem(row, 3, min_qty_item)

            # Max Quantity
            max_qty_item = QTableWidgetItem(str(item["max_quantity"] or "0.00"))
            self.table.setItem(row, 4, max_qty_item)

            # Purchase Rate with Unit Dropdown
            purchase_widget = QWidget()
            purchase_layout = QHBoxLayout()
            purchase_layout.setContentsMargins(0, 0, 0, 0)
            purchase_input = QLineEdit(str(item["purchase_rate"] or "0.00"))
            purchase_input.setFixedWidth(100)
            purchase_layout.addWidget(purchase_input)
            purchase_unit_combo = QComboBox()
            purchase_unit_combo.addItem("---Select---", -1)
            for unit in self.available_units:
                purchase_unit_combo.addItem(unit["name"], unit["id"])
            current_unit_id = item.get("purchase_unit_id")
            if current_unit_id:
                for index in range(purchase_unit_combo.count()):
                    if purchase_unit_combo.itemData(index) == current_unit_id:
                        purchase_unit_combo.setCurrentIndex(index)
                        break
            purchase_layout.addWidget(purchase_unit_combo)
            purchase_widget.setLayout(purchase_layout)
            self.table.setCellWidget(row, 5, purchase_widget)

            # Selling Rate with Unit Dropdown
            selling_widget = QWidget()
            selling_layout = QHBoxLayout()
            selling_layout.setContentsMargins(0, 0, 0, 0)
            selling_input = QLineEdit(str(item["selling_rate"] or "0.00"))
            selling_input.setFixedWidth(100)
            selling_layout.addWidget(selling_input)
            selling_unit_combo = QComboBox()
            selling_unit_combo.addItem("---Select---", -1)
            for unit in self.available_units:
                selling_unit_combo.addItem(unit["name"], unit["id"])
            current_selling_unit_id = item.get("selling_unit_id")
            if current_selling_unit_id:
                for index in range(selling_unit_combo.count()):
                    if selling_unit_combo.itemData(index) == current_selling_unit_id:
                        selling_unit_combo.setCurrentIndex(index)
                        break
            selling_layout.addWidget(selling_unit_combo)
            selling_widget.setLayout(selling_layout)
            self.table.setCellWidget(row, 6, selling_widget)

            # Tax Dropdown
            tax_combo = QComboBox()
            tax_combo.addItem("---Select---", -1)
            for tax in self.available_taxes:
                tax_combo.addItem(tax["name"], tax["id"])
            current_tax_id = item.get("tax_id")
            if current_tax_id:
                for index in range(tax_combo.count()):
                    if tax_combo.itemData(index) == current_tax_id:
                        tax_combo.setCurrentIndex(index)
                        break
            self.table.setCellWidget(row, 7, tax_combo)

    def filter_table(self):
        """Filter the table based on the search input"""
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            item_name = self.table.item(row, 1).text().lower()
            self.table.setRowHidden(row, search_text not in item_name)

    def update_selected_items(self):
        """Update the selected items in the table without store association"""
        updated_items = []
        for row in range(self.table.rowCount()):
            if (
                isinstance(self.table.cellWidget(row, 0), QCheckBox)
                and self.table.cellWidget(row, 0).isChecked()
            ):
                item_id = self.table.item(row, 1).data(Qt.UserRole)
                if item_id in self.original_data:
                    original_item = self.original_data[item_id]
                    updated_data = {"item_id": item_id}
                    has_updates = False

                    # Stock Quantity
                    try:
                        stock_quantity = float(self.table.item(row, 2).text())
                        if stock_quantity != original_item.get("stock_quantity", 0.00):
                            updated_data["stock_quantity"] = stock_quantity
                            has_updates = True
                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Invalid stock quantity for {original_item['item_name']}",
                        )
                        continue

                    # Min Quantity
                    try:
                        min_quantity = float(self.table.item(row, 3).text())
                        if min_quantity != original_item.get("min_quantity", 0.00):
                            updated_data["min_quantity"] = min_quantity
                            has_updates = True
                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Invalid min quantity for {original_item['item_name']}",
                        )
                        continue

                    # Max Quantity
                    try:
                        max_quantity = float(self.table.item(row, 4).text())
                        if max_quantity != original_item.get("max_quantity", 0.00):
                            updated_data["max_quantity"] = max_quantity
                            has_updates = True
                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Invalid max quantity for {original_item['item_name']}",
                        )
                        continue

                    # Purchase Rate and Unit
                    purchase_widget = self.table.cellWidget(row, 5)
                    purchase_input = purchase_widget.layout().itemAt(0).widget()
                    purchase_unit_combo = purchase_widget.layout().itemAt(1).widget()
                    try:
                        purchase_rate = float(purchase_input.text())
                        purchase_unit_id = purchase_unit_combo.currentData()
                        if purchase_rate != original_item.get(
                            "purchase_rate", 0.00
                        ) or purchase_unit_id != original_item.get("purchase_unit_id"):
                            updated_data["purchase_rate"] = purchase_rate
                            updated_data["purchase_unit_id"] = (
                                purchase_unit_id if purchase_unit_id != -1 else None
                            )
                            has_updates = True
                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Invalid purchase rate for {original_item['item_name']}",
                        )
                        continue

                    # Selling Rate and Unit
                    selling_widget = self.table.cellWidget(row, 6)
                    selling_input = selling_widget.layout().itemAt(0).widget()
                    selling_unit_combo = selling_widget.layout().itemAt(1).widget()
                    try:
                        selling_rate = float(selling_input.text())
                        selling_unit_id = selling_unit_combo.currentData()
                        if selling_rate != original_item.get(
                            "selling_rate", 0.00
                        ) or selling_unit_id != original_item.get("selling_unit_id"):
                            updated_data["selling_rate"] = selling_rate
                            updated_data["selling_unit_id"] = (
                                selling_unit_id if selling_unit_id != -1 else None
                            )
                            has_updates = True
                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Invalid selling rate for {original_item['item_name']}",
                        )
                        continue

                    # Tax
                    tax_combo = self.table.cellWidget(row, 7)
                    current_tax_id = tax_combo.currentData()
                    if current_tax_id != original_item.get("tax_id"):
                        updated_data["tax_id"] = (
                            current_tax_id if current_tax_id != -1 else None
                        )
                        has_updates = True

                    if has_updates:
                        updated_items.append(updated_data)

        if not updated_items:
            QMessageBox.information(
                self, "Info", "No items selected or no changes made."
            )
            return

        # Update items directly without store iteration
        result = self.item_type_manager.update_cost_stock_data(updated_items)
        if not result["success"]:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update items: {result['message']}",
            )
            return

        QMessageBox.information(
            self,
            "Success",
            f"Updated {len(updated_items)} items successfully",
        )
        self.populate_table()

    def find_tax_id_by_name(self, tax_name):
        for tax in self.available_taxes:
            if tax["name"] == tax_name:
                return tax["id"]
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    item_type_window = CostStockView()
    item_type_window.setWindowTitle("Cost & Stock View")
    item_type_window.show()
    sys.exit(app.exec_())
