import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QDateEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
)
from PyQt5.QtCore import Qt, QDate
from datetime import date, timedelta
from Application.Components.DayClose.modal import DayCloseManager
from Application.Components.Inventory.Expenses.model import ExpenseManager


class AuditWidget(QWidget):
    def __init__(
        self,
        store_name,
        working_date,
        next_working_date,
        running_orders,
        total_amount,
        voided_orders,
        total_expenses,  # Added total_expenses parameter
        parent=None,
    ):
        super().__init__(parent)
        self.store_name = store_name
        self.working_date = working_date
        self.next_working_date = next_working_date
        self.db_helper = DayCloseManager()
        self.expenses_manager = ExpenseManager()

        self.setWindowTitle(
            f"Day Close Summary for {store_name} from {working_date.strftime('%Y-%m-%d')} To {next_working_date.strftime('%Y-%m-%d')}"
        )

        layout = QVBoxLayout()
        info_label = QLabel(
            f"Your working date is {working_date.strftime('%Y-%m-%d')}, orders are now frozen for that day"
        )
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        next_audit_layout = QHBoxLayout()
        next_audit_label = QLabel("Next Working Date")
        self.next_audit_date_edit = QDateEdit()
        self.next_audit_date_edit.setDate(next_working_date)
        self.next_audit_date_edit.setCalendarPopup(True)
        next_audit_layout.addWidget(next_audit_label)
        next_audit_layout.addWidget(self.next_audit_date_edit)
        layout.addLayout(next_audit_layout)

        # Summary Section
        summary_group = QGroupBox("Sales Summary")
        summary_layout = QGridLayout()
        summary_layout.addWidget(QLabel("Running Orders"), 0, 0)
        self.running_orders_label = QLabel(str(running_orders))
        summary_layout.addWidget(self.running_orders_label, 0, 1)
        summary_layout.addWidget(QLabel("Total Amount"), 1, 0)
        self.total_amount_label = QLabel(f"TZS {total_amount:.2f}")
        summary_layout.addWidget(self.total_amount_label, 1, 1)
        summary_layout.addWidget(QLabel("Voided Orders"), 2, 0)
        self.voided_orders_label = QLabel(str(voided_orders))
        summary_layout.addWidget(self.voided_orders_label, 2, 1)
        summary_layout.addWidget(QLabel("Total Expenses"), 3, 0)
        self.total_expenses_label = QLabel(f"TZS {total_expenses:.2f}")
        summary_layout.addWidget(self.total_expenses_label, 3, 1)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        back_button = QPushButton("Back to Summaryxxx")
        back_button.clicked.connect(self.back_to_summary)
        buttons_layout.addWidget(back_button)
        finish_button = QPushButton("Finishxxx")
        finish_button.clicked.connect(self.finish_and_redirect)
        buttons_layout.addWidget(finish_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.day_close_view = parent

    def back_to_summary(self):
        self.day_close_view.show_summary()

    def finish_and_redirect(self):
        next_working_date = self.next_audit_date_edit.date().toPyDate()
        stores = self.db_helper.get_stores_data()
        if not stores:
            QMessageBox.critical(self, "Error", "No stores found in database.")
            return
        store_id = stores[0]["id"]

        success = self.db_helper.save_day_close_data(
            store_id=store_id,
            working_date=self.working_date.strftime("%Y-%m-%d"),
            next_working_date=next_working_date.strftime("%Y-%m-%d"),
            running_orders=int(self.running_orders_label.text()),
            total_amount=float(self.total_amount_label.text().replace("TZS ", "")),
            voided_orders=int(self.voided_orders_label.text()),
        )

        if success:
            QMessageBox.information(self, "Success", "Day close saved successfully.")
            self.day_close_view.populate_table()
            self.day_close_view.show_summary()
        else:
            QMessageBox.critical(self, "Error", "Failed to save day close data.")


class DayCloseView(QWidget):
    def __init__(self, db_helper=None):
        super().__init__()
        self.db_helper = DayCloseManager() if db_helper is None else db_helper
        self.expenses_manager = ExpenseManager()  # Added expenses manager
        self.setWindowTitle("Day Close")
        self.setGeometry(100, 100, 800, 400)

        self.main_layout = QVBoxLayout()
        title_label = QLabel("Day Close Summary")
        title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title_label)

        self.day_close_button = QPushButton("Perform Day Close")
        self.day_close_button.clicked.connect(self.perform_daily_close)
        self.main_layout.addWidget(self.day_close_button)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(
            8
        )  # Increased column count to include expenses
        self.table_widget.setHorizontalHeaderLabels(
            [
                "Store Name",
                "Working Date",
                "Next Working Date",
                "Running Orders",
                "Total Amount",
                "Voided Orders",
                "Total Expenses",
                "Action",
            ]  # Added Total Expenses
        )
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.main_layout.addWidget(self.table_widget)

        self.audit_widget = None
        self.setLayout(self.main_layout)
        self.check_and_perform_day_close()
        self.show_summary()

    def show_summary(self):
        for i in reversed(range(self.main_layout.count())):
            widget = self.main_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        title_label = QLabel("Day Close Summary")
        title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(self.day_close_button)
        self.main_layout.addWidget(self.table_widget)
        self.populate_table()

    def show_audit_details(self, store_name, working_date):
        working_qdate = QDate(working_date.year, working_date.month, working_date.day)
        next_audit_qdate = working_qdate.addDays(1)
        next_audit = next_audit_qdate.toPyDate()

        running_count, total_amount, voided_count = self.db_helper.get_orders_status(
            working_date
        )

        # Calculate total expenses for this date
        total_expenses = self._get_total_expenses_for_date(working_date)

        for i in reversed(range(self.main_layout.count())):
            widget = self.main_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        self.audit_widget = AuditWidget(
            store_name=store_name,
            working_date=working_date,
            next_working_date=next_audit,
            running_orders=running_count,
            total_amount=total_amount,
            voided_orders=voided_count,
            total_expenses=total_expenses,
            parent=self,
        )
        self.main_layout.addWidget(self.audit_widget)

    def perform_daily_close(self):
        current_date = date.today() - timedelta(days=1)
        stores = self.db_helper.get_stores_data()

        if not stores:
            QMessageBox.critical(
                self, "Error", "No stores found. Please contact support."
            )
            return

        for store in stores:
            if not self.db_helper.check_day_close_exists(store["id"], current_date):
                success = self.db_helper.perform_day_close(store["id"], current_date)
                if success:
                    print(f"Day close completed for {store['name']} on {current_date}")
                else:
                    print(f"Failed to close day for {store['name']}")
        self.populate_table()

    def check_and_perform_day_close(self):
        current_date = date.today() - timedelta(days=1)
        stores = self.db_helper.get_stores_data()

        if not stores:
            print("No stores available to check day close.")
            return

        for store in stores:
            if not self.db_helper.check_day_close_exists(store["id"], current_date):
                self.perform_daily_close()
                break

    def _get_total_expenses_for_date(self, target_date):
        if not self.expenses_manager:
            return 0.0
        total = 0.0
        expenses_data = self.expenses_manager.get_expenses_data()
        for expense in expenses_data:
            if expense["expense_date"] == target_date.strftime("%Y-%m-%d"):
                total += expense["amount"]
        return total

    def populate_table(self):
        try:
            conn = self.db_helper._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    s.name,
                    dc.working_date,
                    dc.next_working_date,
                    dc.running_orders,
                    dc.total_amount,
                    dc.voided_orders,
                    COALESCE(SUM(e.amount), 0) as total_expenses
                FROM day_close dc
                JOIN stores s ON dc.store_id = s.id
                LEFT JOIN expenses e ON e.expense_date = dc.working_date
                GROUP BY s.name, dc.working_date, dc.next_working_date,
                        dc.running_orders, dc.total_amount, dc.voided_orders
                ORDER BY dc.working_date DESC
                LIMIT 1
                """
            )
            data = cursor.fetchall()

            self.table_widget.setRowCount(len(data))
            if data:
                (
                    store_name,
                    working_date,
                    next_working_date,
                    running_orders,
                    total_amount,
                    voided_orders,
                    total_expenses,
                ) = data[0]

                if isinstance(working_date, str):
                    working_date = date.fromisoformat(working_date)
                if isinstance(next_working_date, str):
                    next_working_date = date.fromisoformat(next_working_date)

                self.table_widget.setItem(0, 0, QTableWidgetItem(store_name))
                self.table_widget.setItem(
                    0, 1, QTableWidgetItem(working_date.strftime("%Y-%m-%d"))
                )
                self.table_widget.setItem(
                    0, 2, QTableWidgetItem(next_working_date.strftime("%Y-%m-%d"))
                )
                self.table_widget.setItem(0, 3, QTableWidgetItem(str(running_orders)))
                self.table_widget.setItem(
                    0, 4, QTableWidgetItem(f"TZS {total_amount:.2f}")
                )
                self.table_widget.setItem(0, 5, QTableWidgetItem(str(voided_orders)))
                self.table_widget.setItem(
                    0, 6, QTableWidgetItem(f"TZS {total_expenses:.2f}")
                )

                audit_button = QPushButton("Audit")
                audit_button.clicked.connect(
                    lambda checked, sn=store_name, wd=working_date: self.show_audit_details(
                        sn, wd
                    )
                )
                audit_button.setStyleSheet(
                    "background-color: #e0f7fa; color: #00838f; border: 1px solid #b2ebf2; border-radius: 5px; padding: 5px;"
                )
                hbox = QHBoxLayout()
                hbox.addWidget(audit_button)
                hbox.setAlignment(Qt.AlignCenter)
                button_widget = QWidget()
                button_widget.setLayout(hbox)
                self.table_widget.setCellWidget(0, 7, button_widget)
                self.table_widget.setColumnWidth(7, 100)
            else:
                self.table_widget.setRowCount(0)

            self.db_helper._commit_and_close(conn)

        except Exception as e:
            print(f"Error populating table: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DayCloseView()
    window.show()
    sys.exit(app.exec_())
