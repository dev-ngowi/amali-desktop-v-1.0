import sys
import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from Application.Components.PurchaseOrders.invoice import PurchaseOrderInvoice
from Application.Components.PurchaseOrders.model import PurchaseOrderManager
from Application.Components.PurchaseOrders.register import AddPurchaseOrderWindow
from Application.Components.PurchaseOrders.update import EditPurchaseOrderWindow
from Application.Components.PurchaseOrders.received import ReceivePurchaseOrder
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PurchaseOrderView(QWidget):
    def __init__(self, po_manager=None):
        super().__init__()
        self.po_manager = po_manager or PurchaseOrderManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header with filter
        header_layout = QHBoxLayout()
        title_label = QLabel("Purchase Orders")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)

        # Date Filter
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())  # Default to today
        self.date_filter.dateChanged.connect(self.filter_by_date)
        header_layout.addWidget(QLabel("Filter by Date:"))
        header_layout.addWidget(self.date_filter)

        header_layout.addStretch(1)
        self.add_new_po = QPushButton("Add New Purchase Order")
        self.add_new_po.clicked.connect(self.open_add_po_window)
        header_layout.addWidget(self.add_new_po)
        layout.addLayout(header_layout)

        self.po_table = QTableWidget()
        self.po_table.setColumnCount(7)
        self.po_table.setHorizontalHeaderLabels(
            [
                "Order Number",
                "Supplier",
                "Order Date",
                "Status",
                "Total Amount",
                "Currency",
                "Action",
            ]
        )
        self.po_table.horizontalHeader().setStretchLastSection(True)
        self.po_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.po_table, 1)

        self.filter_by_date()  # Populate with today's POs by default

    def populate_table(self, po_data):
        try:
            self.po_table.setRowCount(len(po_data))

            for row, po in enumerate(po_data):
                self.po_table.setItem(row, 0, QTableWidgetItem(po["order_number"]))
                self.po_table.setItem(row, 1, QTableWidgetItem(po["supplier_name"]))
                self.po_table.setItem(row, 2, QTableWidgetItem(po["order_date"]))
                self.po_table.setItem(row, 3, QTableWidgetItem(po["status"]))
                self.po_table.setItem(row, 4, QTableWidgetItem(str(po["total_amount"])))
                self.po_table.setItem(row, 5, QTableWidgetItem(po["currency"]))

                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)

                if po["status"] == "Pending":
                    edit_button = QPushButton("Edit")
                    delete_button = QPushButton("Cancel")
                    invoice_button = QPushButton("Invoice")

                    edit_button.clicked.connect(
                        lambda _, pid=po["id"]: self.open_edit_po_window(pid)
                    )
                    delete_button.clicked.connect(
                        lambda _, pid=po["id"]: self.delete_purchase_order(pid)
                    )
                    invoice_button.clicked.connect(
                        lambda _, pid=po["id"]: self.generate_invoice(pid)
                    )

                    action_layout.addWidget(edit_button)
                    action_layout.addWidget(delete_button)
                    action_layout.addWidget(invoice_button)
                elif po["status"] == "Approved":
                    receive_button = QPushButton("Receive")
                    receive_button.clicked.connect(
                        lambda _, pid=po["id"]: self.open_receive_window(pid)
                    )
                    action_layout.addWidget(receive_button)
                elif po["status"] == "Received":
                    completed_button = QPushButton("Completed")
                    completed_button.setEnabled(False)  # Disabled button
                    action_layout.addWidget(completed_button)

                action_layout.setAlignment(Qt.AlignCenter)
                action_layout.setContentsMargins(0, 0, 0, 0)
                self.po_table.setCellWidget(row, 6, action_widget)

        except Exception as e:
            logger.error(f"Failed to populate table: {str(e)}")
            QMessageBox.critical(
                self, "Error", f"Failed to load purchase orders: {str(e)}"
            )

    def filter_by_date(self):
        try:
            selected_date = self.date_filter.date().toString("yyyy-MM-dd")
            po_data = self.po_manager.list_purchase_orders()
            filtered_data = [po for po in po_data if po["order_date"] == selected_date]
            self.populate_table(filtered_data)
        except Exception as e:
            logger.error(f"Failed to filter purchase orders: {str(e)}")
            QMessageBox.critical(
                self, "Error", f"Failed to filter purchase orders: {str(e)}"
            )

    def open_add_po_window(self):
        self.add_window = AddPurchaseOrderWindow(self.po_manager, parent=self)
        self.add_window.po_added.connect(self.filter_by_date)
        self.add_window.setModal(True)
        self.add_window.show()

    def open_edit_po_window(self, po_id):
        self.edit_window = EditPurchaseOrderWindow(
            self.po_manager, parent=self, po_id=po_id
        )
        self.edit_window.po_updated.connect(self.filter_by_date)
        self.edit_window.setModal(True)
        self.edit_window.show()

    def delete_purchase_order(self, po_id):
        reply = QMessageBox.question(
            self,
            "Confirm Cancel",
            "Are you sure you want to cancel this purchase order?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                success = self.po_manager.delete_purchase_order(po_id)
                if success:
                    self.filter_by_date()
                    QMessageBox.information(
                        self, "Success", "Purchase order cancelled successfully"
                    )
                else:
                    QMessageBox.warning(
                        self, "Warning", "No purchase order was cancelled"
                    )
            except Exception as e:
                logger.error(f"Error cancelling purchase order: {str(e)}")
                QMessageBox.critical(
                    self, "Error", f"Failed to cancel purchase order: {str(e)}"
                )

    def generate_invoice(self, po_id):
        try:
            invoice_window = PurchaseOrderInvoice(self.po_manager, po_id, parent=self)
            invoice_window.show()
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate invoice: {str(e)}")

    def open_receive_window(self, po_id):
        self.receive_window = ReceivePurchaseOrder(self.po_manager, po_id, parent=self)
        self.receive_window.show()
        self.receive_window.finished.connect(
            self.filter_by_date
        )  # Refresh table after receiving


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PurchaseOrderView()
    window.setWindowTitle("Purchase Orders")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
