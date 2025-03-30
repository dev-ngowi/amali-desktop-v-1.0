# view.py
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
    QMessageBox,
)
from PyQt5.QtCore import Qt

from Application.Components.Inventory.ItemType.model import ItemTypeManager


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)



class AddItemTypeDialog(QDialog):
    def __init__(self, item_type_manager, parent=None):
        super().__init__(parent)
        self.item_type_manager = item_type_manager
        self.setWindowTitle("Add New Item Type")
        self.setMinimumSize(400, 150)
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()

        self.layout.addRow(QLabel("Name:"), self.name_input)

        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addRow(self.buttons_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_item_type_data(self):
        return self.name_input.text()


class ItemTypeView(QWidget):
    def __init__(self):
        super().__init__()
        self.item_type_manager = ItemTypeManager()
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        title_label = QLabel("Item Types")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        self.add_new_item_type = QPushButton("Add New Item Type")
        header_layout.addWidget(self.add_new_item_type)
        layout.addLayout(header_layout)

        self.item_type_table = QTableWidget()
        self.item_type_table.setColumnCount(4)
        self.item_type_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Created At", "Action"]
        )
        self.item_type_table.setColumnWidth(0, 50)
        self.item_type_table.setColumnWidth(3, 150)

        self.populate_table()
        layout.addWidget(self.item_type_table, 1)

        self.setLayout(layout)
        self.add_new_item_type.clicked.connect(self.open_add_item_type_dialog)

    def populate_table(self):
        item_type_data = self.item_type_manager.get_item_types()
        self.item_type_table.setRowCount(len(item_type_data))
        self.item_type_table.setColumnCount(4)  # Ensure correct column count

        for i, item_type in enumerate(item_type_data):
            self.item_type_table.setItem(i, 0, QTableWidgetItem(str(item_type["id"])))
            self.item_type_table.setItem(i, 1, QTableWidgetItem(item_type["name"]))
            self.item_type_table.setItem(
                i, 2, QTableWidgetItem(str(item_type["created_at"]))
            )

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")
            edit_button.clicked.connect(
                lambda _, it=item_type["id"]: self.edit_item_type(it)
            )
            delete_button.clicked.connect(
                lambda _, it=item_type["id"]: self.delete_item_type(it)
            )
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            self.item_type_table.setCellWidget(i, 3, action_widget)

    def open_add_item_type_dialog(self):
        dialog = AddItemTypeDialog(self.item_type_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_item_type_data()
            if name:
                self.add_new_item_type_func(name)
            else:
                logger.warning("Add item type dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def add_new_item_type_func(self, name):
        if self.item_type_manager.save_item_type(name):
            self.populate_table()
            QMessageBox.information(self, "Success", "Item type added successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to add item type.")

    def edit_item_type(self, item_type_id):
        dialog = AddItemTypeDialog(self.item_type_manager, self)
        dialog.setWindowTitle("Edit Item Type")
        dialog.setMinimumSize(400, 150)
        item_types = self.item_type_manager.get_item_types()
        item_type = next(it for it in item_types if it["id"] == item_type_id)
        dialog.name_input.setText(item_type["name"])

        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_item_type_data()
            if name:
                if self.item_type_manager.update_item_type(item_type_id, name):
                    self.populate_table()
                    QMessageBox.information(
                        self, "Success", "Item type updated successfully!"
                    )
                else:
                    QMessageBox.critical(self, "Error", "Failed to update item type.")
            else:
                logger.warning("Edit item type dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def delete_item_type(self, item_type_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this item type?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.item_type_manager.delete_item_type(item_type_id):
                self.populate_table()
                QMessageBox.information(
                    self, "Success", "Item type deleted successfully!"
                )
            else:
                QMessageBox.critical(self, "Error", "Failed to delete item type.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    item_type_window = ItemTypeView()
    item_type_window.setWindowTitle("Item Types")
    item_type_window.show() # Or showMaximized()

    sys.exit(app.exec_())