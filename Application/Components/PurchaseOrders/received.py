import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import logging
from datetime import datetime

from Application.Components.PurchaseOrders.model import PurchaseOrderManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReceivePurchaseOrder(QDialog):
    def __init__(self, po_manager, po_id, parent=None):
        super().__init__(parent)
        self.po_manager = po_manager
        self.po_id = po_id
        self.items_data = []
        self.setWindowTitle(f"Receive Purchase Order - ID: {po_id}")
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.load_po_data()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # GRN Info
        self.layout.addWidget(
            QLabel(f"Goods Received Note (GRN) for PO ID: {self.po_id}")
        )

        form_layout = QFormLayout()
        self.delivery_note_input = QLineEdit()
        self.received_date_input = QDateEdit()
        self.received_date_input.setDate(QDate.currentDate())
        self.remarks_input = QTextEdit()
        self.remarks_input.setMaximumHeight(50)

        # Add store location selector
        self.store_combo = QComboBox()
        self.load_store_locations()

        form_layout.addRow("Delivery Note #:", self.delivery_note_input)
        form_layout.addRow("Received Date:", self.received_date_input)
        form_layout.addRow("Store Location:", self.store_combo)
        form_layout.addRow("Remarks:", self.remarks_input)
        self.layout.addLayout(form_layout)

        # Items Table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(
            [
                "Item",
                "Ordered Qty",
                "Received Qty",
                "Accepted Qty",
                "Rejected Qty",
                "Unit Price",
                "Condition",
            ]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.items_table)

        # Buttons
        button_layout = QHBoxLayout()
        self.confirm_btn = QPushButton("Confirm Receipt")
        self.confirm_btn.clicked.connect(self.confirm_receipt)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(self.confirm_btn)
        button_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)

    def load_store_locations(self):
        try:
            stores = self.po_manager.get_stores()
            if not stores:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No store locations found. Please configure stores first.",
                )
                self.close()
                return
            for store in stores:
                self.store_combo.addItem(store["name"], store["id"])
            self.store_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error loading store locations: {str(e)}")
            QMessageBox.critical(
                self, "Error", f"Failed to load store locations: {str(e)}"
            )
            self.close()

    def load_po_data(self):
        try:
            po = self.po_manager.get_purchase_order(self.po_id)
            if not po:
                QMessageBox.warning(self, "Error", "Purchase order not found")
                self.close()
                return

            self.items_data = po["items"]
            self.items_table.setRowCount(len(self.items_data))

            for row, item in enumerate(self.items_data):
                self.items_table.setItem(row, 0, QTableWidgetItem(item["item_name"]))
                self.items_table.item(row, 0).setFlags(Qt.ItemIsEnabled)
                ordered_qty = QTableWidgetItem(f"{item['quantity']:.2f}")
                ordered_qty.setFlags(Qt.ItemIsEnabled)
                self.items_table.setItem(row, 1, ordered_qty)
                received_qty = QDoubleSpinBox()
                received_qty.setMaximum(item["quantity"])
                received_qty.setValue(item["quantity"])
                self.items_table.setCellWidget(row, 2, received_qty)
                accepted_qty = QDoubleSpinBox()
                accepted_qty.setMaximum(item["quantity"])
                accepted_qty.setValue(item["quantity"])
                self.items_table.setCellWidget(row, 3, accepted_qty)
                rejected_qty = QDoubleSpinBox()
                rejected_qty.setMaximum(item["quantity"])
                rejected_qty.setValue(0.0)
                self.items_table.setCellWidget(row, 4, rejected_qty)
                unit_price = QTableWidgetItem(f"{item['unit_price']:.2f}")
                unit_price.setFlags(Qt.ItemIsEnabled)
                self.items_table.setItem(row, 5, unit_price)
                condition = QComboBox()
                condition.addItems(["Good", "Damaged", "Defective"])
                self.items_table.setCellWidget(row, 6, condition)

        except Exception as e:
            logger.error(f"Error loading PO data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load PO data: {str(e)}")

    def confirm_receipt(self):
        try:
            # Validate inputs
            received_items = []
            for row in range(self.items_table.rowCount()):
                item = self.items_data[row]
                received_qty = self.items_table.cellWidget(row, 2).value()
                accepted_qty = self.items_table.cellWidget(row, 3).value()
                rejected_qty = self.items_table.cellWidget(row, 4).value()
                condition = self.items_table.cellWidget(row, 6).currentText()

                if accepted_qty + rejected_qty > received_qty:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        f"Sum of accepted and rejected quantities exceeds received quantity for {item['item_name']}",
                    )
                    return

                received_items.append(
                    {
                        "purchase_order_item_id": item.get("id"),
                        "item_id": item.get("item_id"),
                        "ordered_quantity": item["quantity"],
                        "received_quantity": received_qty,
                        "accepted_quantity": accepted_qty,
                        "rejected_quantity": rejected_qty,
                        "unit_price": item["unit_price"],
                        "received_condition": condition,
                    }
                )

            # Prepare GRN data
            po_data = self.po_manager.get_purchase_order(self.po_id)
            grn_data = {
                "purchase_order_id": self.po_id,
                "supplier_id": po_data["supplier_id"],
                "received_by": 1,  # Replace with actual user ID if available
                "received_date": self.received_date_input.date().toString("yyyy-MM-dd"),
                "delivery_note_number": self.delivery_note_input.text() or None,
                "status": "Completed",
                "remarks": self.remarks_input.toPlainText() or None,
                "items": received_items,
            }

            # Create GRN
            grn_result = self.po_manager.create_grn(**grn_data)

            # Update PO status
            self.po_manager.update_purchase_order(self.po_id, status="Received")

            # Update stock for each item with the selected store_id
            store_id = self.store_combo.currentData()
            if not store_id:
                raise ValueError("No store location selected")

            for item in received_items:
                stock_id = self.po_manager.get_stock_id(item["item_id"], store_id)
                self.po_manager.update_stock_from_grn(
                    grn_result["id"], stock_id=stock_id
                )

            QMessageBox.information(
                self, "Success", f"GRN {grn_result['grn_number']} created successfully"
            )
            self.close()

        except Exception as e:
            logger.error(f"Error confirming receipt: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to confirm receipt: {str(e)}")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    po_manager = PurchaseOrderManager()
    window = ReceivePurchaseOrder(po_manager, 1)
    window.show()
    sys.exit(app.exec_())
