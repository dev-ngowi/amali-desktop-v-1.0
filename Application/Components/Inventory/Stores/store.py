import sys
import logging
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QMessageBox,
)
from PyQt5.QtCore import Qt

from Application.Components.Inventory.Stores.modal import StoreManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AddStoreDialog(QDialog):
    def __init__(self, store_manager, parent=None):
        super().__init__(parent)
        self.store_manager = store_manager
        self.setWindowTitle("Add New Store")
        self.setMinimumSize(400, 200)
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.location_input = QLineEdit()
        self.manager_combo = QComboBox()

        # Populate the combo box with users
        users = self.store_manager.get_users()
        if not users:
            logger.warning("No users available to populate manager dropdown.")
            self.manager_combo.addItem("No managers available", None)
            QMessageBox.warning(self, "Warning", "No managers found in the database.")
        else:
            for user in users:
                self.manager_combo.addItem(user["username"], user["id"])
            logger.info("Manager dropdown populated successfully.")

        self.layout.addRow(QLabel("Name:"), self.name_input)
        self.layout.addRow(QLabel("Location:"), self.location_input)
        self.layout.addRow(QLabel("Manager:"), self.manager_combo)

        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addRow(self.buttons_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_store_data(self):
        manager_id = self.manager_combo.currentData()
        if manager_id is None:
            logger.error("No valid manager selected.")
            return None, None, None
        return (
            self.name_input.text(),
            self.location_input.text(),
            manager_id,
        )


class StoresView(QWidget):
    def __init__(self):
        super().__init__()
        self.store_manager = StoreManager()  # No need to pass connection

        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        title_label = QLabel("Stores")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        self.add_store_button = QPushButton("Add New Store")
        header_layout.addWidget(self.add_store_button)
        layout.addLayout(header_layout)

        self.stores_table = QTableWidget()
        self.stores_table.setColumnCount(6)
        self.stores_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Location", "Manager ID", "Created At", "Action"]
        )
        self.stores_table.setColumnWidth(0, 50)
        self.stores_table.setColumnWidth(4, 150)
        self.stores_table.setColumnWidth(5, 150)

        self.populate_table()
        # Set the stretch factor of the table to make it expand vertically
        layout.addWidget(self.stores_table, 1)

        self.setLayout(layout)
        self.add_store_button.clicked.connect(self.open_add_store_dialog)

    def populate_table(self):
        stores_data = self.store_manager.get_stores_data()
        self.stores_table.setRowCount(len(stores_data))

        for i, store in enumerate(stores_data):
            self.stores_table.setItem(i, 0, QTableWidgetItem(str(store["id"])))
            self.stores_table.setItem(i, 1, QTableWidgetItem(store["name"]))
            self.stores_table.setItem(i, 2, QTableWidgetItem(store["location"]))
            self.stores_table.setItem(i, 3, QTableWidgetItem(str(store["manager_id"])))
            self.stores_table.setItem(i, 4, QTableWidgetItem(store["created_at"]))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")
            edit_button.clicked.connect(lambda _, s=store["id"]: self.edit_store(s))
            delete_button.clicked.connect(lambda _, s=store["id"]: self.delete_store(s))
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            self.stores_table.setCellWidget(i, 5, action_widget)

    def open_add_store_dialog(self):
        dialog = AddStoreDialog(self.store_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            name, location, manager_id = dialog.get_store_data()
            if name and location and manager_id is not None:
                self.add_new_store(name, location, manager_id)
            else:
                logger.warning("Add store dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def add_new_store(self, name, location, manager_id):
        if self.store_manager.save_stores(name, location, manager_id):
            self.populate_table()
            QMessageBox.information(self, "Success", "Store added successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to add store.")

    def edit_store(self, store_id):
        dialog = AddStoreDialog(self.store_manager, self)
        dialog.setWindowTitle("Edit Store")
        dialog.setMinimumSize(400, 200)
        stores = self.store_manager.get_stores_data()
        store = next(s for s in stores if s["id"] == store_id)
        dialog.name_input.setText(store["name"])
        dialog.location_input.setText(store["location"])
        index = dialog.manager_combo.findData(store["manager_id"])
        if index >= 0:
            dialog.manager_combo.setCurrentIndex(index)
        else:
            logger.warning(
                f"Manager ID {store['manager_id']} not found in dropdown for edit."
            )
            dialog.manager_combo.addItem(
                f"Unknown Manager ({store['manager_id']})", store["manager_id"]
            )

        if dialog.exec_() == QDialog.Accepted:
            name, location, manager_id = dialog.get_store_data()
            if name and location and manager_id is not None:
                if self.store_manager.update_stores(
                    store_id, name, location, manager_id
                ):
                    self.populate_table()
                    QMessageBox.information(
                        self, "Success", "Store updated successfully!"
                    )
                else:
                    QMessageBox.critical(self, "Error", "Failed to update store.")
            else:
                logger.warning("Edit store dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def delete_store(self, store_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this store?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.store_manager.delete_stores(store_id):
                self.populate_table()
                QMessageBox.information(self, "Success", "Store deleted successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete store.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StoresView()
    window.showMaximized()
    sys.exit(app.exec_())
