import sys
import logging
import sqlite3
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

from Application.Components.Settings.Payments.modal import PaymentsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AddPaymentDialog(QDialog):
    def __init__(self, payments_manager, parent=None):
        super().__init__(parent)
        self.payments_manager = payments_manager
        self.setWindowTitle("Add New Payment")
        self.setMinimumSize(400, 200)
        self.layout = QFormLayout(self)

        self.short_code_input = QLineEdit()
        self.payment_method_input = QLineEdit()
        self.payment_type_combo = QComboBox()

        # Populate the combo box with payment types
        payment_types = self.payments_manager.get_payment_types()
        if not payment_types:
            logger.warning("No payment types available.")
            self.payment_type_combo.addItem("No payment types available", None)
            QMessageBox.warning(self, "Warning", "No payment types found in the database.")
        else:
            for pt in payment_types:
                self.payment_type_combo.addItem(pt["name"], pt["id"])
            logger.info("Payment type dropdown populated successfully.")

        self.layout.addRow(QLabel("Short Code:"), self.short_code_input)
        self.layout.addRow(QLabel("Payment Method:"), self.payment_method_input)
        self.layout.addRow(QLabel("Payment Type:"), self.payment_type_combo)

        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addRow(self.buttons_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_payment_data(self):
        payment_type_id = self.payment_type_combo.currentData()
        if payment_type_id is None:
            logger.error("No valid payment type selected.")
            return None, None, None
        return (
            self.short_code_input.text(),
            self.payment_method_input.text(),
            payment_type_id,
        )


class PaymentsMainView(QWidget):
    def __init__(self):
        super().__init__()
        self.payments_manager = PaymentsManager()

        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        title_label = QLabel("Payments")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        self.add_payment_button = QPushButton("Add New Payment")
        header_layout.addWidget(self.add_payment_button)
        layout.addLayout(header_layout)

        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(5)
        self.payments_table.setHorizontalHeaderLabels(
            ["ID", "Short Code", "Payment Method", "Created At", "Action"]
        )
        self.payments_table.setColumnWidth(0, 50)
        self.payments_table.setColumnWidth(4, 150)
        self.payments_table.setColumnWidth(5, 150)

        self.populate_table()
        layout.addWidget(self.payments_table, 1)

        self.setLayout(layout)
        self.add_payment_button.clicked.connect(self.open_add_payment_dialog)

    def populate_table(self):
        payments_data = self.payments_manager.get_payments_data()
        self.payments_table.setRowCount(len(payments_data))

        for i, payment in enumerate(payments_data):
            self.payments_table.setItem(i, 0, QTableWidgetItem(str(payment["id"])))
            self.payments_table.setItem(i, 1, QTableWidgetItem(payment["short_code"]))
            self.payments_table.setItem(i, 2, QTableWidgetItem(payment["payment_method"]))
            self.payments_table.setItem(i, 4, QTableWidgetItem(payment["created_at"]))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")
            edit_button.clicked.connect(lambda _, p=payment["id"]: self.edit_payment(p))
            delete_button.clicked.connect(lambda _, p=payment["id"]: self.delete_payment(p))
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            self.payments_table.setCellWidget(i, 5, action_widget)

    def open_add_payment_dialog(self):
        dialog = AddPaymentDialog(self.payments_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            short_code, payment_method, payment_type_id = dialog.get_payment_data()
            if short_code and payment_method and payment_type_id is not None:
                self.add_new_payment(short_code, payment_method, payment_type_id)
            else:
                logger.warning("Add payment dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def add_new_payment(self, short_code, payment_method, payment_type_id):
        if self.payments_manager.save_payment(short_code, payment_method, payment_type_id):
            self.populate_table()
            QMessageBox.information(self, "Success", "Payment added successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to add payment.")

    def edit_payment(self, payment_id):
        dialog = AddPaymentDialog(self.payments_manager, self)
        dialog.setWindowTitle("Edit Payment")
        dialog.setMinimumSize(400, 200)
        payments = self.payments_manager.get_payments_data()
        payment = next(p for p in payments if p["id"] == payment_id)
        dialog.short_code_input.setText(payment["short_code"])
        dialog.payment_method_input.setText(payment["payment_method"])
        index = dialog.payment_type_combo.findData(payment["payment_type_id"])
        if index >= 0:
            dialog.payment_type_combo.setCurrentIndex(index)
        else:
            logger.warning(
                f"Payment Type ID {payment['payment_type_id']} not found in dropdown for edit."
            )
            # Fetch payment type name if ID is not in the current list
            payment_type = self.payments_manager.get_payment_type(payment["payment_type_id"])
            if payment_type:
                dialog.payment_type_combo.addItem(f"{payment_type['name']} (ID: {payment['payment_type_id']})", payment["payment_type_id"])
            else:
                dialog.payment_type_combo.addItem(f"Unknown Payment Type (ID: {payment['payment_type_id']})", payment["payment_type_id"])
            dialog.payment_type_combo.setCurrentIndex(dialog.payment_type_combo.count() - 1)


        if dialog.exec_() == QDialog.Accepted:
            short_code, payment_method, payment_type_id = dialog.get_payment_data()
            if short_code and payment_method and payment_type_id is not None:
                if self.payments_manager.update_payment(
                    payment_id, short_code, payment_method, payment_type_id
                ):
                    self.populate_table()
                    QMessageBox.information(
                        self, "Success", "Payment updated successfully!"
                    )
                else:
                    QMessageBox.critical(self, "Error", "Failed to update payment.")
            else:
                logger.warning("Edit payment dialog rejected or invalid data.")
                QMessageBox.warning(
                    self, "Warning", "Please fill in all fields correctly."
                )

    def delete_payment(self, payment_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this payment?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if self.payments_manager.delete_payment(payment_id):
                self.populate_table()
                QMessageBox.information(self, "Success", "Payment deleted successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete payment.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PaymentsMainView()
    window.showMaximized()
    sys.exit(app.exec_())