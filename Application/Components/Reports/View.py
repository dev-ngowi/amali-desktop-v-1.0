import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QTextEdit,
    QListWidget,
    QStackedWidget,
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QComboBox,
)
from PyQt5.QtCore import QDate, Qt, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import csv

from Application.Components.Reports.modal import ReportManager

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
except ImportError:
    REPORTLAB_INSTALLED = False
else:
    REPORTLAB_INSTALLED = True


class ReportView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Report View")
        self.setGeometry(100, 100, 900, 700)

        self.report_manager = ReportManager()
        self.stores_data = self.report_manager.get_stores_data()
        self.stores = ["All Stores"] + [store["name"] for store in self.stores_data]

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.addItem("Sales Summary")
        self.sidebar.addItem("Sale Detailed Report")
        self.sidebar.addItem("Stocks Reports")
        self.sidebar.addItem("Top Selling Items Reports")
        self.sidebar.currentRowChanged.connect(self.switch_report_view)
        main_layout.addWidget(self.sidebar)

        # Main Report Area
        self.report_area = QStackedWidget()

        # Sales Summary View
        self.sales_summary_view = QWidget()
        self.init_sales_summary_ui()
        self.report_area.addWidget(self.sales_summary_view)

        # Placeholder Views
        self.sale_detailed_report_view = QLabel("Sale Detailed Report View")
        self.report_area.addWidget(self.sale_detailed_report_view)

        self.stocks_reports_view = QLabel("Stocks Reports View")
        self.report_area.addWidget(self.stocks_reports_view)

        self.top_selling_items_view = QLabel("Top Selling Items Reports View")
        self.report_area.addWidget(self.top_selling_items_view)

        main_layout.addWidget(self.report_area)

        main_layout.setStretch(0, 2)  # Sidebar 20%
        main_layout.setStretch(1, 8)  # Report area 80%

        self.setLayout(main_layout)

    def init_sales_summary_ui(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Sales Summary")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Store Filter Section
        store_filter_layout = QHBoxLayout()
        self.store_label = QLabel("Filter by Store:")
        self.store_combo = QComboBox()
        self.store_combo.addItem("All Stores")
        self.store_combo.addItems(self.stores)
        store_filter_layout.addWidget(self.store_label)
        store_filter_layout.addWidget(self.store_combo)
        store_filter_layout.addStretch(1)
        layout.addLayout(store_filter_layout)

        # Date Filter Section
        date_filter_layout = QHBoxLayout()

        self.start_date_label = QLabel("Start Date:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")

        self.end_date_label = QLabel("End Date:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")

        self.generate_report_button = QPushButton("Generate Report")
        self.generate_report_button.clicked.connect(self.generate_sales_summary)

        date_filter_layout.addWidget(self.start_date_label)
        date_filter_layout.addWidget(self.start_date_edit)
        date_filter_layout.addWidget(self.end_date_label)
        date_filter_layout.addWidget(self.end_date_edit)
        date_filter_layout.addWidget(self.generate_report_button)
        date_filter_layout.addStretch(1)

        layout.addLayout(date_filter_layout)

        # Report Table
        self.summary_table_view = QTableView()
        self.summary_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.summary_table_view)

        # Download Option
        download_layout = QHBoxLayout()
        download_layout.addStretch(1)
        self.download_button = QPushButton("Download as PDF")
        self.download_button.clicked.connect(self.download_sales_summary_pdf)
        download_layout.addWidget(self.download_button)
        layout.addLayout(download_layout)

        self.sales_summary_view.setLayout(layout)

    def switch_report_view(self, index):
        self.report_area.setCurrentIndex(index)
        if index == 0:
            pass  # Report generation tied to button
        elif index == 1:
            self.display_sale_detailed_report()
        elif index == 2:
            self.display_stocks_reports()
        elif index == 3:
            self.display_top_selling_items()

    def display_sale_detailed_report(self):
        self.sale_detailed_report_view.setText(
            "Implementation for Sale Detailed Report will go here."
        )

    def display_stocks_reports(self):
        self.stocks_reports_view.setText(
            "Implementation for Stocks Reports will go here."
        )

    def display_top_selling_items(self):
        self.top_selling_items_view.setText(
            "Implementation for Top Selling Items Reports will go here."
        )

    def generate_sales_summary(self):
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        selected_store_name = self.store_combo.currentText()
        selected_store_id = None
        if selected_store_name != "All Stores":
            for store in self.stores_data:
                if store["name"] == selected_store_name:
                    selected_store_id = store["id"]
                    break

        sales_data = self.report_manager.get_sales_summary_data(
            start_date, end_date, selected_store_id
        )

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            [
                "Date",
                "Sub Total",
                "Tax Total",
                "Discount",
                "Others",
                "Tip",
                "Final Total",
                "Payment Total",
                "Amount Due",
            ]
        )

        total_sub_total = 0
        total_tax_total = 0
        total_discount = 0
        total_others = 0
        total_tip = 0
        total_final_total = 0
        total_payment_total = 0
        total_amount_due = 0

        for sale in sales_data:
            date = sale["date"]
            sub_total = sale.get("sub_total", 0.00)
            tax_total = sale.get("tax_total", 0.00)
            discount = sale.get("discount", 0.00)
            others = sale.get("others", 0.00)
            tip = sale.get("tip", 0.00)
            final_total = sale.get("ground_total", 0.00)
            payment_total = sale.get("payment_total", 0.00)
            amount_due = sale.get("amount_due", 0.00)

            row = [
                QStandardItem(date),
                QStandardItem(f"{sub_total:.2f}"),
                QStandardItem(f"{tax_total:.2f}"),
                QStandardItem(f"{discount:.2f}"),
                QStandardItem(f"{others:.2f}"),
                QStandardItem(f"{tip:.2f}"),
                QStandardItem(f"{final_total:.2f}"),
                QStandardItem(f"{payment_total:.2f}"),
                QStandardItem(f"{amount_due:.2f}"),
            ]
            model.appendRow(row)

            total_sub_total += sub_total
            total_tax_total += tax_total
            total_discount += discount
            total_others += others
            total_tip += tip
            total_final_total += final_total
            total_payment_total += payment_total
            total_amount_due += amount_due

        grand_total_row = [
            QStandardItem(""),
            QStandardItem("Grand Total"),
            QStandardItem(f"{total_tax_total:.2f}"),
            QStandardItem(f"{total_discount:.2f}"),
            QStandardItem(f"{total_others:.2f}"),
            QStandardItem(f"{total_tip:.2f}"),
            QStandardItem(f"{total_final_total:.2f}"),
            QStandardItem(f"{total_payment_total:.2f}"),
            QStandardItem(f"{total_amount_due:.2f}"),
        ]
        model.appendRow(grand_total_row)

        grand_total_row_index = model.rowCount() - 1
        self.summary_table_view.setSpan(grand_total_row_index, 0, 1, 2)

        self.summary_table_view.setModel(model)
        self.summary_table_view.horizontalHeader().setStretchLastSection(True)
        self.summary_table_view.resizeColumnsToContents()
        self.summary_table_view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Interactive
        )
        for i in range(1, model.columnCount()):
            self.summary_table_view.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.Stretch
            )

    def download_sales_summary_pdf(self):
        if not REPORTLAB_INSTALLED:
            QMessageBox.critical(
                self,
                "Error",
                "Reportlab is not installed. Please install it using 'pip install reportlab'.",
            )
            return

        model = self.summary_table_view.model()
        if model is None:
            QMessageBox.warning(self, "No Data", "No sales summary data to download.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Sales Summary as PDF", "", "PDF (*.pdf)"
        )

        if file_path:
            if not file_path.lower().endswith(".pdf"):
                file_path += ".pdf"

            try:
                doc = SimpleDocTemplate(file_path, pagesize=letter)
                styles = getSampleStyleSheet()
                centered_style = styles["Normal"]
                centered_style.alignment = TA_CENTER

                company_details = self.report_manager.get_company_details()
                company_name = ""
                address_lines = []
                if company_details:
                    company_info = company_details[0]
                    company_name = Paragraph(
                        f"<b>{company_info['company_name']}</b>", centered_style
                    )
                    address_lines.append(
                        Paragraph(company_info["address"], centered_style)
                    )
                    if company_info["state"]:
                        address_lines.append(
                            Paragraph(company_info["state"], centered_style)
                        )
                    if company_info["phone"]:
                        address_lines.append(
                            Paragraph(f"Phone: {company_info['phone']}", centered_style)
                        )

                report_title = Paragraph("<b>Sales Summary</b>", centered_style)

                story = []
                if company_name:
                    story.append(company_name)
                    for line in address_lines:
                        story.append(line)
                    story.append(Spacer(1, 0.2 * inch))
                story.append(report_title)
                story.append(Spacer(1, 0.2 * inch))

                table_data = []
                header = [
                    model.horizontalHeaderItem(i).text()
                    for i in range(model.columnCount())
                ]
                table_data.append(header)
                for row in range(model.rowCount()):
                    row_data = [
                        model.item(row, col).text()
                        for col in range(model.columnCount())
                    ]
                    table_data.append(row_data)
                if table_data and table_data[-1][1] == "Grand Total":
                    last_row = table_data[-1]
                    grand_total_label = last_row[1]
                    totals = last_row[2:]
                    table_data[-1] = ["", grand_total_label] + totals

                table = Table(table_data)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("BACKGROUND", (0, 1), (-1, -2), colors.beige),
                            ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                            ("SPAN", (0, -1), (1, -1)),
                        ]
                    )
                )

                story.append(table)
                doc.build(story)
                QMessageBox.information(
                    self, "Success", f"Sales summary downloaded to: {file_path}"
                )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving PDF: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReportView()
    window.show()
    sys.exit(app.exec_())
