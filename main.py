import os
import socket
import sqlite3
import sys
from datetime import datetime, date, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon, QPixmap
from Application.Components.DayClose.day_close import DayCloseManager
from Application.Components.Inventory.Expenses.model import ExpenseManager
from Application.Components.Inventory.Main import InventoryView, MainInventoryWindow
from Application.Components.OrderSummary.Carts.modal import CartModel
from Application.Components.Reports.View import ReportView
from Application.Components.components import Sidebar, ProductCard, PaymentCard
from Application.Components.OrderSummary.order_summary import OrderSummaryView
from Helper.db_conn import db
from Helper.api import sync_data_with_server, load_icon


def load_icon(icon_path):
    """Loads an icon from the given path."""
    return QIcon(QPixmap(icon_path))


def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
        print(f"Running in PyInstaller bundle, base path: {base_path}")
    else:
        base_path = os.path.abspath(".")
        print(f"Running in dev mode, base path: {base_path}")
    full_path = os.path.join(base_path, relative_path)
    print(
        f"Resolved path for {relative_path}: {full_path}, exists: {os.path.exists(full_path)}"
    )
    return full_path


class AuditWidget(QDialog):
    def __init__(
        self,
        store_name,
        working_date,
        next_working_date,
        running_orders,
        total_amount,
        voided_orders,
        total_expenses,  # Added total_expenses parameter
        db_helper,
        parent=None,
    ):
        super().__init__(parent)
        self.store_name = store_name
        self.working_date = working_date
        self.next_working_date = next_working_date
        self.db_helper = db_helper
        self.setWindowTitle(
            f"Day Close Audit for {store_name} - {working_date.strftime('%Y-%m-%d')}"
        )
        self.setModal(True)
        self.setGeometry(100, 100, 400, 300)

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

        summary_grid = QGridLayout()
        summary_grid.addWidget(QLabel("Running Orders"), 0, 0)
        self.running_orders_label = QLabel(str(running_orders))
        summary_grid.addWidget(self.running_orders_label, 0, 1)
        summary_grid.addWidget(QLabel("Total Amount"), 1, 0)
        self.total_amount_label = QLabel(f"TZS {total_amount:.2f}")
        summary_grid.addWidget(self.total_amount_label, 1, 1)
        summary_grid.addWidget(QLabel("Voided Orders"), 2, 0)
        self.voided_orders_label = QLabel(str(voided_orders))
        summary_grid.addWidget(self.voided_orders_label, 2, 1)
        summary_grid.addWidget(QLabel("Total Expenses"), 3, 0)  # Added expenses display
        self.total_expenses_label = QLabel(f"TZS {total_expenses:.2f}")
        summary_grid.addWidget(self.total_expenses_label, 3, 1)
        layout.addLayout(summary_grid)

        back_button = QPushButton("Cancel")
        back_button.clicked.connect(self.reject)
        layout.addWidget(back_button)

        finish_button = QPushButton("Finish")
        finish_button.clicked.connect(self.finish_and_save)
        layout.addWidget(finish_button)

        self.setLayout(layout)

    def finish_and_save(self):
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
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save day close data.")


class DayCloseView(QWidget):
    day_close_saved = pyqtSignal()

    def __init__(self, db_helper=None):
        super().__init__()
        self.db_helper = DayCloseManager() if db_helper is None else db_helper
        self.expenses_manager = ExpenseManager()  
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
        self.table_widget.setColumnCount(8)
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
            ]
        )
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.main_layout.addWidget(self.table_widget)

        self.setLayout(self.main_layout)
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
                    self.show_audit_details(store["name"], current_date)
                else:
                    print(f"Failed to close day for {store['name']}")
        self.populate_table()

    def _get_total_expenses_for_date(self, target_date):
        if not self.expenses_manager:
            return 0.0
        total = 0.0
        expenses_data = self.expenses_manager.get_expenses_data()
        for expense in expenses_data:
            if expense["expense_date"] == target_date.strftime("%Y-%m-%d"):
                total += expense["amount"]
        return total

    def show_audit_details(self, store_name, working_date):
        if isinstance(working_date, str):
            working_date = date.fromisoformat(working_date)

        next_audit_date = working_date + timedelta(days=1)

        try:
            running_count, total_amount, voided_count = (
                self.db_helper.get_orders_status(working_date)
            )
            total_expenses = self._get_total_expenses_for_date(
                working_date
            )  # Calculate expenses
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch audit details: {e}")
            return

        audit_dialog = AuditWidget(
            store_name=store_name,
            working_date=working_date,
            next_working_date=next_audit_date,
            running_orders=running_count,
            total_amount=total_amount,
            voided_orders=voided_count,
            total_expenses=total_expenses,  # Pass total expenses
            db_helper=self.db_helper,
            parent=self,
        )
        if audit_dialog.exec_() == QDialog.Accepted:
            self.populate_table()
            self.day_close_saved.emit()

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
            print(f"DayCloseView: Day Close Data fetched: {data}")

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
                store_name_copy = str(store_name)
                working_date_copy = date(
                    working_date.year, working_date.month, working_date.day
                )
                audit_button.clicked.connect(
                    lambda checked=False, s=store_name_copy, w=working_date_copy: self.show_audit_details(
                        s, w
                    )
                )
                audit_button.setStyleSheet(
                    "background-color: #e0f7fa; color: #00838f; border: 1px solid #b2ebf2; border-radius: 5px; padding: 5px;"
                )
                self.table_widget.setCellWidget(0, 7, audit_button)
                self.table_widget.setColumnWidth(7, 100)
            else:
                self.table_widget.setRowCount(0)
            self.db_helper._commit_and_close(conn)
        except Exception as e:
            print(f"DayCloseView: Error populating table: {e}")
            import traceback

            traceback.print_exc()


class PrinterSettingsWindow(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        if db is None:
            raise ValueError(
                "Database instance (db) is required for PrinterSettingsWindow"
            )
        self.db = db
        self.setWindowTitle("Printer Settings")
        self.setStyleSheet("background-color: #f5f5f5;")
        self.setGeometry(100, 100, 600, 400)

        self.main_layout = QVBoxLayout(self)
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(15)

        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar.setStyleSheet(
            "background-color: #f8f9fa; border-radius: 8px; padding: 10px;"
        )

        printer_options = self.db.get_virtual_device_data()
        for text in printer_options:
            btn = QPushButton(text)
            btn.setStyleSheet(
                """
                QPushButton {
                    background: transparent;
                    padding: 10px;
                    border-radius: 6px;
                    text-align: left;
                }
                QPushButton:hover { background: #e9ecef; }
                """
            )
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=text: self.select_printer_type(t))
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch()
        self.content_layout.addWidget(self.sidebar, 2)

        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_widget)
        self.settings_layout.setContentsMargins(20, 20, 20, 20)

        self.form_layout = QGridLayout()
        self.settings_layout.addLayout(self.form_layout)

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setStyleSheet(
            """
            QPushButton {
                background: #4a9dff;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #4a9dff80; }
            """
        )
        self.save_btn.clicked.connect(self.save_settings)

        self.error_label = QLabel("Please select an item from the list.")
        self.error_label.setStyleSheet("color: #dc3545; font-size: 12px;")
        self.error_label.setVisible(False)
        self.settings_layout.addWidget(self.error_label)

        self.content_layout.addWidget(self.settings_widget, 5)
        self.main_layout.addLayout(self.content_layout)

        self.selected_printer = None
        self.input_fields = {}

    def clear_form(self):
        for i in reversed(range(self.form_layout.count())):
            widget = self.form_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.form_layout.deleteLater()
        self.form_layout = QGridLayout()
        self.settings_layout.insertLayout(0, self.form_layout)

        if self.save_btn in self.settings_layout.children():
            self.settings_layout.removeWidget(self.save_btn)

    def create_network_printer_form(self):
        self.input_fields = {}
        self.form_layout.addWidget(QLabel("Printer Name"), 0, 0)
        self.input_fields["printer_name"] = QLineEdit()
        self.form_layout.addWidget(self.input_fields["printer_name"], 0, 1)

        self.form_layout.addWidget(QLabel("Printer IP Address"), 1, 0)
        self.input_fields["printer_ip"] = QLineEdit()
        self.form_layout.addWidget(self.input_fields["printer_ip"], 1, 1)

        self.form_layout.addWidget(QLabel("Paper Size (inches)"), 2, 0)
        self.input_fields["paper_size"] = QComboBox()
        self.input_fields["paper_size"].addItems(["3x2", "4x3", "5x3"])
        self.form_layout.addWidget(self.input_fields["paper_size"], 2, 1)

        self.form_layout.addWidget(QLabel("Inkjet Type"), 3, 0)
        self.input_fields["inkjet_type"] = QComboBox()
        self.input_fields["inkjet_type"].addItems(["Inkjet", "Laser"])
        self.form_layout.addWidget(self.input_fields["inkjet_type"], 3, 1)

    def create_bluetooth_printer_form(self):
        self.input_fields = {}
        self.form_layout.addWidget(QLabel("Printer Name"), 0, 0)
        self.input_fields["printer_name"] = QLineEdit()
        self.form_layout.addWidget(self.input_fields["printer_name"], 0, 1)

        self.form_layout.addWidget(QLabel("Bluetooth Address"), 1, 0)
        self.input_fields["bluetooth_address"] = QLineEdit()
        self.input_fields["bluetooth_address"].setPlaceholderText(
            "e.g., 00:11:22:33:44:55"
        )
        self.form_layout.addWidget(self.input_fields["bluetooth_address"], 1, 1)

        self.form_layout.addWidget(QLabel("Paper Size (inches)"), 2, 0)
        self.input_fields["paper_size"] = QComboBox()
        self.input_fields["paper_size"].addItems(["3x2", "4x3", "5x3"])
        self.form_layout.addWidget(self.input_fields["paper_size"], 2, 1)

    def create_cash_drawer_form(self):
        self.input_fields = {}
        self.form_layout.addWidget(QLabel("Associated Printer"), 0, 0)
        self.input_fields["associated_printer"] = QComboBox()
        printer_names = [
            name for name in self.db.get_virtual_device_data() if "Printer" in name
        ]
        self.input_fields["associated_printer"].addItems(printer_names)
        self.form_layout.addWidget(self.input_fields["associated_printer"], 0, 1)

        self.form_layout.addWidget(QLabel("Drawer Code"), 1, 0)
        self.input_fields["drawer_code"] = QLineEdit()
        self.input_fields["drawer_code"].setPlaceholderText("e.g., 27,112,0,25,250")
        self.form_layout.addWidget(self.input_fields["drawer_code"], 1, 1)

    def select_printer_type(self, printer_type):
        self.selected_printer = printer_type
        self.error_label.setVisible(False)

        for i in range(self.sidebar_layout.count()):
            widget = self.sidebar_layout.itemAt(i).widget()
            if widget and widget != self.sender():
                widget.setChecked(False)
        self.sender().setChecked(True)

        self.clear_form()
        if "Network Printer" in printer_type:
            self.create_network_printer_form()
        elif "Bluetooth Printer" in printer_type:
            self.create_bluetooth_printer_form()
        elif "Cash Drawer" in printer_type:
            self.create_cash_drawer_form()

        self.settings_layout.addWidget(self.save_btn, alignment=Qt.AlignRight)

    def get_virtual_device_id(self, device_name):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM virtual_devices WHERE name = ?", (device_name,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error retrieving virtual device ID: {e}")
            return None

    def save_settings(self):
        if not self.selected_printer:
            self.error_label.setVisible(True)
            return

        virtual_device_id = self.get_virtual_device_id(self.selected_printer)
        if not virtual_device_id:
            self.error_label.setText("Error: Could not find device in database.")
            self.error_label.setVisible(True)
            QMessageBox.critical(
                self, "Error", "Failed to save settings.", QMessageBox.Ok
            )
            return

        try:
            if "Network Printer" in self.selected_printer:
                printer_name = self.input_fields["printer_name"].text()
                printer_ip = self.input_fields["printer_ip"].text()
                paper_size = self.input_fields["paper_size"].currentText()
                if not (printer_name and printer_ip):
                    self.error_label.setText("Please fill all required fields.")
                    self.error_label.setVisible(True)
                    return
                self.db.insert_printer_settings(
                    virtual_device_id=virtual_device_id,
                    printer_type="Network Printer",
                    printer_name=printer_name,
                    printer_ip=printer_ip,
                    paper_size=paper_size,
                )
            elif "Bluetooth Printer" in self.selected_printer:
                printer_name = self.input_fields["printer_name"].text()
                bluetooth_address = self.input_fields["bluetooth_address"].text()
                paper_size = self.input_fields["paper_size"].currentText()
                if not (printer_name and bluetooth_address):
                    self.error_label.setText("Please fill all required fields.")
                    self.error_label.setVisible(True)
                    return
                self.db.insert_printer_settings(
                    virtual_device_id=virtual_device_id,
                    printer_type="Bluetooth Printer",
                    printer_name=printer_name,
                    paper_size=paper_size,
                    bluetooth_address=bluetooth_address,
                )
            elif "Cash Drawer" in self.selected_printer:
                associated_printer = self.input_fields[
                    "associated_printer"
                ].currentText()
                drawer_code = self.input_fields["drawer_code"].text()
                if not associated_printer:
                    self.error_label.setText("Please select an associated printer.")
                    self.error_label.setVisible(True)
                    return
                self.db.insert_printer_settings(
                    virtual_device_id=virtual_device_id,
                    printer_type="Cash Drawer",
                    printer_name="Cash Drawer",
                    associated_printer=associated_printer,
                    drawer_code=drawer_code,
                )
            QMessageBox.information(
                self, "Success", "Settings saved successfully.", QMessageBox.Ok
            )
            self.accept()
        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to save settings: {str(e)}",
                QMessageBox.Ok,
            )


# class SyncWorker(QThread):
#     sync_finished = pyqtSignal(bool)

#     def __init__(self, force_full_sync=True, parent=None):
#         super().__init__(parent)
#         self.force_full_sync = force_full_sync

#     def run(self):
#         success = sync_data_with_server(self.force_full_sync)
#         self.sync_finished.emit(success)


class DashboardView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMALI v.1.0")
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        self.setGeometry(0, 0, screen_size.width(), screen_size.height())
        self.setStyleSheet("background-color: #f5f5f5;")

        self.db_helper = DayCloseManager()
        self.cart_model = CartModel()
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header
        self.header = QWidget()
        self.header.setStyleSheet("background-color: #2b2d42; padding: 10px;")
        header_layout = QHBoxLayout(self.header)

        # Left Controls Layout
        left_controls_layout = QHBoxLayout()
        sales_btn = QPushButton("Sales")
        sales_btn.setStyleSheet(
            """
            QPushButton { color: white; background: transparent; padding: 8px 12px; border-radius: 6px; border: 2px solid gray; font-weight: bold; }
            QPushButton:hover { background: blue; }
            """
        )
        sales_btn.clicked.connect(self.open_sales_view)
        left_controls_layout.addWidget(sales_btn)

        sales_summary_btn = QPushButton("Sales Summary")
        sales_summary_btn.setStyleSheet(
            """
            QPushButton { color: white; background: transparent; padding: 8px 12px; border-radius: 6px; border: 2px solid gray; font-weight: bold; }
            QPushButton:hover { background: blue; }
            """
        )
        sales_summary_btn.clicked.connect(self.open_sales_summary_view)
        left_controls_layout.addWidget(sales_summary_btn)

        delivery_btn = QPushButton("Delivery")
        delivery_btn.setStyleSheet(
            """
            QPushButton { color: white; background: transparent; padding: 8px 12px; border-radius: 6px; border: 2px solid gray; font-weight: bold; }
            QPushButton:hover { background: blue; }
            """
        )
        delivery_btn.clicked.connect(self.open_delivery_view)
        left_controls_layout.addWidget(delivery_btn)

        # Title Layout (Logo)
        title_layout = QVBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap(get_resource_path("Resources/Images/logo.png"))
        if logo_pixmap.isNull():
            print("Warning: Failed to load logo from Resources/Images/logo.png")
            logo_label.setText("Amali")
            logo_label.setStyleSheet(
                "color: white; font-size: 24px; font-weight: bold;"
            )
        else:
            logo_pixmap = logo_pixmap.scaled(
                100, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(logo_label)
        

        # Right Controls Layout
        right_controls_layout = QHBoxLayout()
        
        # # # Sync Toggle Switch with LED Indicator
        # sync_layout = QHBoxLayout()
        # sync_layout.setSpacing(5)

        # self.sync_switch = QCheckBox("Sync")
        # self.sync_switch.setChecked(True)
        # self.sync_switch.setStyleSheet(
        #     """
        #     QCheckBox {
        #         color: white;
        #         font-size: 14px;
        #         padding: 5px;
        #         spacing: 5px;
        #     }
        #     QCheckBox::indicator {
        #         width: 40px;
        #         height: 20px;
        #         border-radius: 10px;
        #         background-color: #dc3545;
        #     }
        #     QCheckBox::indicator:checked {
        #         background-color: #28a745;
        #     }
        #     QCheckBox::indicator::before {
        #         content: '';
        #         width: 16px;
        #         height: 16px;
        #         border-radius: 8px;
        #         background-color: white;
        #         position: absolute;
        #         top: 2px;
        #         left: 2px;
        #         transition: 0.2s;
        #     }
        #     QCheckBox::indicator:checked::before {
        #         left: 22px;
        #     }
        #     """
        # )
        # self.sync_switch.stateChanged.connect(self.on_sync_switch_changed)
        # sync_layout.addWidget(self.sync_switch)

        # self.sync_status_indicator = QLabel()
        # self.sync_status_indicator.setFixedSize(10, 10)
        # self.sync_status_indicator.setStyleSheet(
        #     "background-color: gray; border-radius: 5px;"
        # )
        # self.sync_status_indicator.setToolTip("Sync Status: Unknown")
        # sync_layout.addWidget(self.sync_status_indicator)

        # right_controls_layout.addLayout(sync_layout)
        
        day_close_btn = QPushButton("Day Close")
        day_close_btn.setStyleSheet(
            """
            QPushButton { color: white; background: transparent; padding: 8px 12px; border-radius: 6px; border: 2px solid gray; font-weight: bold; }
            QPushButton:hover { background: blue; }
            """
        )
        day_close_btn.clicked.connect(self.open_day_close_view)
        right_controls_layout.addWidget(day_close_btn)

        inventory_btn = QPushButton("Inventory")
        inventory_btn.setStyleSheet(
            """
            QPushButton { color: white; background: transparent; padding: 8px 12px; border-radius: 6px; border: 2px solid gray; font-weight: bold; }
            QPushButton:hover { background: blue; }
            """
        )
        inventory_btn.clicked.connect(self.open_inventory_view)
        right_controls_layout.addWidget(inventory_btn)

        report_btn = QPushButton("Report")
        report_btn.setStyleSheet(
            """
            QPushButton { color: white; background: transparent; padding: 8px 12px; border-radius: 6px; border: 2px solid gray; font-weight: bold; }
            QPushButton:hover { background: blue; }
            """
        )
        report_btn.clicked.connect(self.open_report_view)
        right_controls_layout.addWidget(report_btn)

        for text in ["Settings", "Help"]:
            btn = QPushButton(text)
            btn.setStyleSheet(
                """
                QPushButton { color: white; background: transparent; padding: 8px 12px; border-radius: 6px; border: 2px solid gray; font-weight: bold; }
                QPushButton:hover { background: blue; }
                """
            )
            right_controls_layout.addWidget(btn)

        logo_btn = QPushButton()
        logo_btn.setIcon(load_icon(get_resource_path("Resources/Images/gear.png")))
        logo_btn.setIconSize(QSize(24, 24))
        logo_btn.setToolTip("Company Logo")
        logo_btn.setStyleSheet(
            """
            QPushButton { background: transparent; padding: 8px; border-radius: 6px; }
            QPushButton:hover { background: #404258; }
            """
        )
        logo_btn.clicked.connect(self.open_printer_settings)
        right_controls_layout.addWidget(logo_btn)

        header_layout.addLayout(left_controls_layout)
        header_layout.addStretch(1)
        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)
        header_layout.addLayout(right_controls_layout)

        self.main_layout.addWidget(self.header)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # Dashboard Content
        self.dashboard_content = QWidget()
        content_layout = QHBoxLayout(self.dashboard_content)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(15)
        self.stacked_widget.addWidget(self.dashboard_content)

        self.sidebar = Sidebar()
        self.sidebar.update_group_buttons(db.get_local_item_groups())
        content_layout.addWidget(self.sidebar, 2)

        product_widget = QWidget()
        product_layout = QVBoxLayout(product_widget)

        category_scroll_area = QScrollArea()
        category_scroll_area.setWidgetResizable(True)
        category_scroll_area.setStyleSheet(
            "background-color: transparent; border: 0.5rem solid gray; padding-left: 10px;"
        )

        category_container = QWidget()
        category_container.setMinimumWidth(1200)
        self.category_layout = QHBoxLayout(category_container)
        self.category_layout.setContentsMargins(0, 0, 0, 0)
        self.category_layout.setSpacing(10)

        category_scroll_area.setMaximumHeight(60)
        category_scroll_area.setWidget(category_container)
        product_layout.addWidget(category_scroll_area)

        product_layout.addSpacing(15)

        search_container = QHBoxLayout()
        search_container.setSpacing(10)

        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search Items")
        self.product_search.setStyleSheet(
            """
            QLineEdit {
                background: white; border: 1px solid #ced4da; border-radius: 8px; padding: 8px 10px; font-size: 14px;
            }
            QLineEdit:disabled {
                background: #e9ecef; color: #6c757d;
            }
            """
        )
        self.product_search.setMaximumHeight(40)
        self.product_search.textChanged.connect(self.filter_products)
        search_container.addWidget(self.product_search, 3)

        self.mode_switch = QPushButton("Barcode Mode")
        self.mode_switch.setCheckable(True)
        self.mode_switch.setChecked(True)
        self.mode_switch.setStyleSheet(
            """
            QPushButton {
                background: #4a9dff; color: white; border: none; border-radius: 8px; padding: 8px; font-size: 14px; font-weight: bold; min-width: 100px;
            }
            QPushButton:checked {
                background: #28a745;
            }
            QPushButton:hover:!checked {
                background: #4a9dff80;
            }
            QPushButton:hover:checked {
                background: #218838;
            }
            """
        )
        self.mode_switch.clicked.connect(self.toggle_search_mode)
        search_container.addWidget(self.mode_switch, 1)

        self.product_barcode_search = QLineEdit()
        self.product_barcode_search.setPlaceholderText("Scan Barcode")
        self.product_barcode_search.setStyleSheet(
            """
            QLineEdit {
                background: white; border: 1px solid #ced4da; border-radius: 8px; padding: 8px 10px; font-size: 14px;
            }
            QLineEdit:disabled {
                background: #e9ecef; color: #6c757d;
            }
            """
        )
        self.product_barcode_search.setMaximumHeight(40)
        self.product_barcode_search.setFocusPolicy(Qt.StrongFocus)
        self.product_barcode_search.textChanged.connect(self.handle_barcode_input)
        self.barcode_timer = QTimer(self)
        self.barcode_timer.setSingleShot(True)
        self.barcode_timer.timeout.connect(self.process_pending_barcode)
        search_container.addWidget(self.product_barcode_search, 3)

        self.is_barcode_mode = True
        self.product_barcode_search.setEnabled(True)
        self.product_search.setEnabled(False)
        self.product_barcode_search.setFocus()

        product_layout.addLayout(search_container)
        self.product_grid = QGridLayout()
        self.product_grid.setVerticalSpacing(10)
        self.product_grid.setHorizontalSpacing(10)
        self.product_grid.setAlignment(Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget()
        container.setLayout(self.product_grid)
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        scroll.setWidget(container)
        scroll.setAlignment(Qt.AlignTop)
        product_layout.addWidget(scroll)

        content_layout.addWidget(product_widget, 5)

        # Checkout Widget
        self.checkout_widget = QWidget()
        self.checkout_widget.setStyleSheet("background: #f8f9fa; border-radius: 12px;")
        self.checkout_layout = QVBoxLayout(self.checkout_widget)
        self.checkout_layout.setContentsMargins(15, 15, 15, 15)
        self.checkout_layout.setSpacing(15)

        self.customer_type_label = QLabel("Customer Type:")
        self.customer_type = QComboBox()
        self.customer_types_data = db.get_customer_types()
        customer_type_names = [ct["name"] for ct in self.customer_types_data]
        self.customer_type.addItems(customer_type_names)
        self.customer_type.setStyleSheet(
            """
            QComboBox { background: white; border: 1px solid #ced4da; border-radius: 8px; padding: 8px; font-size: 14px; }
            """
        )
        self.checkout_layout.addWidget(self.customer_type_label)
        self.checkout_layout.addWidget(self.customer_type)

        self.customer_label = QLabel("Select Customer:")
        self.customer_select = QComboBox()
        self.customers_data = db.get_customers()
        self.populate_customers_combobox()
        self.customer_select.setStyleSheet(
            """
            QComboBox { background: white; border: 1px solid #ced4da; border-radius: 8px; padding: 8px; font-size: 14px; }
            """
        )
        self.customer_select.setVisible(False)
        self.checkout_layout.addWidget(self.customer_label)
        self.checkout_layout.addWidget(self.customer_select)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Item", "Unit", "Qty", "Price", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.table.setStyleSheet(
            """
            QTableWidget { background: white; border-radius: 8px; border: 1px solid #dee2e6; }
            QHeaderView::section { background: #e9ecef; padding: 8px; }
            """
        )
        self.checkout_layout.addWidget(self.table)

        details = QGridLayout()
        self.subtotal_label = QLabel("0.00")
        self.total_label = QLabel("0.00")
        details.addWidget(QLabel("Subtotal:"), 0, 0)
        details.addWidget(self.subtotal_label, 0, 1)
        details.addWidget(QLabel("Total:"), 1, 0)
        details.addWidget(self.total_label, 1, 1)
        self.checkout_layout.addLayout(details)

        btn_layout = QHBoxLayout()
        self.add_to_cart_btn = QPushButton("Add to Cart")
        self.add_to_cart_btn.setStyleSheet(
            """
            QPushButton { background: #4a9dff; color: white; border: none; border-radius: 8px; padding: 12px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: #4a9dff80; }
            """
        )
        self.add_to_cart_btn.clicked.connect(self.add_to_cart)
        btn_layout.addWidget(self.add_to_cart_btn)

        self.checkout_btn = QPushButton("Check Out")
        self.checkout_btn.setStyleSheet(
            """
            QPushButton { background: #28a745; color: white; border: none; border-radius: 8px; padding: 12px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: #218838; }
            """
        )
        self.checkout_btn.clicked.connect(self.open_payment_card)
        btn_layout.addWidget(self.checkout_btn)

        self.checkout_layout.addLayout(btn_layout)
        content_layout.addWidget(self.checkout_widget, 3)

        # Order Summary View
        self.order_summary_view = OrderSummaryView(self)
        self.stacked_widget.addWidget(self.order_summary_view)
        self.order_summary_index = 1

        # Day Close View
        self.day_close_view = DayCloseView(db_helper=self.db_helper)
        self.stacked_widget.addWidget(self.day_close_view)
        self.day_close_index = 2
        self.day_close_view.day_close_saved.connect(self.enable_header)

        # Report View
        self.report_view = ReportView()
        self.stacked_widget.addWidget(self.report_view)
        self.report_index = 3

        # Inventory View
        self.inventory_view = MainInventoryWindow()
        self.stacked_widget.addWidget(self.inventory_view)
        self.inventory_index = 4

        # Connections
        self.sidebar.group_selected.connect(self.update_category_cards)
        self.customer_type.currentTextChanged.connect(self.on_customer_type_changed)

        self.payment_card = PaymentCard(0.0, self)
        content_layout.addWidget(self.payment_card, 3)
        self.payment_card.setVisible(False)

        self.setCentralWidget(self.main_widget)

        self.current_items = []
        self.current_category_id = None
        self.product_cards = {}
        self.pending_barcode = ""

        item_groups = db.get_local_item_groups()
        if item_groups:
            self.update_category_cards(item_groups[0])

        # self.sync_timer = QTimer(self)
        # self.sync_timer.timeout.connect(self.start_sync_thread)
        # self.sync_timer.start(10000)  # Sync every 10 seconds if enabled
        # self.sync_thread = None
        # self.check_internet_on_startup()

        # Check and perform day close on startup
        self.check_and_perform_day_close()

    def disable_header(self):
        self.header.setEnabled(False)

    def enable_header(self):
        self.header.setEnabled(True)

    def check_and_perform_day_close(self):
        current_date = date.today() - timedelta(days=1)
        stores = self.db_helper.get_stores_data()

        if not stores:
            print("DashboardView: No stores available to check day close.")
            return

        for store in stores:
            if not self.db_helper.check_day_close_exists(store["id"], current_date):
                print("DashboardView: No day close found, switching to DayCloseView")
                self.stacked_widget.setCurrentIndex(self.day_close_index)
                self.disable_header()
                reply = QMessageBox.question(
                    self,
                    "Day Close Required",
                    f"No day close found for {current_date.strftime('%Y-%m-%d')}. Would you like to perform it now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self.day_close_view.perform_daily_close()
                break
        else:
            print("DashboardView: Day close already exists, proceeding to dashboard")
            self.enable_header()

    def open_day_close_view(self):
        print("Opening Day Close View")
        current_date = date.today() - timedelta(days=1)
        stores = self.db_helper.get_stores_data()
        day_close_pending = any(
            not self.db_helper.check_day_close_exists(store["id"], current_date)
            for store in stores
        )
        self.stacked_widget.setCurrentIndex(self.day_close_index)
        if day_close_pending:
            self.disable_header()

    def open_inventory_view(self):
        print("Opening Inventory View")
        self.stacked_widget.setCurrentIndex(self.inventory_index)

    def open_report_view(self):
        print("Opening Report View")
        self.stacked_widget.setCurrentIndex(self.report_index)

    def dashboard_view(self):
        self.stacked_widget.setCurrentIndex(0)

    def get_cart_items(self):
        items = []
        for row in range(self.table.rowCount()):
            name = (
                self.table.item(row, 0).text() if self.table.item(row, 0) else "Unknown"
            )
            unit = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            qty = (
                float(self.table.item(row, 2).text()) if self.table.item(row, 2) else 0
            )
            price = (
                float(self.table.item(row, 3).text()) if self.table.item(row, 3) else 0
            )
            item_id = (
                self.table.item(row, 0).data(Qt.UserRole)
                if self.table.item(row, 0)
                else None
            )
            items.append(
                {
                    "item_id": item_id,
                    "name": name,
                    "unit": unit,
                    "quantity": qty,
                    "amount": price * qty,
                }
            )
        return items

    def add_to_cart(self):
        cart_items = self.get_cart_items()
        if not cart_items:
            QMessageBox.warning(
                self, "Error", "No items in cart to add!", QMessageBox.Ok
            )
            return

        total_amount = sum(item["amount"] for item in cart_items)
        customer_type_name = self.customer_type.currentText()
        customer_type_id = next(
            (
                ct["id"]
                for ct in self.customer_types_data
                if ct["name"] == customer_type_name
            ),
            None,
        )
        if not customer_type_id:
            QMessageBox.critical(
                self, "Error", "Invalid customer type selected!", QMessageBox.Ok
            )
            return

        customer_id = None
        if self.customer_select.isVisible():
            customer_id = self.customer_select.currentData()

        order_number = f"CART-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cart_data = {
            "order_number": order_number,
            "customer_type_id": customer_type_id,
            "customer_id": customer_id,
            "total_amount": total_amount,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": cart_items,
            "status": "in-cart",
        }

        result = self.cart_model.create_cart(cart_data)
        if result["success"]:
            QMessageBox.information(
                self,
                "Success",
                f"Cart saved successfully with ID: {result['cart_id']}",
                QMessageBox.Ok,
            )
            self.clear_checkout()
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save cart: {result['message']}",
                QMessageBox.Ok,
            )

    def open_sales_view(self):
        print("Switching to Sales View (Dashboard)")
        self.stacked_widget.setCurrentIndex(0)

    def open_sales_summary_view(self):
        print("Switching to Sales Summary View")
        cart_items = self.get_cart_items()
        orders = []
        for idx, item in enumerate(cart_items):
            total_amount = item["amount"]
            orders.append(
                {
                    "order_no": f"ORD-{idx + 1:03d}",
                    "time": QDateTime.currentDateTime().toString("hh:mm:ss"),
                    "receipt_no": f"REC-{idx + 1:03d}",
                    "status": "Completed",
                    "total_amount": total_amount,
                }
            )
        self.order_summary_view.set_orders(orders)
        self.stacked_widget.setCurrentIndex(self.order_summary_index)

    def open_delivery_view(self):
        print("Switching to Delivery View")
        cart_items = self.get_cart_items()
        orders = []
        for idx, item in enumerate(cart_items):
            total_amount = item["amount"]
            orders.append(
                {
                    "order_no": f"DEL-{idx + 1:03d}",
                    "time": QDateTime.currentDateTime().toString("hh:mm:ss"),
                    "receipt_no": f"REC-{idx + 1:03d}",
                    "status": "Pending Delivery",
                    "total_amount": total_amount,
                }
            )
        self.order_summary_view.set_orders(orders)
        self.stacked_widget.setCurrentIndex(self.order_summary_index)

    def toggle_search_mode(self):
        self.is_barcode_mode = not self.is_barcode_mode
        if self.is_barcode_mode:
            self.mode_switch.setText("Barcode Mode")
            self.product_search.setEnabled(False)
            self.product_barcode_search.setEnabled(True)
            self.product_barcode_search.setFocus()
            self.product_search.clear()
        else:
            self.mode_switch.setText("Search Mode")
            self.product_search.setEnabled(True)
            self.product_barcode_search.setEnabled(False)
            self.product_search.setFocus()
            self.product_barcode_search.clear()

    # def on_sync_switch_changed(self, state):
    #     """Handle toggle switch state change."""
    #     is_enabled = bool(state)
    #     print(f"Sync toggled: {'ON' if is_enabled else 'OFF'}")
    #     self.update_sync_indicator("gray", "Sync Status: Unknown")
    #     if is_enabled:
    #         self.sync_timer.start(10000)
    #         self.start_sync_thread()
    #     else:
    #         self.sync_timer.stop()
    #         if self.sync_thread and self.sync_thread.isRunning():
    #             self.sync_thread.quit()
    #             self.sync_thread.wait()
    #         self.update_sync_indicator("orange", "Sync Disabled")

    # def start_sync_thread(self):
    #     """Start synchronization based on toggle state."""
    #     if self.sync_thread and self.sync_thread.isRunning():
    #         print("Sync already in progress, skipping.")
    #         return

    #     if self.sync_switch.isChecked():
    #         if self.is_internet_available():
    #             print("Internet available, starting full sync...")
    #             self.update_sync_indicator("yellow", "Syncing...")
    #             self.sync_thread = SyncWorker(force_full_sync=True)
    #             self.sync_thread.sync_finished.connect(self.on_sync_finished)
    #             self.sync_thread.start()
    #         else:
    #             print("No internet connection, skipping sync")
    #             self.update_sync_indicator("red", "No Internet")
    #     else:
    #         if self.is_internet_available():
    #             print("Sync toggle OFF: Starting partial sync...")
    #             self.update_sync_indicator("yellow", "Partial Syncing...")
    #             self.sync_thread = SyncWorker(force_full_sync=False)
    #             self.sync_thread.sync_finished.connect(self.on_sync_finished)
    #             self.sync_thread.start()
    #         else:
    #             print("No internet, sync disabled")
    #             self.update_sync_indicator("orange", "Sync Disabled, No Internet")

    # def on_sync_finished(self, success):
    #     """Handle sync completion."""
    #     if success:
    #         print("Sync successful")
    #         self.update_sync_indicator("green", "Sync Successful")
    #         self.update_ui_after_sync()
    #     else:
    #         print("Sync failed")
    #         self.update_sync_indicator("red", "Sync Failed")
    #     self.sync_thread = None

    # def update_sync_indicator(self, color, tooltip):
    #     """Update the LED indicator."""
    #     self.sync_status_indicator.setStyleSheet(
    #         f"background-color: {color}; border-radius: 5px;"
    #     )
    #     self.sync_status_indicator.setToolTip(tooltip)
    #     QApplication.processEvents()

    # def check_internet_on_startup(self):
    #     if not self.is_internet_available():
    #         QMessageBox.warning(
    #             self,
    #             "Offline Mode",
    #             "No internet connection detected. Working in offline mode.",
    #             QMessageBox.Ok,
    #         )

    # def is_internet_available(self):
    #     try:
    #         socket.create_connection(("www.google.com", 80), timeout=2)
    #         return True
    #     except OSError:
    #         return False

    # def update_ui_after_sync(self):
    #     self.sidebar.update_group_buttons(db.get_local_item_groups())
    #     if self.current_category_id:
    #         self.update_product_grid(self.current_category_id)
    #     self.customer_types_data = db.get_customer_types()
    #     self.customers_data = db.get_customers()
    #     self.customer_type.clear()
    #     self.customer_type.addItems([ct["name"] for ct in self.customer_types_data])
    #     self.populate_customers_combobox()
    #     self.refresh_product_cards()

    def refresh_product_cards(self):
        if self.current_category_id:
            items = db.get_local_items_for_category(self.current_category_id)
            self.current_items = items
            self.update_product_grid(self.current_category_id)

    def populate_customers_combobox(self):
        self.customer_select.clear()
        self.customer_select.addItem("Walk-in Customer", None)
        for customer in self.customers_data:
            self.customer_select.addItem(customer["name"], customer["id"])

    def on_customer_type_changed(self, text):
        is_registered = text.lower() == "registered"
        self.customer_select.setVisible(is_registered)
        self.customer_label.setVisible(is_registered)
        if not is_registered:
            self.customer_select.setCurrentIndex(0)

    def update_category_cards(self, group_name):
        for i in reversed(range(self.category_layout.count())):
            widget = self.category_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        categories = db.get_local_categories_for_group(group_name)
        if categories:
            for idx, category in enumerate(categories):
                btn = QPushButton(category["name"])
                btn.setStyleSheet(
                    """
                    QPushButton { background-color: #f0f0f0; color: #333333; border: 1px solid #ddd; border-radius: 5px; padding: 8px; font-size: 14px; min-width: 80px; min-height: 20px; }
                    QPushButton:hover { background-color: #e0e0e0; border: 1px solid #3498db; }
                    QPushButton:pressed { background-color: #d0d0d0; }
                    """
                )
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(
                    lambda checked, cid=category["id"]: self.update_product_grid(cid)
                )
                self.category_layout.addWidget(btn)
                if idx == 0:
                    self.update_product_grid(category["id"])
        else:
            no_data_label = QLabel("No categories available")
            no_data_label.setStyleSheet("color: #7f8c8d; padding: 8px;")
            self.category_layout.addWidget(no_data_label)
        self.category_layout.addStretch()

    def update_product_grid(self, category_id, filtered_items=None):
        self.current_category_id = category_id
        for i in reversed(range(self.product_grid.count())):
            widget = self.product_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if filtered_items is None:
            items = db.get_local_items_for_category(category_id)
            self.current_items = items
        else:
            items = filtered_items

        print(f"Updating grid with {len(items)} items for category {category_id}")

        self.product_cards.clear()
        if items:
            row, col = 0, 0
            added_item_ids = set()
            for item in items:
                item_id = item["item_id"]
                if item_id in added_item_ids:
                    print(
                        f"Skipping duplicate item: {item['item_name']} (ID: {item_id})"
                    )
                    continue

                print(f"Adding item: {item['item_name']}")
                card = ProductCard(item)
                card.clicked.connect(self.add_item_to_checkout)
                self.product_grid.addWidget(card, row, col, alignment=Qt.AlignTop)
                self.product_cards[item_id] = card
                added_item_ids.add(item_id)
                col += 1
                if col > 4:
                    col = 0
                    row += 1
                if row > 3 and col == 0:
                    break
        else:
            print("No items to display")
            no_items_label = QLabel("No items available")
            no_items_label.setStyleSheet("color: #7f8c8d; padding: 10px;")
            self.product_grid.addWidget(no_items_label, 0, 0, alignment=Qt.AlignTop)
        self.product_grid.parentWidget().adjustSize()

    def filter_products(self, text):
        """Filter products globally across all items based on search text."""
        if not text.strip():
            # If search text is empty, revert to current category view
            if self.current_category_id:
                self.update_product_grid(self.current_category_id)
            return

        # Fetch all items from the database
        all_items = db.get_all_local_items()
        if not all_items:
            print("No items found in database for global search")
            self.update_product_grid(self.current_category_id, [])
            return

        # Filter items based on 'name' (case-insensitive)
        filtered_items = [
            item
            for item in all_items
            if text.lower() in item.get("name", "Unnamed Item").lower()
        ]

        # Deduplicate items by 'id' and adapt to expected UI structure
        seen_item_ids = set()
        deduplicated_filtered_items = []
        for item in filtered_items:
            item_id = item.get("id")
            if item_id and item_id not in seen_item_ids:
                # Transform to match UI expected structure
                ui_item = {
                    "item_id": item_id,
                    "item_name": item.get("name", "Unnamed Item"),
                    "item_unit": item.get("selling_unit_name", ""),
                    "item_price": (
                        list(item.get("prices", {}).values())[0]
                        if item.get("prices")
                        else 0.0
                    ),
                    "stock_quantity": (
                        list(item.get("stocks", {}).values())[0].get(
                            "stock_quantity", 0.0
                        )
                        if item.get("stocks")
                        else 0.0
                    ),
                }
                deduplicated_filtered_items.append(ui_item)
                seen_item_ids.add(item_id)

        self.update_product_grid(None, deduplicated_filtered_items)
        print(
            f"Filtered {len(deduplicated_filtered_items)} items globally with query: '{text}'"
        )

    def add_item_to_checkout(self, item):
        try:
            item_id = item["item_id"]
            if not item_id:
                raise ValueError(f"No item ID found in {item}")
            stock_quantity = float(item["stock_quantity"])
            if stock_quantity <= 0:
                QMessageBox.warning(
                    self,
                    "Out of Stock",
                    f"{item['item_name']} is out of stock!",
                    QMessageBox.Ok,
                )
                return

            # Check if item already exists in the table
            for row in range(self.table.rowCount()):
                name_item = self.table.item(row, 0)
                if name_item and name_item.text() == item["item_name"]:
                    qty_item = self.table.item(row, 2)
                    current_qty = float(qty_item.text())

                    if current_qty + 1 > stock_quantity:
                        QMessageBox.warning(
                            self,
                            "Stock Limit",
                            f"Only {stock_quantity} {item['item_name']} available!",
                            QMessageBox.Ok,
                        )
                        return

                    qty_item.setText(str(int(current_qty + 1)))
                    if not name_item.data(Qt.UserRole):
                        name_item.setData(Qt.UserRole, item_id)
                    self.update_totals()
                    print(
                        f"Updated quantity for {item['item_name']} in checkout, Item ID: {name_item.data(Qt.UserRole)}"
                    )
                    return

            # Add new item to the table
            row_count = self.table.rowCount()
            self.table.insertRow(row_count)

            name_item = QTableWidgetItem(item["item_name"])
            name_item.setData(Qt.UserRole, item_id)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Non-editable

            unit_item = QTableWidgetItem(item["item_unit"])
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)  # Non-editable

            qty_item = QTableWidgetItem("1")
            qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)  # Editable

            price_item = QTableWidgetItem(f"{float(item['item_price']):.2f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)  # Non-editable

            self.table.setItem(row_count, 0, name_item)
            self.table.setItem(row_count, 1, unit_item)
            self.table.setItem(row_count, 2, qty_item)
            self.table.setItem(row_count, 3, price_item)

            remove_btn = QPushButton()
            remove_btn.setIcon(
                load_icon(get_resource_path("Resources/Images/trash_icon.png"))
            )
            remove_btn.setIconSize(QSize(16, 16))
            remove_btn.setStyleSheet(
                "QPushButton { border-radius: 4px; padding: 2px; min-width: 24px; min-height: 24px; } QPushButton:hover { background: #c82333; }"
            )
            remove_btn.clicked.connect(lambda _, r=row_count: self.remove_item(r))
            self.table.setCellWidget(row_count, 4, remove_btn)

            print(
                f"Added {item['item_name']} to checkout at row {row_count}, Item ID: {self.table.item(row_count, 0).data(Qt.UserRole)}"
            )
            self.update_totals()

            # Connect itemChanged signal to handle quantity edits
            if not self.table.receivers(self.table.itemChanged):
                self.table.itemChanged.connect(self.handle_quantity_change)

        except Exception as e:
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self, "Error", f"Failed to add item: {str(e)}", QMessageBox.Ok
            )

    def handle_quantity_change(self, item):
        try:
            if item.column() != 2:  # Only handle changes in the "Qty" column
                return

            row = item.row()
            name_item = self.table.item(row, 0)
            if not name_item:
                return

            item_id = name_item.data(Qt.UserRole)
            if not item_id:
                QMessageBox.warning(self, "Error", "Item ID not found!", QMessageBox.Ok)
                return

            # Get item details from the database
            item_data = db.get_item_by_id(item_id)
            if not item_data:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Item with ID {item_id} not found in database!",
                    QMessageBox.Ok,
                )
                return

            stock_quantity = float(item_data["stock_quantity"])
            new_qty_text = item.text().strip()

            # Validate the new quantity
            try:
                new_qty = float(new_qty_text)
                if new_qty <= 0:
                    QMessageBox.warning(
                        self,
                        "Invalid Quantity",
                        "Quantity must be greater than 0!",
                        QMessageBox.Ok,
                    )
                    item.setText("1")  # Reset to default
                    self.update_totals()
                    return
                if new_qty > stock_quantity:
                    QMessageBox.warning(
                        self,
                        "Stock Limit",
                        f"Only {stock_quantity} {item_data['item_name']} available!",
                        QMessageBox.Ok,
                    )
                    item.setText(str(int(stock_quantity)))  # Set to max available
                    self.update_totals()
                    return
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Please enter a valid number!",
                    QMessageBox.Ok,
                )
                item.setText("1")  # Reset to default
                self.update_totals()
                return

            self.update_totals()
            print(f"Quantity updated for {item_data['item_name']} to {new_qty}")

        except Exception as e:
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self, "Error", f"Failed to update quantity: {str(e)}", QMessageBox.Ok
            )

    def update_totals(self):
        try:
            subtotal = 0.0
            for row in range(self.table.rowCount()):
                qty_item = self.table.item(row, 2)
                if not qty_item or not qty_item.text():
                    continue
                qty = float(qty_item.text())

                price_item = self.table.item(row, 3)
                if not price_item or not price_item.text():
                    continue
                price = float(price_item.text().replace(",", "").strip())

                subtotal += qty * price

            self.subtotal_label.setText(f"{subtotal:.2f}")
            self.total_label.setText(f"{subtotal:.2f}")
            QApplication.processEvents()

        except Exception as e:
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self, "Error", f"Unexpected error in update_totals: {e}", QMessageBox.Ok
            )

    def remove_item(self, row):
        if row < self.table.rowCount():
            self.table.removeRow(row)
            self.update_totals()

    def open_payment_card(self):
        total = float(self.total_label.text())
        if total > 0:
            self.payment_card.total_amount = total
            self.payment_card.total_amount_label.setText(f"TOTAL AMOUNT: {total:.2f}")
            self.payment_card.update_ground_total()
            self.payment_card.tip = 0.0
            self.payment_card.discount = 0.0
            self.payment_card.tip_input.setText("0")
            self.payment_card.discount_input.setText("0")
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.payment_card.order_no_label.setText(f"Order No: {order_number}")
            self.payment_card.date_label.setText(
                f"Date: {datetime.now().strftime('%d/%m/%Y')}"
            )
            self.checkout_widget.setVisible(False)
            self.payment_card.setVisible(True)
        else:
            QMessageBox.warning(self, "Error", "No items in cart to check out!")

    def clear_checkout(self):
        self.table.setRowCount(0)
        self.subtotal_label.setText("0.00")
        self.total_label.setText("0.00")

    def open_printer_settings(self):
        settings_window = PrinterSettingsWindow(self, db=db)
        settings_window.exec_()

    def handle_barcode_input(self, text):
        barcode_text = text.strip()
        print(f"Received input: {barcode_text}")
        if barcode_text:
            print("Processing barcode...")
            self.pending_barcode = barcode_text
            self.barcode_timer.stop()
            self.barcode_timer.start(700)

    def process_pending_barcode(self):
        if not hasattr(self, "pending_barcode") or not self.pending_barcode:
            print("No barcode to process")
            return

        barcode = self.pending_barcode
        print(f"Processing barcode: {barcode}")

        try:
            self.product_barcode_search.textChanged.disconnect(
                self.handle_barcode_input
            )
        except TypeError:
            pass

        try:
            print(f"Calling db.get_item_by_barcode with barcode: '{barcode}'")
            item = db.get_item_by_barcode(barcode)
            print(f"Returned item from database: {item}")

            if item is None or not isinstance(item, dict):
                print(f"Invalid item data for barcode '{barcode}': {item}")
                QMessageBox.warning(
                    self,
                    "Item Not Found",
                    f"No item found with barcode '{barcode}'.",
                    QMessageBox.Ok,
                )
                return

            required_fields = [
                "item_name",
                "item_unit",
                "item_price",
                "stock_quantity",
                "item_id",
            ]
            missing_fields = [
                field
                for field in required_fields
                if field not in item or item[field] is None
            ]
            if missing_fields:
                print(f"Missing fields: {missing_fields}")
                QMessageBox.warning(
                    self,
                    "Data Error",
                    f"Missing fields: {', '.join(missing_fields)}",
                    QMessageBox.Ok,
                )
                return

            stock_quantity = float(item["stock_quantity"])
            if stock_quantity <= 0:
                QMessageBox.warning(
                    self,
                    "Out of Stock",
                    f"{item.get('item_name', 'Unknown')} is out of stock!",
                    QMessageBox.Ok,
                )
                return

            print(f"Adding item to checkout: {item}")
            self.add_item_to_checkout(item)

        except Exception as e:
            print(f"Error processing barcode: {str(e)}")
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Error",
                f"Barcode processing failed: {str(e)}",
                QMessageBox.Ok,
            )
        finally:
            self.pending_barcode = ""
            self.product_barcode_search.clear()
            self.product_barcode_search.setFocus()
            self.product_barcode_search.textChanged.connect(self.handle_barcode_input)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Tab, Qt.Key_Escape):
            super().keyPressEvent(event)
        else:
            if (
                not self.product_search.hasFocus()
                and not self.customer_select.hasFocus()
            ):
                if self.is_barcode_mode:
                    self.product_barcode_search.setFocus()
                else:
                    self.product_search.setFocus()
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardView()
    window.show()
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Application crashed: {e}")
        import traceback

        traceback.print_exc()
