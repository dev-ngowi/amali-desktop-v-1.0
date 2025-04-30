import sys
import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from Application.Components.Inventory.Items.model import ItemManager
from Application.Components.Inventory.Items.register import AddItemWindow
from Application.Components.Inventory.Items.update import EditItemWindow

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ItemsView(QWidget):
    def __init__(self, item_manager=None):
        super().__init__()
        self.item_manager = item_manager or ItemManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header layout with search
        header_layout = QHBoxLayout()
        title_label = QLabel("Items")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or barcode...")
        self.search_input.textChanged.connect(self.search_items)
        self.search_input.setMaximumWidth(300)
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """
        )
        header_layout.addWidget(self.search_input)

        header_layout.addStretch(1)

        # Styled Add New Item button
        self.add_new_item = QPushButton("Add New Item")
        self.add_new_item.clicked.connect(self.open_add_item_window)
        self.add_new_item.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """
        )
        header_layout.addWidget(self.add_new_item)
        layout.addLayout(header_layout)

        self.item_table = QTableWidget()
        self.item_table.setColumnCount(5)
        self.item_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Barcode", "Created At", "Action"]
        )

        # Set size policy to expanding
        self.item_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.item_table.horizontalHeader().setStretchLastSection(True)
        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.item_table.setColumnWidth(0, 50)
        self.item_table.setColumnWidth(2, 150)
        self.item_table.setColumnWidth(3, 150)
        self.item_table.setColumnWidth(4, 150)
        layout.addWidget(self.item_table, 1)

        self.setLayout(layout)
        self.populate_table()

    def populate_table(self, search_query=None):
        items_result = self.item_manager.list_items()
        if not items_result["success"]:
            logger.error(f"Failed to fetch items: {items_result['message']}")
            QMessageBox.critical(self, "Error", "Failed to load items")
            return

        item_data = items_result["data"]
        # Deduplicate items by barcode
        seen_barcodes = set()
        unique_items = []

        for item in item_data:
            barcode = item.get("barcode", "")
            if barcode not in seen_barcodes:
                seen_barcodes.add(barcode)
                # Apply search filter if query exists
                if search_query:
                    search_query = search_query.lower()
                    if (
                        search_query in item["name"].lower()
                        or search_query in item.get("barcode", "").lower()
                    ):
                        unique_items.append(item)
                else:
                    unique_items.append(item)

        self.item_table.setRowCount(len(unique_items))

        for i, item in enumerate(unique_items):
            self.item_table.setItem(i, 0, QTableWidgetItem(str(item["id"])))
            self.item_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            self.item_table.setItem(i, 2, QTableWidgetItem(item.get("barcode", "")))
            self.item_table.setItem(i, 3, QTableWidgetItem(str(item["created_at"])))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")
            edit_button.clicked.connect(
                lambda _, it=item["id"]: self.open_edit_item_window(it)
            )
            delete_button.clicked.connect(lambda _, it=item["id"]: self.delete_item(it))
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.setContentsMargins(0, 0, 0, 0)
            self.item_table.setCellWidget(i, 4, action_widget)

    def search_items(self, text):
        """Filter items based on search input"""
        self.populate_table(search_query=text)

    def open_add_item_window(self):
        self.add_window = AddItemWindow(self.item_manager, parent=self)
        self.add_window.setModal(True)
        self.add_window.show()

    def open_edit_item_window(self, item_id):
        self.edit_window = EditItemWindow(
            self.item_manager, parent=self, item_id=item_id
        )
        self.edit_window.setModal(True)
        self.edit_window.show()

    def delete_item(self, item_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this item?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            result = self.item_manager.delete_item(item_id)
            if result["success"]:
                self.populate_table()
                QMessageBox.information(self, "Success", result["message"])
            else:
                QMessageBox.critical(self, "Error", result["message"])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ItemsView()
    window.setWindowTitle("Items")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
