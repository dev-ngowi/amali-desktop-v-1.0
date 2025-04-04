from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QComboBox,
    QFileDialog,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QGridLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
import random

from Application.Components.Inventory.Items.model import ItemManager


class AddItemWindow(QDialog):
    def __init__(self, item_manager, parent=None):
        super().__init__(parent)
        self.item_manager = item_manager  # Instance of ItemManager passed in
        self.parent_widget = parent
        self.setWindowTitle("Add New Item")
        self.setMinimumSize(900, 450)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()

        # Form section
        form_widget = QWidget()
        grid_layout = QGridLayout()
        row = 0

        # Form fields
        self.name_input = QLineEdit()
        self.barcode_input = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.item_type_combo = QComboBox()
        self.buying_unit_combo = QComboBox()
        self.selling_unit_combo = QComboBox()
        self.brand_combo = QComboBox()
        self.expire_date_input = QLineEdit()
        self.image_input = QLineEdit()

        # Barcode with generate button
        barcode_layout = QHBoxLayout()
        barcode_layout.addWidget(self.barcode_input)
        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self.generate_barcode)
        barcode_layout.addWidget(generate_btn)
        barcode_widget = QWidget()
        barcode_widget.setLayout(barcode_layout)

        # Image with browse button
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_input)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_image)
        image_layout.addWidget(browse_btn)
        image_widget = QWidget()
        image_widget.setLayout(image_layout)

        # Add fields to grid layout (Two-Column Example)
        grid_layout.addWidget(QLabel("Item Name *"), row, 0)
        grid_layout.addWidget(self.name_input, row, 1)
        grid_layout.addWidget(QLabel("Barcode"), row, 2)
        grid_layout.addWidget(barcode_widget, row, 3)
        row += 1

        grid_layout.addWidget(QLabel("Category *"), row, 0)
        grid_layout.addWidget(self.category_combo, row, 1)
        grid_layout.addWidget(QLabel("Item Type *"), row, 2)
        grid_layout.addWidget(self.item_type_combo, row, 3)
        row += 1

        grid_layout.addWidget(QLabel("Buying Unit *"), row, 0)
        grid_layout.addWidget(self.buying_unit_combo, row, 1)
        grid_layout.addWidget(QLabel("Selling Unit *"), row, 2)
        grid_layout.addWidget(self.selling_unit_combo, row, 3)
        row += 1

        grid_layout.addWidget(QLabel("Brand"), row, 0)
        grid_layout.addWidget(self.brand_combo, row, 1)
        grid_layout.addWidget(QLabel("Expire Date"), row, 2)
        grid_layout.addWidget(self.expire_date_input, row, 3)
        row += 1

        grid_layout.addWidget(QLabel("Item Image"), row, 0)
        grid_layout.addWidget(image_widget, row, 1, 1, 3)
        row += 1

        form_widget.setLayout(grid_layout)

        # Store tab
        tabs = QTabWidget()
        self.store_table = QTableWidget()
        self.store_table.setColumnCount(8)
        self.store_table.setHorizontalHeaderLabels(
            [
                "Store Name",
                "Min Qty",
                "Max Qty",
                "Stock",
                "Purchase Rate",
                "Selling Price",
                "Tax",
                "Action",
            ]
        )
        self.store_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        add_store_btn = QPushButton("+ Add New Store")
        add_store_btn.clicked.connect(self.add_store_row)

        store_layout = QVBoxLayout()
        store_layout.addWidget(self.store_table)
        store_layout.addWidget(add_store_btn)

        store_widget = QWidget()
        store_widget.setLayout(store_layout)
        tabs.addTab(store_widget, "Store, Cost & Stock")

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_item)
        save_layout.addWidget(save_btn)

        # Assemble main layout
        main_layout.addWidget(form_widget)
        main_layout.addWidget(tabs)
        main_layout.addLayout(save_layout)
        self.setLayout(main_layout)

        # Load dynamic data into combo boxes
        self.load_combo_data()
        # Add an initial store row
        self.add_store_row()

    def load_combo_data(self):
        """Load dynamic data into combo boxes from the database using ItemManager"""
        categories_result = self.item_manager.get_categories()
        if categories_result["success"]:
            self.category_combo.addItem("Select Category", -1)
            for category in categories_result["data"]:
                self.category_combo.addItem(category["name"], category["id"])
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to load categories: " + categories_result["message"],
            )
            self.category_combo.addItem("Select Category", -1)

        item_types_result = self.item_manager.get_item_types()
        if item_types_result["success"]:
            self.item_type_combo.addItem("Select Item Type", -1)
            for item_type in item_types_result["data"]:
                self.item_type_combo.addItem(item_type["name"], item_type["id"])
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to load item types: " + item_types_result["message"],
            )
            self.item_type_combo.addItem("Select Item Type", -1)

        units_result = self.item_manager.get_units()
        if units_result["success"]:
            self.buying_unit_combo.addItem("Select Unit", -1)
            self.selling_unit_combo.addItem("Select Unit", -1)
            for unit in units_result["data"]:
                self.buying_unit_combo.addItem(unit["name"], unit["id"])
                self.selling_unit_combo.addItem(unit["name"], unit["id"])
        else:
            QMessageBox.warning(
                self, "Error", "Failed to load units: " + units_result["message"]
            )
            self.buying_unit_combo.addItem("Select Unit", -1)
            self.selling_unit_combo.addItem("Select Unit", -1)

        brands_result = self.item_manager.get_brands()
        if brands_result["success"]:
            self.brand_combo.addItem("None", None)
            for brand in brands_result["data"]:
                self.brand_combo.addItem(brand["name"], brand["id"])
        else:
            QMessageBox.warning(
                self, "Error", "Failed to load brands: " + brands_result["message"]
            )
            self.brand_combo.addItem("None", None)

    def generate_barcode(self):
        """Generate a random 12-digit barcode"""
        barcode = str(random.randint(100000000000, 999999999999))
        self.barcode_input.setText(barcode)

    def browse_image(self):
        """Open file dialog to select an image"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.image_input.setText(file_name)

    def add_store_row(self):
        """Add a new row to the store table with dynamic store and tax data"""
        row_count = self.store_table.rowCount()
        self.store_table.insertRow(row_count)

        # Store combo box
        store_combo = QComboBox()
        stores_result = self.item_manager.get_stores()
        if stores_result["success"]:
            store_combo.addItem("Select Store", -1)
            for store in stores_result["data"]:
                store_combo.addItem(store["name"], store["id"])
        else:
            QMessageBox.warning(
                self, "Error", "Failed to load stores: " + stores_result["message"]
            )
            store_combo.addItem("Select Store", -1)
        store_combo.setEditable(True)

        # Editable fields with default values
        min_qty = QLineEdit()
        min_qty.setText("0")
        min_qty.setAlignment(Qt.AlignRight)
        max_qty = QLineEdit()
        max_qty.setText("0")
        max_qty.setAlignment(Qt.AlignRight)
        stock_qty = QLineEdit()
        stock_qty.setText("0")
        stock_qty.setAlignment(Qt.AlignRight)
        purchase_rate = QLineEdit()
        purchase_rate.setText("0.00")
        purchase_rate.setAlignment(Qt.AlignRight)
        selling_price = QLineEdit()
        selling_price.setText("0.00")
        selling_price.setAlignment(Qt.AlignRight)

        # Tax combo box
        tax_combo = QComboBox()
        taxes_result = self.item_manager.get_taxes()
        if taxes_result["success"]:
            tax_combo.addItem("None", None)
            for tax in taxes_result["data"]:
                tax_combo.addItem(tax["name"], tax["id"])
        else:
            QMessageBox.warning(
                self, "Error", "Failed to load taxes: " + taxes_result["message"]
            )
            tax_combo.addItem("None", None)
        tax_combo.setEditable(True)

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.delete_store_row(row_count))

        # Add widgets to table
        self.store_table.setCellWidget(row_count, 0, store_combo)
        self.store_table.setCellWidget(row_count, 1, min_qty)
        self.store_table.setCellWidget(row_count, 2, max_qty)
        self.store_table.setCellWidget(row_count, 3, stock_qty)
        self.store_table.setCellWidget(row_count, 4, purchase_rate)
        self.store_table.setCellWidget(row_count, 5, selling_price)
        self.store_table.setCellWidget(row_count, 6, tax_combo)
        self.store_table.setCellWidget(row_count, 7, delete_btn)

        # Set focus to min_qty
        min_qty.setFocus()

    def delete_store_row(self, row):
        """Delete a row from the store table if more than one row exists"""
        if self.store_table.rowCount() > 1:
            self.store_table.removeRow(row)

    def get_item_data(self):
        """Collect item data from the form for saving"""
        try:
            # Validate required fields
            if not self.name_input.text():
                raise ValueError("Name is required")
            if self.category_combo.currentData() == -1:
                raise ValueError("Category is required")
            if self.item_type_combo.currentData() == -1:
                raise ValueError("Item Type is required")
            if self.buying_unit_combo.currentData() == -1:
                raise ValueError("Buying Unit is required")
            if self.selling_unit_combo.currentData() == -1:
                raise ValueError("Selling Unit is required")

            # Collect store data
            store_data = []
            for row in range(self.store_table.rowCount()):
                store_combo = self.store_table.cellWidget(row, 0)
                min_qty = self.store_table.cellWidget(row, 1)
                max_qty = self.store_table.cellWidget(row, 2)
                stock_qty = self.store_table.cellWidget(row, 3)
                purchase_rate = self.store_table.cellWidget(row, 4)
                selling_price = self.store_table.cellWidget(row, 5)
                tax_combo = self.store_table.cellWidget(row, 6)

                if store_combo.currentData() == -1:
                    raise ValueError(f"Store is required for row {row + 1}")

                # Convert text to appropriate types with error handling
                try:
                    min_qty_val = float(min_qty.text() or "0")
                    max_qty_val = float(max_qty.text() or "0")
                    stock_qty_val = float(stock_qty.text() or "0")
                    purchase_rate_val = float(purchase_rate.text() or "0.00")
                    selling_price_val = float(selling_price.text() or "0.00")
                except ValueError as e:
                    raise ValueError(
                        f"Invalid numeric value in row {row + 1}: {str(e)}"
                    )

                store_data.append(
                    {
                        "store_id": store_combo.currentData(),
                        "min_quantity": min_qty_val,
                        "max_quantity": max_qty_val,
                        "stock_quantity": stock_qty_val,
                        "purchase_rate": purchase_rate_val,
                        "selling_price": selling_price_val,
                        "tax_id": tax_combo.currentData(),
                    }
                )

            # Return item data dictionary
            return {
                "name": self.name_input.text(),
                "barcode": self.barcode_input.text() or None,
                "category_id": self.category_combo.currentData(),
                "item_type_id": self.item_type_combo.currentData(),
                "buying_unit_id": self.buying_unit_combo.currentData(),
                "selling_unit_id": self.selling_unit_combo.currentData(),
                "brand_id": self.brand_combo.currentData(),
                "expire_date": self.expire_date_input.text() or None,
                "item_image_path": self.image_input.text() or None,
                "store_data": store_data,
                "item_group_id": None,
            }
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
            return None

    def save_item(self):
        """Save the item data to the database using ItemManager"""
        item_data = self.get_item_data()
        if item_data:
            result = self.item_manager.create_item(item_data)
            if result["success"]:
                QMessageBox.information(self, "Success", result["message"])
                self.close()
                if hasattr(self.parent_widget, "populate_table"):
                    self.parent_widget.populate_table()
            else:
                QMessageBox.critical(self, "Error", result["message"])


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    item_manager = ItemManager()
    window = AddItemWindow(item_manager)
    window.show()
    sys.exit(app.exec_())
