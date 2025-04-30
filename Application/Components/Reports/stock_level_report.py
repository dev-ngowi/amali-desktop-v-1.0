# stock_level_report.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

REPORTLAB_INSTALLED = True


class StockLevelReport(QWidget):
    def __init__(self, report_manager, stores_data):
        super().__init__()
        self.report_manager = report_manager
        self.stores_data = stores_data
        self.stores = ["All Stores"] + [store["name"] for store in self.stores_data]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Stock Level Report")
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

        # Generate Button
        button_layout = QHBoxLayout()
        self.generate_report_button = QPushButton("Generate Report")
        self.generate_report_button.clicked.connect(self.generate_stock_level)
        button_layout.addStretch(1)
        button_layout.addWidget(self.generate_report_button)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)

        # Report Table
        self.stock_table_view = QTableView()
        self.stock_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.stock_table_view)

        # Download Option
        download_layout = QHBoxLayout()
        download_layout.addStretch(1)
        self.download_button = QPushButton("Download as PDF")
        self.download_button.clicked.connect(self.download_stock_level_pdf)
        download_layout.addWidget(self.download_button)
        layout.addLayout(download_layout)

        self.setLayout(layout)

    def generate_stock_level(self):
        selected_store_name = self.store_combo.currentText()
        selected_store_id = None
        if selected_store_name != "All Stores":
            for store in self.stores_data:
                if store["name"] == selected_store_name:
                    selected_store_id = store["id"]
                    break

        stock_level_data = self.report_manager.get_stock_level_data(
            store_id=selected_store_id
        )

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            [
                "Item Name",
                "Store Name",
                "Stock Quantity",
                "Minimum Quantity",
                "Maximum Quantity",
                "Status",
            ]
        )

        for entry in stock_level_data:
            row = [
                QStandardItem(entry["item_name"]),
                QStandardItem(entry["store_name"]),
                QStandardItem(f"{entry['stock_quantity']:.2f}"),
                QStandardItem(f"{entry['min_quantity']:.2f}"),
                QStandardItem(f"{entry['max_quantity']:.2f}"),
                QStandardItem(entry["status"]),
            ]
            model.appendRow(row)

        self.stock_table_view.setModel(model)
        self.stock_table_view.horizontalHeader().setStretchLastSection(True)
        self.stock_table_view.resizeColumnsToContents()

    def download_stock_level_pdf(self):
        if not REPORTLAB_INSTALLED:
            QMessageBox.critical(
                self,
                "Error",
                "Reportlab is not installed. Please install it using 'pip install reportlab'.",
            )
            return

        model = self.stock_table_view.model()
        if model is None:
            QMessageBox.warning(self, "No Data", "No stock level data to download.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Stock Level Report as PDF", "", "PDF (*.pdf)"
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

                # Custom style for table cells to enable wrapping
                cell_style = styles["Normal"]
                cell_style.alignment = TA_LEFT
                cell_style.fontSize = 9
                cell_style.leading = 10  # Line spacing

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

                story.append(Paragraph("<b>Stock Level Report</b>", title_style))
                store_name = self.store_combo.currentText()
                story.append(Paragraph(f"Store: {store_name}", subtitle_style))
                story.append(Spacer(1, 0.3 * inch))

                # Prepare table data with wrapped text for item names
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
                        # Wrap text for the "Item Name" and "Store Name" columns (col 0 and 1)
                        if col in [0, 1]:
                            para = Paragraph(text, cell_style)
                            row_data.append(para)
                        else:
                            row_data.append(text)
                    table_data.append(row_data)

                # Define column widths
                col_widths = [
                    2.0 * inch,
                    1.5 * inch,
                    1.0 * inch,
                    1.0 * inch,
                    1.0 * inch,
                    0.8 * inch,
                ]

                # Create table
                table = Table(table_data, colWidths=col_widths)
                table.setStyle(
                    TableStyle(
                        [
                            # Header styling
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
                            # Body styling
                            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 1), (-1, -1), 9),
                            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                            ("TOPPADDING", (0, 1), (-1, -1), 6),
                            # Alignments
                            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                            ("ALIGN", (0, 1), (1, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            # Grid styling
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
                    self, "Success", f"Stock level report downloaded to: {file_path}"
                )

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving PDF: {e}")
