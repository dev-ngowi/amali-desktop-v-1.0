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


class EditItemWindow(QDialog):
    def __init__(self, item_manager, parent=None, item_id=None):
        super().__init__(parent)
        self.item_manager = item_manager
        self.parent_widget = parent
        self.item_id = item_id
        self.setWindowTitle("Edit Item")
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.load_item_data()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Form section
        form_widget = QWidget()
        grid_layout = QGridLayout()
        row = 0

        self.name_input = QLineEdit()
        self.barcode_input = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)  # Enable search
        self.item_type_combo = QComboBox()
        self.buying_unit_combo = QComboBox()
        self.selling_unit_combo = QComboBox()
        self.brand_combo = QComboBox()
        self.expire_date_input = QLineEdit()
        self.image_input = QLineEdit()

        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_input)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_image)
        image_layout.addWidget(browse_btn)
        image_widget = QWidget()
        image_widget.setLayout(image_layout)

        # Add fields to grid layout (Two-Column Example - Adjust as needed)
        grid_layout.addWidget(QLabel("Item Name *"), row, 0)
        grid_layout.addWidget(self.name_input, row, 1)
        grid_layout.addWidget(QLabel("Barcode"), row, 2)
        grid_layout.addWidget(self.barcode_input, row, 3)
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
        grid_layout.addWidget(image_widget, row, 1, 1, 3)  # Span across 3 columns
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

        main_layout.addWidget(form_widget)
        main_layout.addWidget(tabs)
        main_layout.addLayout(save_layout)
        self.setLayout(main_layout)

        self.load_combo_data()

    def load_combo_data(self):
        """Load dynamic data into combo boxes from the database using ItemManager"""
        # Categories
        categories_result = self.item_manager.get_categories()
        if categories_result["success"]:
            self.category_combo.addItem("Select Category", -1)  # Default option
            for category in categories_result["data"]:
                self.category_combo.addItem(category["name"], category["id"])
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to load categories: " + categories_result["message"],
            )
            self.category_combo.addItem("Select Category", -1)

        # Item Types
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

        # Units (for buying and selling)
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

        # Brands
        brands_result = self.item_manager.get_brands()
        if brands_result["success"]:
            self.brand_combo.addItem("None", None)  # Allow no brand selection
            for brand in brands_result["data"]:
                self.brand_combo.addItem(brand["name"], brand["id"])
        else:
            QMessageBox.warning(
                self, "Error", "Failed to load brands: " + brands_result["message"]
            )
            self.brand_combo.addItem("None", None)

    def browse_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.image_input.setText(file_name)

    def load_item_data(self):
        if not self.item_id:
            return

        result = self.item_manager.read_item(self.item_id)
        if result["success"]:
            item = result["data"]
            self.name_input.setText(item["name"])
            self.barcode_input.setText(item.get("barcode", ""))

            # Set combo box values based on IDs
            self._select_combobox_item(self.category_combo, item.get("category_id"))
            self._select_combobox_item(self.item_type_combo, item.get("item_type_id"))
            self._select_combobox_item(
                self.buying_unit_combo, item.get("buying_unit_id")
            )
            self._select_combobox_item(
                self.selling_unit_combo, item.get("selling_unit_id")
            )
            self._select_combobox_item(self.brand_combo, item.get("brand_id"))

            self.expire_date_input.setText(str(item.get("expire_date", "")))
            self.image_input.setText(item.get("item_image_path", ""))

            # Load store data into table
            if "stores" in item and isinstance(item["stores"], list):
                for store_item in item["stores"]:
                    self.add_store_row(store_data=store_item)
            else:
                # Ensure at least one row if no store data exists
                self.add_store_row()
        else:
            QMessageBox.critical(self, "Error", "Failed to load item data")

    def _select_combobox_item(self, combo, item_id):
        """Helper function to select an item in a combo box by its data value"""
        for i in range(combo.count()):
            if combo.itemData(i) == item_id:
                combo.setCurrentIndex(i)
                return
        # If ID not found, select the default "Select..." or "None" option
        combo.setCurrentIndex(0)

    def add_store_row(self, store_data=None):
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
        store_combo.setEditable(True)  # Make Store Name combo box type-editable

        # Other fields
        min_qty = QLineEdit("0")
        max_qty = QLineEdit("0")
        stock_qty = QLineEdit("0")
        purchase_rate = QLineEdit("0.0")
        selling_price = QLineEdit("0.0")

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
        tax_combo.setEditable(True)  # Make Tax combo box type-editable

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

        # Set initial data if provided
        if store_data:
            self._select_combobox_item(store_combo, store_data.get("store_id"))
            min_qty.setText(str(store_data.get("min_quantity", 0)))
            max_qty.setText(str(store_data.get("max_quantity", 0)))
            stock_qty.setText(str(store_data.get("stock_quantity", 0)))
            purchase_rate.setText(str(store_data.get("purchase_rate", 0.0)))
            selling_price.setText(str(store_data.get("selling_price", 0.0)))
            self._select_combobox_item(tax_combo, store_data.get("tax_id"))

        # Try setting focus to the first editable field (Min Qty) in the new row
        min_qty.setFocus()

    def delete_store_row(self, row):
        if self.store_table.rowCount() > 1:
            self.store_table.removeRow(row)

    def get_item_data(self):
        try:
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

                store_data.append(
                    {
                        "store_id": store_combo.currentData(),
                        "min_quantity": float(min_qty.text() or 0),
                        "max_quantity": float(max_qty.text() or 0),
                        "stock_quantity": float(stock_qty.text() or 0),
                        "purchase_rate": float(purchase_rate.text() or 0),
                        "selling_price": float(selling_price.text() or 0),
                        "tax_id": tax_combo.currentData(),
                    }
                )

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
        except (ValueError, IndexError) as e:
            QMessageBox.warning(
                self, "Warning", str(e) if str(e) else "Invalid input data"
            )
            return None

    def save_item(self):
        item_data = self.get_item_data()
        if item_data:
            result = self.item_manager.update_item(self.item_id, item_data)
            if result["success"]:
                QMessageBox.information(self, "Success", result["message"])
                self.close()
                if hasattr(self.parent_widget, "populate_table"):
                    self.parent_widget.populate_table()
            else:
                QMessageBox.critical(self, "Error", result["message"])
