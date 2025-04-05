import sys
import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from Application.Components.Inventory.Suppliers.model import SupplierManager
from Application.Components.Inventory.Suppliers.register import AddSupplierWindow
from Application.Components.Inventory.Suppliers.update import EditSupplierWindow

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SupplierView(QWidget):
    def __init__(self, supplier_manager=None):
        super().__init__()
        self.supplier_manager = supplier_manager or SupplierManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        header_layout = QHBoxLayout()
        title_label = QLabel("Suppliers")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        self.add_new_supplier = QPushButton("Add New Supplier")
        self.add_new_supplier.clicked.connect(self.open_add_supplier_window)
        header_layout.addWidget(self.add_new_supplier)
        layout.addLayout(header_layout)

        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(7)
        self.supplier_table.setHorizontalHeaderLabels(
            [
                "Supplier Name",
                "City",
                "Phone",
                "Email",
                "Contact Person",
                "Created At",
                "Action",
            ]
        )

        self.supplier_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.supplier_table.horizontalHeader().setStretchLastSection(True)
        self.supplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.supplier_table.setColumnWidth(0, 200)
        self.supplier_table.setColumnWidth(2, 150)
        self.supplier_table.setColumnWidth(3, 150)
        self.supplier_table.setColumnWidth(4, 150)
        self.supplier_table.setColumnWidth(5, 150)
        layout.addWidget(self.supplier_table, 1)

        self.populate_table()

    def populate_table(self):
        try:
            supplier_data = self.supplier_manager.list_suppliers()
            self.supplier_table.setRowCount(len(supplier_data))

            for row, supplier in enumerate(supplier_data):
                self.supplier_table.setItem(
                    row, 0, QTableWidgetItem(supplier["name"] or "")
                )
                self.supplier_table.setItem(
                    row, 1, QTableWidgetItem(supplier.get("city_name", ""))
                )
                self.supplier_table.setItem(
                    row, 2, QTableWidgetItem(supplier["phone"] or "")
                )
                self.supplier_table.setItem(
                    row, 3, QTableWidgetItem(supplier["email"] or "")
                )
                self.supplier_table.setItem(
                    row, 4, QTableWidgetItem(supplier["contact_person"] or "")
                )
                self.supplier_table.setItem(
                    row, 5, QTableWidgetItem(supplier["created_at"] or "")
                )

                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                edit_button = QPushButton("Edit")
                delete_button = QPushButton("Delete")

                edit_button.clicked.connect(
                    lambda _, sid=supplier["id"]: self.open_edit_supplier_window(sid)
                )
                delete_button.clicked.connect(
                    lambda _, sid=supplier["id"]: self.delete_supplier(sid)
                )

                action_layout.addWidget(edit_button)
                action_layout.addWidget(delete_button)
                action_layout.setAlignment(Qt.AlignCenter)
                action_layout.setContentsMargins(0, 0, 0, 0)
                self.supplier_table.setCellWidget(row, 6, action_widget)

        except Exception as e:
            logger.error(f"Failed to fetch Suppliers: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load suppliers: {str(e)}")

    def open_add_supplier_window(self):
        self.add_window = AddSupplierWindow(self.supplier_manager, parent=self)
        self.add_window.supplier_added.connect(self.populate_table)
        self.add_window.setModal(True)
        self.add_window.show()

    def open_edit_supplier_window(self, supplier_id):
        self.edit_window = EditSupplierWindow(
            self.supplier_manager, parent=self, supplier_id=supplier_id
        )
        self.edit_window.supplier_updated.connect(self.populate_table)
        self.edit_window.setModal(True)
        self.edit_window.show()

    def delete_supplier(self, supplier_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this supplier?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                success = self.supplier_manager.delete_supplier(supplier_id)
                if success:
                    self.populate_table()
                    QMessageBox.information(
                        self, "Success", "Supplier deleted successfully"
                    )
                else:
                    QMessageBox.warning(self, "Warning", "No supplier was deleted")
            except Exception as e:
                logger.error(f"Error deleting supplier: {str(e)}")
                QMessageBox.critical(
                    self, "Error", f"Failed to delete supplier: {str(e)}"
                )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SupplierView()
    window.setWindowTitle("Suppliers")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
