import sys
import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from Application.Components.Inventory.Customers.model import CustomerManager
from Application.Components.Inventory.Customers.register import AddCustomerWindow
from Application.Components.Inventory.Customers.update import EditCustomerWindow


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CustomerView(QWidget):
    def __init__(self, customer_manager=None):
        super().__init__()
        self.customer_manager = customer_manager or CustomerManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        header_layout = QHBoxLayout()
        title_label = QLabel("Customers")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        self.add_new_customer = QPushButton("Add New Customer")
        self.add_new_customer.clicked.connect(self.open_add_customer_window)
        header_layout.addWidget(self.add_new_customer)
        layout.addLayout(header_layout)

        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(6)
        self.customer_table.setHorizontalHeaderLabels(
            ["Customer Name", "City", "Phone", "Email", "Created At", "Action"]
        )

        # Set size policy to expanding
        self.customer_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.customer_table.horizontalHeader().setStretchLastSection(True)
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customer_table.setColumnWidth(
            0, 200
        )  # Adjusted width for better visibility
        self.customer_table.setColumnWidth(2, 150)
        self.customer_table.setColumnWidth(3, 150)
        self.customer_table.setColumnWidth(4, 150)
        layout.addWidget(self.customer_table, 1)

        self.populate_table()

    def populate_table(self):
        try:
            customer_data = self.customer_manager.list_customers()
            self.customer_table.setRowCount(len(customer_data))

            for row, customer in enumerate(customer_data):
                # Handle None values and ensure string conversion
                self.customer_table.setItem(
                    row, 0, QTableWidgetItem(customer["customer_name"] or "")
                )
                self.customer_table.setItem(
                    row, 1, QTableWidgetItem(customer.get("city_name", ""))
                )
                self.customer_table.setItem(
                    row, 2, QTableWidgetItem(customer["phone"] or "")
                )
                self.customer_table.setItem(
                    row, 3, QTableWidgetItem(customer["email"] or "")
                )
                self.customer_table.setItem(
                    row, 4, QTableWidgetItem(customer["created_at"] or "")
                )

                # Action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                edit_button = QPushButton("Edit")
                delete_button = QPushButton("Delete")

                # Connect buttons with customer ID
                edit_button.clicked.connect(
                    lambda _, cid=customer["id"]: self.open_edit_customer_window(cid)
                )
                delete_button.clicked.connect(
                    lambda _, cid=customer["id"]: self.delete_customer(cid)
                )

                action_layout.addWidget(edit_button)
                action_layout.addWidget(delete_button)
                action_layout.setAlignment(Qt.AlignCenter)
                action_layout.setContentsMargins(0, 0, 0, 0)
                self.customer_table.setCellWidget(row, 5, action_widget)

        except Exception as e:
            logger.error(f"Failed to fetch Customers: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load customers: {str(e)}")

    def open_add_customer_window(self):
        self.add_window = AddCustomerWindow(self.customer_manager, parent=self)
        self.add_window.customer_added.connect(
            self.populate_table
        )  # Refresh table after adding
        self.add_window.setModal(True)
        self.add_window.show()

    def open_edit_customer_window(self, customer_id):
        self.edit_window = EditCustomerWindow(
            self.customer_manager, parent=self, customer_id=customer_id
        )
        self.edit_window.customer_updated.connect(
            self.populate_table
        )  # Refresh table after editing
        self.edit_window.setModal(True)
        self.edit_window.show()

    def delete_customer(self, customer_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this customer?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                success = self.customer_manager.delete_customer(customer_id)
                if success:
                    self.populate_table()
                    QMessageBox.information(
                        self, "Success", "Customer deleted successfully"
                    )
                else:
                    QMessageBox.warning(self, "Warning", "No customer was deleted")
            except Exception as e:
                logger.error(f"Error deleting customer: {str(e)}")
                QMessageBox.critical(
                    self, "Error", f"Failed to delete customer: {str(e)}"
                )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomerView()
    window.setWindowTitle("Customers")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
