# dead_stock_report.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

REPORTLAB_INSTALLED = True


class DeadStockReport(QWidget):
    def __init__(self, report_manager, stores_data):
        super().__init__()
        self.report_manager = report_manager
        self.stores_data = stores_data
        self.stores = ["All Stores"] + [store["name"] for store in self.stores_data]
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)  # Add spacing between sections

        # Header Section (Title)
        header_layout = QHBoxLayout()
        title_label = QLabel("Dead Stock Report")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)  # Space after title

        # Filter Section
        filter_group = QGroupBox("Filters")
        filter_layout = QGridLayout()
        filter_layout.setHorizontalSpacing(10)
        filter_layout.setVerticalSpacing(10)

        # Store Filter
        self.store_label = QLabel("Filter by Store:")
        self.store_combo = QComboBox()
        self.store_combo.addItems(self.stores)
        self.store_combo.setMinimumWidth(200)
        filter_layout.addWidget(self.store_label, 0, 0)
        filter_layout.addWidget(self.store_combo, 0, 1)

        # Days Threshold
        self.days_label = QLabel("Days Threshold:")
        self.days_input = QSpinBox()
        self.days_input.setRange(30, 365)
        self.days_input.setValue(90)  # Default to 90 days
        self.days_input.setMinimumWidth(100)
        filter_layout.addWidget(self.days_label, 1, 0)
        filter_layout.addWidget(self.days_input, 1, 1)

        filter_layout.setColumnStretch(2, 1)  # Stretch remaining space
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)

        # Button Section
        button_layout = QHBoxLayout()
        self.generate_report_button = QPushButton("Generate Report")
        self.generate_report_button.clicked.connect(self.generate_dead_stock)
        self.generate_report_button.setMinimumWidth(150)
        button_layout.addStretch(1)
        button_layout.addWidget(self.generate_report_button)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)
        main_layout.addSpacing(10)

        # Table Section
        self.dead_stock_table_view = QTableView()
        self.dead_stock_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dead_stock_table_view.setMinimumHeight(
            300
        )  # Ensure table has enough height
        main_layout.addWidget(
            self.dead_stock_table_view, stretch=1
        )  # Stretch to fill space

        # Download Section
        download_layout = QHBoxLayout()
        self.download_button = QPushButton("Download as PDF")
        self.download_button.clicked.connect(self.download_dead_stock_pdf)
        self.download_button.setMinimumWidth(150)
        download_layout.addStretch(1)
        download_layout.addWidget(self.download_button)
        download_layout.addStretch(1)
        main_layout.addLayout(download_layout)

        # Set the main layout
        self.setLayout(main_layout)

    def generate_dead_stock(self):
        selected_store_name = self.store_combo.currentText()
        selected_store_id = None
        if selected_store_name != "All Stores":
            for store in self.stores_data:
                if store["name"] == selected_store_name:
                    selected_store_id = store["id"]
                    break

        days_threshold = self.days_input.value()
        dead_stock_data = self.report_manager.get_dead_stock_data(
            days_threshold=days_threshold, store_id=selected_store_id
        )

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            [
                "Item Name",
                "Store Name",
                "Stock Quantity",
                "Minimum Quantity",
                "Maximum Quantity",
                "Last Sale Date",
            ]
        )

        for entry in dead_stock_data:
            row = [
                QStandardItem(entry["item_name"]),
                QStandardItem(entry["store_name"]),
                QStandardItem(f"{entry['stock_quantity']:.2f}"),
                QStandardItem(f"{entry['min_quantity']:.2f}"),
                QStandardItem(f"{entry['max_quantity']:.2f}"),
                QStandardItem(str(entry["last_sale_date"])),
            ]
            model.appendRow(row)

        self.dead_stock_table_view.setModel(model)
        self.dead_stock_table_view.horizontalHeader().setStretchLastSection(True)
        self.dead_stock_table_view.resizeColumnsToContents()

    def download_dead_stock_pdf(self):
        if not REPORTLAB_INSTALLED:
            QMessageBox.critical(
                self,
                "Error",
                "Reportlab is not installed. Please install it using 'pip install reportlab'.",
            )
            return

        model = self.dead_stock_table_view.model()
        if model is None:
            QMessageBox.warning(self, "No Data", "No dead stock data to download.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Dead Stock Report as PDF", "", "PDF (*.pdf)"
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
                cell_style.alignment = TA_LEFT
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

                story.append(Paragraph("<b>Dead Stock Report</b>", title_style))
                store_name = self.store_combo.currentText()
                days_threshold = self.days_input.value()
                story.append(Paragraph(f"Store: {store_name}", subtitle_style))
                story.append(
                    Paragraph(f"Threshold: {days_threshold} days", subtitle_style)
                )
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
                        if col in [0, 1]:  # Item Name and Store Name
                            para = Paragraph(text, cell_style)
                            row_data.append(para)
                        else:
                            row_data.append(text)
                    table_data.append(row_data)

                col_widths = [
                    2.0 * inch,
                    1.5 * inch,
                    1.0 * inch,
                    1.0 * inch,
                    1.0 * inch,
                    1.0 * inch,
                ]

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
                            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 1), (-1, -1), 9),
                            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                            ("TOPPADDING", (0, 1), (-1, -1), 6),
                            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                            ("ALIGN", (0, 1), (1, -1), "LEFT"),
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
                    self, "Success", f"Dead stock report downloaded to: {file_path}"
                )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving PDF: {e}")
