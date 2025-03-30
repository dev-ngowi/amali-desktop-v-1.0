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

from Application.Components.Inventory.ItemGroup.model import ItemGroupManager


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AddItemGroupDialog(QDialog):
    def __init__(self, item_group_manager, parent=None):
        super().__init__(parent)
        self.item_group_manager = item_group_manager
        self.setWindowTitle("Add New Item Group")
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

    def get_item_group_data(self):
        return self.name_input.text()


class ItemGroupView(QWidget):
    def __init__(self):
        super().__init__()
        self.item_group_manager = ItemGroupManager()

        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        title_label = QLabel("Item Groups")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        self.add_new_item_group = QPushButton("Add New Item Group")
        header_layout.addWidget(self.add_new_item_group)
        layout.addLayout(header_layout)

        self.item_group_table = QTableWidget()
        self.item_group_table.setColumnCount(4)
        self.item_group_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Created At", "Action"]
        )
        self.item_group_table.setColumnWidth(0, 50)
        self.item_group_table.setColumnWidth(3, 150)

        self.populate_table()
        layout.addWidget(self.item_group_table, 1)

        self.setLayout(layout)
        self.add_new_item_group.clicked.connect(self.open_add_item_group_dialog)

    def populate_table(self):
        item_group_data = self.item_group_manager.get_item_groups()
        self.item_group_table.setRowCount(len(item_group_data))
        self.item_group_table.setColumnCount(4)  # Ensure correct column count

        for i, item_group in enumerate(item_group_data):
            self.item_group_table.setItem(i, 0, QTableWidgetItem(str(item_group["id"])))
            self.item_group_table.setItem(i, 1, QTableWidgetItem(item_group["name"]))
            self.item_group_table.setItem(
                i, 2, QTableWidgetItem(str(item_group["created_at"]))
            )

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")
            edit_button.clicked.connect(
                lambda _, ig=item_group["id"]: self.edit_item_group(ig)
            )
            delete_button.clicked.connect(
                lambda _, ig=item_group["id"]: self.delete_item_group(ig)
            )
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            self.item_group_table.setCellWidget(i, 3, action_widget)

    def open_add_item_group_dialog(self):
        dialog = AddItemGroupDialog(self.item_group_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_item_group_data()
            if name:
                self.add_new_item_group_func(name)
            else:
                logger.warning("Add item group dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def add_new_item_group_func(self, name):
        if self.item_group_manager.save_item_group(name):
            self.populate_table()
            QMessageBox.information(self, "Success", "Item group added successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to add item group.")

    def edit_item_group(self, item_group_id):
        dialog = AddItemGroupDialog(self.item_group_manager, self)
        dialog.setWindowTitle("Edit Item Group")
        dialog.setMinimumSize(400, 150)
        item_groups = self.item_group_manager.get_item_groups()
        item_group = next(ig for ig in item_groups if ig["id"] == item_group_id)
        dialog.name_input.setText(item_group["name"])

        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_item_group_data()
            if name:
                if self.item_group_manager.update_item_group(item_group_id, name):
                    self.populate_table()
                    QMessageBox.information(
                        self, "Success", "Item group updated successfully!"
                    )
                else:
                    QMessageBox.critical(self, "Error", "Failed to update item group.")
            else:
                logger.warning("Edit item group dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def delete_item_group(self, item_group_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this item group?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.item_group_manager.delete_item_group(item_group_id):
                self.populate_table()
                QMessageBox.information(
                    self, "Success", "Item group deleted successfully!"
                )
            else:
                QMessageBox.critical(self, "Error", "Failed to delete item group.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ItemGroupView()
    window.showMaximized()
    sys.exit(app.exec_())