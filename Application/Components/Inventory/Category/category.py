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

from Application.Components.Inventory.Category.model import CategoryManager


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AddCategoryDialog(QDialog):
    def __init__(self, category_manager, parent=None):
        super().__init__(parent)
        self.category_manager = category_manager
        self.setWindowTitle("Add New Category")
        self.setMinimumSize(400, 200)
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.item_group_combo = QComboBox()

        item_groups = self.category_manager.get_item_groups()
        if not item_groups:
            logger.warning("No Item group available to populate dropdown.")
            self.item_group_combo.addItem("No Item group available", None)
            QMessageBox.warning(self, "Warning", "No Item group found in the database.")
        else:
            for item_group in item_groups:
                self.item_group_combo.addItem(item_group["name"], item_group["id"])
            logger.info("Item group  dropdown populated successfully.")

        self.layout.addRow(QLabel("Name:"), self.name_input)
        self.layout.addRow(QLabel("Item Groups:"), self.item_group_combo)

        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addRow(self.buttons_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_categories_data(self):
        item_group_id = self.item_group_combo.currentData()
        if item_group_id is None:
            logger.error("No valid item group selected.")
            return None, None
        return (
            self.name_input.text(),
            item_group_id,
        )


class CategoriesView(QWidget):
    def __init__(self):
        super().__init__()
        self.category_manager = CategoryManager()

        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        title_label = QLabel("Categories")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        self.add_new_category = QPushButton("Add New Category")
        header_layout.addWidget(self.add_new_category)
        layout.addLayout(header_layout)

        self.category_table = QTableWidget()
        self.category_table.setColumnCount(5)
        self.category_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Item Group", "Created At", "Action"]
        )
        self.category_table.setColumnWidth(0, 50)
        self.category_table.setColumnWidth(4, 150)

        self.populate_table()
        layout.addWidget(self.category_table, 1)

        self.setLayout(layout)
        self.add_new_category.clicked.connect(self.open_add_category_dialog)

    def populate_table(self):
        category_data = self.category_manager.get_categories_data()
        self.category_table.setRowCount(len(category_data))

        for i, category in enumerate(category_data):
            self.category_table.setItem(i, 0, QTableWidgetItem(str(category["id"])))
            self.category_table.setItem(i, 1, QTableWidgetItem(category["name"]))
            self.category_table.setItem(
                i, 2, QTableWidgetItem(category["item_group_id"])
            )
            self.category_table.setItem(i, 3, QTableWidgetItem(category["created_at"]))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")
            edit_button.clicked.connect(
                lambda _, c=category["id"]: self.edit_category(c)
            )
            delete_button.clicked.connect(
                lambda _, c=category["id"]: self.delete_category(c)
            )
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            self.category_table.setCellWidget(i, 4, action_widget)

    def open_add_category_dialog(self):
        dialog = AddCategoryDialog(self.category_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            name, item_group_id = dialog.get_categories_data()
            if name and item_group_id is not None:
                self.add_new_category_func(name, item_group_id)
            else:
                logger.warning("Add category dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def add_new_category_func(self, name, item_group_id):
        if self.category_manager.save_categories(name, item_group_id):
            self.populate_table()
            QMessageBox.information(self, "Success", "Category added successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to add category.")

    def edit_category(self, category_id):
        dialog = AddCategoryDialog(self.category_manager, self)
        dialog.setWindowTitle("Edit Category")
        dialog.setMinimumSize(400, 200)
        categories = self.category_manager.get_categories_data()
        category = next(c for c in categories if c["id"] == category_id)
        dialog.name_input.setText(category["name"])
        index = dialog.item_group_combo.findData(category["item_group_id"])
        if index >= 0:
            dialog.item_group_combo.setCurrentIndex(index)

        if dialog.exec_() == QDialog.Accepted:
            name, item_group_id = dialog.get_categories_data()
            if name and item_group_id is not None:
                if self.category_manager.update_categories(
                    category_id, name, item_group_id
                ):
                    self.populate_table()
                    QMessageBox.information(
                        self, "Success", "Category updated successfully!"
                    )
                else:
                    QMessageBox.critical(self, "Error", "Failed to update category.")
            else:
                logger.warning("Edit category dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def delete_category(self, category_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this category?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.category_manager.delete_categories(category_id):
                self.populate_table()
                QMessageBox.information(
                    self, "Success", "Category deleted successfully!"
                )
            else:
                QMessageBox.critical(self, "Error", "Failed to delete category.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CategoriesView()
    window.showMaximized()
    sys.exit(app.exec_())
