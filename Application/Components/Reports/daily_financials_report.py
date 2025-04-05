# daily_financials_report.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

REPORTLAB_INSTALLED = True


class DailyFinancialsReport(QWidget):
    def __init__(self, report_manager):
        super().__init__()
        self.report_manager = report_manager
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # Header Section
        header_layout = QHBoxLayout()
        title_label = QLabel("Daily Financials Report")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)

        # Filter Section
        filter_group = QGroupBox("Filters")
        filter_layout = QGridLayout()
        filter_layout.setHorizontalSpacing(10)
        filter_layout.setVerticalSpacing(10)

        # Date Range
        self.start_date_label = QLabel("Start Date:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))  # Default: 1 month ago
        filter_layout.addWidget(self.start_date_label, 0, 0)
        filter_layout.addWidget(self.start_date_edit, 0, 1)

        self.end_date_label = QLabel("End Date:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())  # Default: today
        filter_layout.addWidget(self.end_date_label, 0, 2)
        filter_layout.addWidget(self.end_date_edit, 0, 3)

        filter_layout.setColumnStretch(4, 1)  # Stretch remaining space
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)

        # Button Section
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate Report")
        self.generate_button.clicked.connect(self.generate_financials)
        self.generate_button.setMinimumWidth(150)
        button_layout.addStretch(1)
        button_layout.addWidget(self.generate_button)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)
        main_layout.addSpacing(10)

        # Table Section
        self.financials_table = QTableView()
        self.financials_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.financials_table.setMinimumHeight(300)
        main_layout.addWidget(self.financials_table, stretch=1)

        # Download Section
        download_layout = QHBoxLayout()
        self.download_button = QPushButton("Download as PDF")
        self.download_button.clicked.connect(self.download_financials_pdf)
        self.download_button.setMinimumWidth(150)
        download_layout.addStretch(1)
        download_layout.addWidget(self.download_button)
        download_layout.addStretch(1)
        main_layout.addLayout(download_layout)

        self.setLayout(main_layout)

    def generate_financials(self):
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        financials_data = self.report_manager.get_daily_financials_data(
            start_date=start_date,
            end_date=end_date
        )

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            [
                "Date",
                "Total Orders",
                "Total Expenses",
                "After Expenses",
            ]
        )

        for entry in financials_data:
            row = [
                QStandardItem(entry["date"]),
                QStandardItem(f"{entry['total_orders']:.2f}"),
                QStandardItem(f"{entry['total_expenses']:.2f}"),
                QStandardItem(f"{entry['after_expenses']:.2f}"),
            ]
            model.appendRow(row)

        self.financials_table.setModel(model)
        self.financials_table.horizontalHeader().setStretchLastSection(True)
        self.financials_table.resizeColumnsToContents()

    def download_financials_pdf(self):
        if not REPORTLAB_INSTALLED:
            QMessageBox.critical(
                self,
                "Error",
                "Reportlab is not installed. Please install it using 'pip install reportlab'.",
            )
            return

        model = self.financials_table.model()
        if model is None:
            QMessageBox.warning(self, "No Data", "No daily financials data to download.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Daily Financials Report as PDF", "", "PDF (*.pdf)"
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

                cell_style = styles["Normal"]
                cell_style.alignment = TA_RIGHT  # Right-align numeric columns
                cell_style.fontSize = 9
                cell_style.leading = 10

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

                story.append(Paragraph("<b>Daily Financials Report</b>", title_style))
                start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
                end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
                story.append(Paragraph(f"From: {start_date} To: {end_date}", subtitle_style))
                story.append(Spacer(1, 0.3 * inch))

                table_data = []
                headers = [
                    model.horizontalHeaderItem(i).text()
                    for i in range(model.columnCount())
                ]
                table_data.append(headers)

                for row in range(model.rowCount()):
                    row_data = []
                    for col in range(model.columnCount()):
                        text = model.item(row, col).text()
                        if col == 0:  # Date column (left-aligned)
                            row_data.append(Paragraph(text, styles["Normal"]))
                        else:  # Numeric columns (right-aligned)
                            row_data.append(text)
                    table_data.append(row_data)

                col_widths = [
                    1.5 * inch,  # Date
                    1.5 * inch,  # Total Orders
                    1.5 * inch,  # Total Expenses
                    1.5 * inch,  # After Expenses
                ]

                table = Table(table_data, colWidths=col_widths)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.5)),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                            ("TOPPADDING", (0, 0), (-1, 0), 8),
                            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 1), (-1, -1), 9),
                            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                            ("TOPPADDING", (0, 1), (-1, -1), 6),
                            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),  # Right-align numeric columns
                            ("ALIGN", (0, 1), (0, -1), "LEFT"),    # Left-align Date
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
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
                    self, "Success", f"Daily financials report downloaded to: {file_path}"
                )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving PDF: {e}")