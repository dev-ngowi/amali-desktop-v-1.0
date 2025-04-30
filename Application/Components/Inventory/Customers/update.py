from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QDialog,
    QMessageBox,
    QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal


class EditCustomerWindow(QDialog):
    customer_updated = pyqtSignal()  # Signal to emit when customer is updated

    def __init__(self, customer_manager, parent=None, customer_id=None):
        super().__init__(parent)
        self.customer_manager = customer_manager
        self.parent_widget = parent
        self.customer_id = customer_id
        self.setWindowTitle("Edit Customer")
        self.setMinimumSize(600, 400)  # Adjusted size for simpler form
        self.init_ui()
        self.load_customer_data()

    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()

        # Form section
        form_widget = QWidget()
        grid_layout = QGridLayout()
        row = 0

        # Form fields
        self.name_input = QLineEdit()
        self.customer_type_combo = QComboBox()
        self.customer_type_combo.setEditable(True)
        self.city_combo = QComboBox()
        self.city_combo.setEditable(True)
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()

        # Add fields to grid layout (Two-Column)
        grid_layout.addWidget(QLabel("Customer Name *"), row, 0)
        grid_layout.addWidget(self.name_input, row, 1)
        row += 1

        grid_layout.addWidget(QLabel("Customer Type *"), row, 0)
        grid_layout.addWidget(self.customer_type_combo, row, 1)
        grid_layout.addWidget(QLabel("City *"), row, 2)
        grid_layout.addWidget(self.city_combo, row, 3)
        row += 1

        grid_layout.addWidget(QLabel("Phone"), row, 0)
        grid_layout.addWidget(self.phone_input, row, 1)
        grid_layout.addWidget(QLabel("Email"), row, 2)
        grid_layout.addWidget(self.email_input, row, 3)
        row += 1

        grid_layout.addWidget(QLabel("Address"), row, 0)
        grid_layout.addWidget(self.address_input, row, 1, 1, 3)  # Span across columns
        row += 1

        form_widget.setLayout(grid_layout)

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_customer)
        save_layout.addWidget(save_btn)

        # Assemble main layout
        main_layout.addWidget(form_widget)
        main_layout.addStretch()
        main_layout.addLayout(save_layout)
        self.setLayout(main_layout)

        self.load_combo_data()

    def load_combo_data(self):
        """Load dynamic data into combo boxes from the database using CustomerManager"""
        try:
            customer_types = self.customer_manager.get_customer_types()
            self.customer_type_combo.addItem("Select Customer Type", -1)
            for ct in customer_types:
                self.customer_type_combo.addItem(ct["name"], ct["id"])

            # Load cities
            cities = self.customer_manager.get_cities()
            self.city_combo.addItem("Select City", -1)
            for city in cities:
                self.city_combo.addItem(city["name"], city["id"])
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to load combo data: {str(e)}",
            )
            self.customer_type_combo.addItem("Select Customer Type", -1)
            self.city_combo.addItem("Select City", -1)

    def load_customer_data(self):
        """Load existing customer data into the form"""
        if not self.customer_id:
            return

        try:
            customer = self.customer_manager.get_customer(self.customer_id)
            if customer:
                self.name_input.setText(customer["customer_name"] or "")
                self._select_combobox_item(
                    self.customer_type_combo, customer["customer_type_id"]
                )
                self._select_combobox_item(self.city_combo, customer["city_id"])
                self.phone_input.setText(customer["phone"] or "")
                self.email_input.setText(customer["email"] or "")
                self.address_input.setText(customer["address"] or "")
            else:
                QMessageBox.critical(self, "Error", "Customer not found")
                self.close()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load customer data: {str(e)}"
            )
            self.close()

    def _select_combobox_item(self, combo, item_id):
        """Helper function to select an item in a combo box by its data value"""
        for i in range(combo.count()):
            if combo.itemData(i) == item_id:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(0)  # Default to "Select..." if not found

    def get_customer_data(self):
        """Collect customer data from the form for updating"""
        try:
            # Validate required fields
            if not self.name_input.text():
                raise ValueError("Customer Name is required")
            if self.customer_type_combo.currentData() == -1:
                raise ValueError("Customer Type is required")
            if self.city_combo.currentData() == -1:
                raise ValueError("City is required")

            # Return customer data dictionary
            return {
                "customer_name": self.name_input.text(),
                "customer_type_id": self.customer_type_combo.currentData(),
                "city_id": self.city_combo.currentData(),
                "phone": self.phone_input.text() or None,
                "email": self.email_input.text() or None,
                "address": self.address_input.text() or None,
            }
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
            return None

    def save_customer(self):
        """Save the updated customer data to the database using CustomerManager"""
        customer_data = self.get_customer_data()
        if customer_data:
            try:
                success = self.customer_manager.update_customer(
                    self.customer_id, **customer_data
                )
                if success:
                    QMessageBox.information(
                        self, "Success", "Customer updated successfully"
                    )
                    self.customer_updated.emit()  # Emit signal to refresh parent table
                    self.close()
                else:
                    QMessageBox.warning(
                        self, "Warning", "No changes were made to the customer"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to update customer: {str(e)}"
                )


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    from Application.Components.Inventory.Customers.model import CustomerManager

    app = QApplication(sys.argv)
    customer_manager = CustomerManager()
    window = EditCustomerWindow(customer_manager, customer_id=1) 
    window.show()
    sys.exit(app.exec_())
