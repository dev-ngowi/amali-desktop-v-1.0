from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QComboBox,
    QDialog,
    QMessageBox,
    QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal


class AddCustomerWindow(QDialog):
    customer_added = pyqtSignal()  # Signal to emit when customer is added

    def __init__(self, customer_manager, parent=None):
        super().__init__(parent)
        self.customer_manager = customer_manager
        self.parent_widget = parent
        self.setWindowTitle("Add New Customer")
        self.setMinimumSize(600, 400)  # Adjusted size for simpler form
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

        # Load dynamic data into combo boxes
        self.load_combo_data()

    def load_combo_data(self):
        """Load dynamic data into combo boxes from the database using CustomerManager"""
        try:
            # Load customer types
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

    def get_customer_data(self):
        """Collect customer data from the form for saving"""
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
                "active": 1,  # Default value as per schema
            }
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
            return None

    def save_customer(self):
        """Save the customer data to the database using CustomerManager"""
        customer_data = self.get_customer_data()
        if customer_data:
            try:
                customer_id = self.customer_manager.create_customer(
                    customer_data["customer_name"],
                    customer_data["customer_type_id"],
                    customer_data["city_id"],
                    phone=customer_data["phone"],
                    email=customer_data["email"],
                    address=customer_data["address"],
                    active=customer_data["active"],
                )
                QMessageBox.information(self, "Success", "Customer added successfully")
                self.customer_added.emit()  # Emit signal to refresh parent table
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add customer: {str(e)}")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    from Application.Components.Inventory.Customers.model import CustomerManager
    app = QApplication(sys.argv)
    customer_manager = CustomerManager()
    window = AddCustomerWindow(customer_manager)
    window.show()
    sys.exit(app.exec_())
