import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from datetime import date, timedelta
from Application.Components.DayClose.modal import DayCloseManager


class DayCloseView(QWidget):
    def __init__(self, db_helper=None):
        super().__init__()
        self.db_helper = DayCloseManager() if db_helper is None else db_helper
        self.setWindowTitle("Day Close")
        self.setGeometry(100, 100, 800, 400)

        layout = QVBoxLayout()
        title_label = QLabel("Day Close Summary")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.day_close_button = QPushButton("Perform Day Close")
        self.day_close_button.clicked.connect(self.perform_daily_close)
        layout.addWidget(self.day_close_button)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(
            [
                "Store Name",
                "Working Date",
                "Next Working Date",
                "Running Orders",
                "Total Amount",
                "Voided Orders",
                "Action",
            ]
        )
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_widget)

        self.setLayout(layout)
        self.check_and_perform_day_close()
        self.populate_table()

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
                    dc.voided_orders
                FROM day_close dc
                JOIN stores s ON dc.store_id = s.id
                ORDER BY dc.working_date DESC
                """
            )
            data = cursor.fetchall()

            self.table_widget.setRowCount(len(data))
            for row_index, row_data in enumerate(data):
                (
                    store_name,
                    working_date,
                    next_working_date,
                    running_orders,
                    total_amount,
                    voided_orders,
                ) = row_data

                if isinstance(working_date, str):
                    working_date = date.fromisoformat(working_date)
                if isinstance(next_working_date, str):
                    next_working_date = date.fromisoformat(next_working_date)

                self.table_widget.setItem(row_index, 0, QTableWidgetItem(store_name))
                self.table_widget.setItem(
                    row_index, 1, QTableWidgetItem(working_date.strftime("%Y-%m-%d"))
                )
                self.table_widget.setItem(
                    row_index,
                    2,
                    QTableWidgetItem(next_working_date.strftime("%Y-%m-%d")),
                )
                self.table_widget.setItem(
                    row_index, 3, QTableWidgetItem(str(running_orders))
                )
                self.table_widget.setItem(
                    row_index, 4, QTableWidgetItem(f"TZS {total_amount:.2f}")
                )
                self.table_widget.setItem(
                    row_index, 5, QTableWidgetItem(str(voided_orders))
                )

                audit_button = QPushButton("Audit")
                audit_button.clicked.connect(
                    lambda checked, sn=store_name, wd=working_date: self.open_audit_dialog(
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
                self.table_widget.setCellWidget(row_index, 6, button_widget)

            self.db_helper._commit_and_close(conn)

        except Exception as e:
            print(f"Error populating table: {e}")

    def open_audit_dialog(self, store_name, working_date):
        working_qdate = QDate(working_date.year, working_date.month, working_date.day)
        next_audit_qdate = working_qdate.addDays(1)
        next_audit = next_audit_qdate.toPyDate()

        running_count, total_amount, voided_count = self.db_helper.get_orders_status(
            working_date
        )

        dialog = AuditDialog(
            store_name=store_name,
            working_date=working_date,
            next_working_date=next_audit,
            running_orders=running_count,
            total_amount=total_amount,
            voided_orders=voided_count,
            cash_orders=0,
            credit_orders=0,
            mobile_orders=0,
            parent=self,
        )
        dialog.exec_()


class AuditDialog(QDialog):
    def __init__(
        self,
        store_name,
        working_date,
        next_working_date,
        running_orders,
        total_amount,
        voided_orders,
        cash_orders,
        credit_orders,
        mobile_orders,
        parent=None,
    ):
        super().__init__(parent)
        self.store_name = store_name
        self.working_date = working_date
        self.next_working_date = next_working_date
        self.db_helper = DayCloseManager()
        self.setWindowTitle(
            f"Day Close Summary for {store_name} from {working_date.strftime('%Y-%m-%d')} To {next_working_date.strftime('%Y-%m-%d')}"
        )
        self.setGeometry(200, 200, 400, 350)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        info_label = QLabel(
            f"Your working date is {working_date.strftime('%Y-%m-%d')}, orders are now frozen for that day"
        )
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)

        next_audit_layout = QHBoxLayout()
        next_audit_label = QLabel("Next Working Date")
        self.next_audit_date_edit = QDateEdit()
        self.next_audit_date_edit.setDate(next_working_date)
        self.next_audit_date_edit.setCalendarPopup(True)
        next_audit_layout.addWidget(next_audit_label)
        next_audit_layout.addWidget(self.next_audit_date_edit)
        main_layout.addLayout(next_audit_layout)

        summary_grid = QGridLayout()
        summary_grid.addWidget(QLabel("Running Orders"), 0, 0)
        self.running_orders_label = QLabel(str(running_orders))
        summary_grid.addWidget(self.running_orders_label, 0, 1)
        summary_grid.addWidget(QLabel("Total Amount"), 1, 0)
        self.total_amount_label = QLabel(f"${total_amount:.2f}")
        summary_grid.addWidget(self.total_amount_label, 1, 1)
        summary_grid.addWidget(QLabel("Voided Orders"), 2, 0)
        self.voided_orders_label = QLabel(str(voided_orders))
        summary_grid.addWidget(self.voided_orders_label, 2, 1)
        main_layout.addLayout(summary_grid)

        button_layout = QHBoxLayout()
        finish_button = QPushButton("Finish")
        finish_button.clicked.connect(self.finish_and_redirect)
        button_layout.addStretch(1)
        button_layout.addWidget(finish_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

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
            total_amount=float(self.total_amount_label.text().replace("$", "")),
            voided_orders=int(self.voided_orders_label.text()),
        )

        if success:
            QMessageBox.information(self, "Success", "Day close saved successfully.")
            # Close the dialog and parent (DayCloseView) to return to the main flow
            self.parent().close()
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save day close data.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DayCloseView()
    window.show()
    sys.exit(app.exec_())
