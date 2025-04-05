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


class EditSupplierWindow(QDialog):
    supplier_updated = pyqtSignal()

    def __init__(self, supplier_manager, parent=None, supplier_id=None):
        super().__init__(parent)
        self.supplier_manager = supplier_manager
        self.parent_widget = parent
        self.supplier_id = supplier_id
        self.setWindowTitle("Edit Supplier")
        self.setMinimumSize(600, 500)
        self.init_ui()
        self.load_supplier_data()

    def init_ui(self):
        main_layout = QVBoxLayout()
        form_widget = QWidget()
        grid_layout = QGridLayout()
        row = 0

        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()
        self.city_combo = QComboBox()
        self.city_combo.setEditable(True)
        self.state_input = QLineEdit()
        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        self.contact_person_input = QLineEdit()
        self.tin_input = QLineEdit()
        self.vrn_input = QLineEdit()
        self.postal_code_input = QLineEdit()

        grid_layout.addWidget(QLabel("Supplier Name *"), row, 0)
        grid_layout.addWidget(self.name_input, row, 1)
        row += 1

        grid_layout.addWidget(QLabel("Email *"), row, 0)
        grid_layout.addWidget(self.email_input, row, 1)
        grid_layout.addWidget(QLabel("Phone *"), row, 2)
        grid_layout.addWidget(self.phone_input, row, 3)
        row += 1

        grid_layout.addWidget(QLabel("Address *"), row, 0)
        grid_layout.addWidget(self.address_input, row, 1, 1, 3)
        row += 1

        grid_layout.addWidget(QLabel("City *"), row, 0)
        grid_layout.addWidget(self.city_combo, row, 1)
        grid_layout.addWidget(QLabel("State *"), row, 2)
        grid_layout.addWidget(self.state_input, row, 3)
        row += 1

        grid_layout.addWidget(QLabel("Country *"), row, 0)
        grid_layout.addWidget(self.country_combo, row, 1)
        grid_layout.addWidget(QLabel("Postal Code"), row, 2)
        grid_layout.addWidget(self.postal_code_input, row, 3)
        row += 1

        grid_layout.addWidget(QLabel("Contact Person"), row, 0)
        grid_layout.addWidget(self.contact_person_input, row, 1)
        row += 1

        grid_layout.addWidget(QLabel("TIN"), row, 0)
        grid_layout.addWidget(self.tin_input, row, 1)
        grid_layout.addWidget(QLabel("VRN"), row, 2)
        grid_layout.addWidget(self.vrn_input, row, 3)

        form_widget.setLayout(grid_layout)

        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_supplier)
        save_layout.addWidget(save_btn)

        main_layout.addWidget(form_widget)
        main_layout.addStretch()
        main_layout.addLayout(save_layout)
        self.setLayout(main_layout)

        self.load_combo_data()

    def load_combo_data(self):
        try:
            cities = self.supplier_manager.get_cities()
            self.city_combo.addItem("Select City", -1)
            for city in cities:
                self.city_combo.addItem(city["name"], city["id"])

            countries = self.supplier_manager.get_countries()
            self.country_combo.addItem("Select Country", -1)
            for country in countries:
                self.country_combo.addItem(country["name"], country["id"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load combo data: {str(e)}")
            self.city_combo.addItem("Select City", -1)
            self.country_combo.addItem("Select Country", -1)

    def load_supplier_data(self):
        if not self.supplier_id:
            return
        try:
            supplier = self.supplier_manager.get_supplier(self.supplier_id)
            if supplier:
                self.name_input.setText(supplier["name"] or "")
                self.email_input.setText(supplier["email"] or "")
                self.phone_input.setText(supplier["phone"] or "")
                self.address_input.setText(supplier["address"] or "")
                self._select_combobox_item(self.city_combo, supplier["city_id"])
                self.state_input.setText(supplier["state"] or "")
                self._select_combobox_item(self.country_combo, supplier["country_id"])
                self.contact_person_input.setText(supplier["contact_person"] or "")
                self.tin_input.setText(supplier["tin"] or "")
                self.vrn_input.setText(supplier["vrn"] or "")
                self.postal_code_input.setText(supplier["postal_code"] or "")
            else:
                QMessageBox.critical(self, "Error", "Supplier not found")
                self.close()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load supplier data: {str(e)}"
            )
            self.close()

    def _select_combobox_item(self, combo, item_id):
        for i in range(combo.count()):
            if combo.itemData(i) == item_id:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(0)

    def get_supplier_data(self):
        try:
            if not self.name_input.text():
                raise ValueError("Supplier Name is required")
            if not self.email_input.text():
                raise ValueError("Email is required")
            if not self.phone_input.text():
                raise ValueError("Phone is required")
            if not self.address_input.text():
                raise ValueError("Address is required")
            if self.city_combo.currentData() == -1:
                raise ValueError("City is required")
            if not self.state_input.text():
                raise ValueError("State is required")
            if self.country_combo.currentData() == -1:
                raise ValueError("Country is required")

            return {
                "name": self.name_input.text(),
                "email": self.email_input.text(),
                "phone": self.phone_input.text(),
                "address": self.address_input.text(),
                "city_id": self.city_combo.currentData(),
                "state": self.state_input.text(),
                "country_id": self.country_combo.currentData(),
                "contact_person": self.contact_person_input.text() or None,
                "tin": self.tin_input.text() or None,
                "vrn": self.vrn_input.text() or None,
                "postal_code": self.postal_code_input.text() or None,
            }
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
            return None

    def save_supplier(self):
        supplier_data = self.get_supplier_data()
        if supplier_data:
            try:
                success = self.supplier_manager.update_supplier(
                    self.supplier_id, **supplier_data
                )
                if success:
                    QMessageBox.information(
                        self, "Success", "Supplier updated successfully"
                    )
                    self.supplier_updated.emit()
                    self.close()
                else:
                    QMessageBox.warning(
                        self, "Warning", "No changes were made to the supplier"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to update supplier: {str(e)}"
                )


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    from Application.Components.Inventory.Suppliers.model import SupplierManager

    app = QApplication(sys.argv)
    supplier_manager = SupplierManager()
    window = EditSupplierWindow(supplier_manager, supplier_id=1)
    window.show()
    sys.exit(app.exec_())
