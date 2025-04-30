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
    QDateEdit,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, QDate

from Application.Components.Inventory.Expenses.model import ExpenseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AddExpenseDialog(QDialog):
    def __init__(self, expense_manager, parent=None, expense_data=None):
        super().__init__(parent)
        self.expense_manager = expense_manager
        self.setWindowTitle("Add New Expense" if not expense_data else "Edit Expense")
        self.setMinimumSize(700, 600)
        self.layout = QFormLayout(self)
        self.expense_id = None
        self.linked_items_prices = {}

        # Form fields
        self.expense_type_combo = QComboBox()
        self.expense_type_combo.addItems(["home", "shop"])
        self.user_combo = QComboBox()
        self.expense_date_edit = QDateEdit()
        self.expense_date_edit.setDate(QDate.currentDate())
        self.expense_date_edit.setCalendarPopup(True)
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.0, 1000000.0)
        self.amount_input.setDecimals(2)
        self.description_input = QLineEdit()
        self.reference_number_input = QLineEdit()
        self.receipt_path_input = QLineEdit()
        self.receipt_browse_button = QPushButton("Browse")
        self.linked_shop_items_list = QListWidget()
        self.linked_shop_items_list.itemChanged.connect(self.update_total_amount)

        # Populate user combo box
        users = self.expense_manager.get_users()
        for user in users:
            self.user_combo.addItem(user["username"], user["id"])

        # Populate linked shop items list with checkboxes
        items = self.expense_manager.get_items()
        for item in items:
            list_item = QListWidgetItem(item["name"])
            list_item.setData(Qt.UserRole, item["id"])
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Unchecked)
            self.linked_shop_items_list.addItem(list_item)
            price = self.expense_manager.get_item_price(item["id"])
            self.linked_items_prices[item["id"]] = price

        # Add fields to layout
        self.layout.addRow(QLabel("Expense Type:"), self.expense_type_combo)
        self.layout.addRow(QLabel("User:"), self.user_combo)
        self.layout.addRow(QLabel("Expense Date:"), self.expense_date_edit)
        self.layout.addRow(QLabel("Amount:"), self.amount_input)
        self.layout.addRow(QLabel("Description:"), self.description_input)
        self.layout.addRow(QLabel("Reference Number:"), self.reference_number_input)
        receipt_layout = QHBoxLayout()
        receipt_layout.addWidget(self.receipt_path_input)
        receipt_layout.addWidget(self.receipt_browse_button)
        self.layout.addRow(QLabel("Receipt Path:"), receipt_layout)
        self.layout.addRow(QLabel("Linked Shop Items:"), self.linked_shop_items_list)

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addRow(self.buttons_layout)

        # Connect signals
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.receipt_browse_button.clicked.connect(self.browse_receipt)

        # Load existing data if editing
        if expense_data:
            self.expense_id = expense_data["id"]
            self.expense_type_combo.setCurrentText(expense_data["expense_type"])
            user_index = self.user_combo.findData(expense_data["user_id"])
            if user_index >= 0:
                self.user_combo.setCurrentIndex(user_index)
            self.expense_date_edit.setDate(
                QDate.fromString(expense_data["expense_date"], "yyyy-MM-dd")
            )
            self.amount_input.setValue(expense_data["amount"])
            self.description_input.setText(expense_data["description"] or "")
            self.reference_number_input.setText(expense_data["reference_number"] or "")
            self.receipt_path_input.setText(expense_data["receipt_path"] or "")

            linked_item_ids = self.expense_manager.get_linked_item_ids(
                expense_data["id"]
            )
            total_price = 0.0
            for i in range(self.linked_shop_items_list.count()):
                item = self.linked_shop_items_list.item(i)
                item_id = item.data(Qt.UserRole)
                if item_id in linked_item_ids:
                    item.setCheckState(Qt.Checked)
                    total_price += self.linked_items_prices.get(item_id, 0.0)
            if not linked_item_ids:
                self.amount_input.setEnabled(True)
            else:
                self.amount_input.setValue(total_price)
                self.amount_input.setEnabled(False)

    def browse_receipt(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Receipt", "", "Images (*.png *.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            self.receipt_path_input.setText(file_path)

    def update_total_amount(self, item):
        total_price = 0.0
        selected_items = []
        for i in range(self.linked_shop_items_list.count()):
            list_item = self.linked_shop_items_list.item(i)
            if list_item.checkState() == Qt.Checked:
                item_id = list_item.data(Qt.UserRole)
                selected_items.append(item_id)
                total_price += self.linked_items_prices.get(item_id, 0.0)

        if selected_items:
            self.amount_input.setValue(total_price)
            self.amount_input.setEnabled(False)
        else:
            self.amount_input.setEnabled(True)
            self.amount_input.setValue(0.0)

    def get_expense_data(self):
        expense_type = self.expense_type_combo.currentText()
        user_id = self.user_combo.currentData()
        expense_date = self.expense_date_edit.date().toString("yyyy-MM-dd")
        amount = self.amount_input.value()
        description = self.description_input.text().strip() or None
        reference_number = self.reference_number_input.text().strip() or None
        receipt_path = self.receipt_path_input.text().strip() or None
        linked_shop_item_ids = [
            self.linked_shop_items_list.item(i).data(Qt.UserRole)
            for i in range(self.linked_shop_items_list.count())
            if self.linked_shop_items_list.item(i).checkState() == Qt.Checked
        ]

        # Validation
        if not user_id:
            QMessageBox.warning(self, "Warning", "Please select a valid user.")
            return None
        if amount <= 0 and not linked_shop_item_ids:
            QMessageBox.warning(
                self,
                "Warning",
                "Please enter an amount greater than 0 or select linked items.",
            )
            return None

        return (
            expense_type,
            user_id,
            expense_date,
            amount,
            description,
            reference_number,
            receipt_path,
            linked_shop_item_ids or None,  # Convert empty list to None
        )


class ExpensesView(QWidget):
    def __init__(self):
        super().__init__()
        self.expense_manager = ExpenseManager()

        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Expenses")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        self.add_expense_button = QPushButton("Add New Expense")
        header_layout.addWidget(self.add_expense_button)
        layout.addLayout(header_layout)

        # Financials display
        self.financials_label = QLabel(
            "Daily Financials: Orders: 0.0, Expenses: 0.0, After Expenses: 0.0"
        )
        self.financials_label.setStyleSheet("font-size: 14px; color: #333;")
        layout.addWidget(self.financials_label)

        # Expenses table
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(7)
        self.expenses_table.setHorizontalHeaderLabels(
            [
                "Type",
                "Amount",
                "Description",
                "Reference",
                "Receipt",
                "Linked Items",
                "Action",
            ]
        )
        self.expenses_table.setColumnWidth(0, 80)
        self.expenses_table.setColumnWidth(1, 100)
        self.expenses_table.setColumnWidth(2, 150)
        self.expenses_table.setColumnWidth(3, 100)
        self.expenses_table.setColumnWidth(4, 150)
        self.expenses_table.setColumnWidth(5, 200)
        self.expenses_table.setColumnWidth(6, 150)

        self.populate_table()
        layout.addWidget(self.expenses_table, 1)

        self.setLayout(layout)
        self.add_expense_button.clicked.connect(self.open_add_expense_dialog)

        # Initial financials update
        self.update_financials_display(QDate.currentDate().toString("yyyy-MM-dd"))

    def populate_table(self):
        expenses_data = self.expense_manager.get_expenses_data()
        self.expenses_table.setRowCount(len(expenses_data))

        for i, expense in enumerate(expenses_data):
            self.expenses_table.setItem(i, 0, QTableWidgetItem(expense["expense_type"]))
            self.expenses_table.setItem(i, 1, QTableWidgetItem(str(expense["amount"])))
            self.expenses_table.setItem(
                i, 2, QTableWidgetItem(expense["description"] or "")
            )
            self.expenses_table.setItem(
                i, 3, QTableWidgetItem(expense["reference_number"] or "")
            )
            self.expenses_table.setItem(
                i, 4, QTableWidgetItem(expense["receipt_path"] or "")
            )
            self.expenses_table.setItem(
                i, 5, QTableWidgetItem(expense["linked_item_names"])
            )

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            edit_button = QPushButton("Edit")
            delete_button = QPushButton("Delete")
            edit_button.clicked.connect(
                lambda _, exp_id=expense["id"], data=expense: self.edit_expense(
                    exp_id, data
                )
            )
            delete_button.clicked.connect(
                lambda _, exp_id=expense["id"]: self.delete_expense(exp_id)
            )
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.setContentsMargins(0, 0, 0, 0)
            self.expenses_table.setCellWidget(i, 6, action_widget)

    def update_financials_display(self, date):
        financials = self.expense_manager.get_daily_financials(date)
        self.financials_label.setText(
            f"Daily Financials: Orders: {financials['total_orders']:.2f}, "
            f"Expenses: {financials['total_expenses']:.2f}, "
            f"After Expenses: {financials['after_expenses']:.2f}"
        )

    def open_add_expense_dialog(self):
        dialog = AddExpenseDialog(self.expense_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            expense_data = dialog.get_expense_data()
            if expense_data:
                self.add_new_expense(*expense_data)
            else:
                logger.warning("Add expense dialog rejected or invalid data.")

    def add_new_expense(
        self,
        expense_type,
        user_id,
        expense_date,
        amount,
        description,
        reference_number,
        receipt_path,
        linked_shop_item_ids,
    ):
        success, message = self.expense_manager.save_expense(
            expense_type,
            user_id,
            expense_date,
            amount,
            description,
            reference_number,
            receipt_path,
            linked_shop_item_ids,
        )
        if success:
            self.populate_table()
            self.update_financials_display(expense_date)
            QMessageBox.information(self, "Success", message)
        else:
            logger.error(f"Failed to save expense: {message}")
            QMessageBox.critical(self, "Error", message)

    def edit_expense(self, expense_id, expense_data):
        dialog = AddExpenseDialog(self.expense_manager, self, expense_data=expense_data)
        if dialog.exec_() == QDialog.Accepted:
            updated_expense_data = dialog.get_expense_data()
            if updated_expense_data:
                if self.expense_manager.update_expense(
                    expense_id, *updated_expense_data
                ):
                    self.populate_table()
                    self.update_financials_display(
                        updated_expense_data[2]
                    )  # expense_date
                    QMessageBox.information(
                        self, "Success", "Expense updated successfully!"
                    )
                else:
                    QMessageBox.critical(self, "Error", "Failed to update expense.")
            else:
                logger.warning("Edit expense dialog rejected or invalid data.")

    def delete_expense(self, expense_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this expense?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            expenses_data = self.expense_manager.get_expenses_data()
            expense_date = next(
                (e["expense_date"] for e in expenses_data if e["id"] == expense_id),
                None,
            )
            if self.expense_manager.delete_expense(expense_id):
                self.populate_table()
                if expense_date:
                    self.update_financials_display(expense_date)
                QMessageBox.information(
                    self, "Success", "Expense deleted successfully!"
                )
            else:
                QMessageBox.critical(self, "Error", "Failed to delete expense.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExpensesView()
    window.showMaximized()
    sys.exit(app.exec_())
