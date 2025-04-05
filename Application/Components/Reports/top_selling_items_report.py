# top_selling_items_report.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QTableView,
    QAbstractItemView,
    QFileDialog,
    QMessageBox,
    QComboBox,
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

REPORTLAB_INSTALLED = True


class TopSellingItemsReport(QWidget):
    def __init__(self, report_manager, stores_data):
        super().__init__()
        self.report_manager = report_manager
        self.stores_data = stores_data
        self.stores = ["All Stores"] + [store["name"] for store in self.stores_data]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Top Selling Items Report")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Store Filter Section
        store_filter_layout = QHBoxLayout()
        self.store_label = QLabel("Filter by Store:")
        self.store_combo = QComboBox()
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
        self.generate_report_button.clicked.connect(self.generate_top_selling_items)

        date_filter_layout.addWidget(self.start_date_label)
        date_filter_layout.addWidget(self.start_date_edit)
        date_filter_layout.addWidget(self.end_date_label)
        date_filter_layout.addWidget(self.end_date_edit)
        date_filter_layout.addWidget(self.generate_report_button)
        date_filter_layout.addStretch(1)
        layout.addLayout(date_filter_layout)

        # Report Table
        self.top_items_table_view = QTableView()
        self.top_items_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.top_items_table_view)

        # Download Option
        download_layout = QHBoxLayout()
        download_layout.addStretch(1)
        self.download_button = QPushButton("Download as PDF")
        self.download_button.clicked.connect(self.download_top_selling_items_pdf)
        download_layout.addWidget(self.download_button)
        layout.addLayout(download_layout)

        self.setLayout(layout)

    def generate_top_selling_items(self):
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        selected_store_name = self.store_combo.currentText()
        selected_store_id = None
        if selected_store_name != "All Stores":
            for store in self.stores_data:
                if store["name"] == selected_store_name:
                    selected_store_id = store["id"]
                    break

        top_items_data = self.report_manager.get_top_selling_items_data(
            start_date, end_date, selected_store_id
        )

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            [
                "Item Name",
                "Total Quantity Sold",
                "Total Revenue",
                "Average Price",
            ]
        )

        for item in top_items_data:
            row = [
                QStandardItem(item["item_name"]),
                QStandardItem(str(item["total_quantity"])),
                QStandardItem(f"{item['total_revenue']:.2f}"),
                QStandardItem(f"{item['average_price']:.2f}"),
            ]
            model.appendRow(row)

        self.top_items_table_view.setModel(model)
        self.top_items_table_view.horizontalHeader().setStretchLastSection(True)
        self.top_items_table_view.resizeColumnsToContents()

    def download_top_selling_items_pdf(self):
        if not REPORTLAB_INSTALLED:
            QMessageBox.critical(
                self,
                "Error",
                "Reportlab is not installed. Please install it using 'pip install reportlab'.",
            )
            return

        model = self.top_items_table_view.model()
        if model is None:
            QMessageBox.warning(
                self, "No Data", "No top selling items data to download."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Top Selling Items Report as PDF", "", "PDF (*.pdf)"
        )

        if file_path:
            if not file_path.lower().endswith(".pdf"):
                file_path += ".pdf"

            try:
                doc = SimpleDocTemplate(
                    file_path,
                    pagesize=letter,
                    rightMargin=0.75 * inch,
                    leftMargin=0.75 * inch,
                    topMargin=1 * inch,
                    bottomMargin=0.75 * inch,
                )

                styles = getSampleStyleSheet()
                normal_style = styles["Normal"]
                title_style = styles["Heading1"]
                subtitle_style = styles["Heading3"]
                normal_style.alignment = TA_CENTER
                title_style.alignment = TA_CENTER
                subtitle_style.alignment = TA_CENTER

                company_details = self.report_manager.get_company_details()
                story = []

                if company_details and company_details[0]:
                    company_info = company_details[0]
                    story.append(
                        Paragraph(f"<b>{company_info['company_name']}</b>", title_style)
                    )
                    story.append(Paragraph(company_info["address"], normal_style))
                    if company_info["state"]:
                        story.append(Paragraph(company_info["state"], normal_style))
                    if company_info["phone"]:
                        story.append(
                            Paragraph(f"Phone: {company_info['phone']}", normal_style)
                        )
                    story.append(Spacer(1, 0.25 * inch))

                story.append(Paragraph("<b>Top Selling Items Report</b>", title_style))
                start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
                end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
                store_name = self.store_combo.currentText()
                story.append(
                    Paragraph(f"Period: {start_date} to {end_date}", subtitle_style)
                )
                story.append(Paragraph(f"Store: {store_name}", subtitle_style))
                story.append(Spacer(1, 0.3 * inch))

                table_data = []
                headers = [
                    model.horizontalHeaderItem(i).text()
                    for i in range(model.columnCount())
                ]
                table_data.append(headers)

                for row in range(model.rowCount()):
                    row_data = [
                        model.item(row, col).text()
                        for col in range(model.columnCount())
                    ]
                    table_data.append(row_data)

                col_widths = [
                    1.5 * inch,
                    1.2 * inch,
                    1.2 * inch,
                    1.2 * inch,
                ]  # Adjusted for readability
                table = Table(table_data, colWidths=col_widths)
                table.setStyle(
                    TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, 0),
                                colors.Color(0.2, 0.3, 0.5),
                            ),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                            ("TOPPADDING", (0, 0), (-1, 0), 8),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 1), (-1, -1), 9),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                            ("ALIGN", (0, 0), (0, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )

                story.append(table)

                def add_footer(canvas, doc):
                    canvas.saveState()
                    canvas.setFont("Helvetica", 8)
                    canvas.setFillGray(0.4)
                    page_num = canvas.getPageNumber()
                    text = f"Page {page_num} | Generated on {QDate.currentDate().toString('yyyy-MM-dd')}"
                    canvas.drawCentredString(letter[0] / 2, 0.5 * inch, text)
                    canvas.restoreState()

                doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Top selling items report downloaded to: {file_path}",
                )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving PDF: {e}")
