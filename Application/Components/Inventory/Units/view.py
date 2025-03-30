import sys
import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from Application.Components.Inventory.Units.model import UnitManager


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AddUnitDialog(QDialog):
    def __init__(self, unit_manager, parent=None):
        super().__init__(parent)
        self.unit_manager = unit_manager
        self.setWindowTitle("Add New Unit")
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

    def get_unit_data(self):
        return self.name_input.text()


class UnitView(QWidget):
    def __init__(self):
        super().__init__()
        self.unit_manager = UnitManager()

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)  # Set layout immediately to ensure proper resizing

        # Header layout
        header_layout = QHBoxLayout()
        title_label = QLabel("Units")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)  # Push button to the right
        self.add_new_unit = QPushButton("Add New Unit")
        header_layout.addWidget(self.add_new_unit)
        layout.addLayout(header_layout)

        # Table setup
        self.unit_table = QTableWidget()
        self.unit_table.setColumnCount(4)
        self.unit_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Created At", "Action"]
        )

        # Set size policy to expanding
        self.unit_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Stretch table columns to fill width
        self.unit_table.horizontalHeader().setStretchLastSection(True)
        self.unit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Add table to layout with stretch factor
        layout.addWidget(self.unit_table, 1)  # Stretch factor of 1 to fill available space

        # Populate table
        self.populate_table()

        # Connect signals
        self.add_new_unit.clicked.connect(self.open_add_unit_dialog)

    def populate_table(self):
        unit_data = self.unit_manager.get_units()
        self.unit_table.setRowCount(len(unit_data))

        for i, unit in enumerate(unit_data):
            self.unit_table.setItem(i, 0, QTableWidgetItem(str(unit["id"])))
            self.unit_table.setItem(i, 1, QTableWidgetItem(unit["name"]))
            self.unit_table.setItem(i, 2, QTableWidgetItem(str(unit["created_at"])))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")
            edit_button.clicked.connect(lambda _, u=unit["id"]: self.edit_unit(u))
            delete_button.clicked.connect(lambda _, u=unit["id"]: self.delete_unit(u))
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            self.unit_table.setCellWidget(i, 3, action_widget)

    def open_add_unit_dialog(self):
        dialog = AddUnitDialog(self.unit_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_unit_data()
            if name:
                self.add_new_unit_func(name)
            else:
                logger.warning("Add unit dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def add_new_unit_func(self, name):
        if self.unit_manager.save_unit(name):
            self.populate_table()
            QMessageBox.information(self, "Success", "Unit added successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to add unit.")

    def edit_unit(self, unit_id):
        dialog = AddUnitDialog(self.unit_manager, self)
        dialog.setWindowTitle("Edit Unit")
        dialog.setMinimumSize(400, 150)
        units = self.unit_manager.get_units()
        unit = next(u for u in units if u["id"] == unit_id)
        dialog.name_input.setText(unit["name"])

        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_unit_data()
            if name:
                if self.unit_manager.update_unit(unit_id, name):
                    self.populate_table()
                    QMessageBox.information(
                        self, "Success", "Unit updated successfully!"
                    )
                else:
                    QMessageBox.critical(self, "Error", "Failed to update unit.")
            else:
                logger.warning("Edit unit dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def delete_unit(self, unit_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this unit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.unit_manager.delete_unit(unit_id):
                self.populate_table()
                QMessageBox.information(self, "Success", "Unit deleted successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete unit.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    unit_window = UnitView()
    unit_window.setWindowTitle("Units")
    unit_window.show()

    sys.exit(app.exec_())
