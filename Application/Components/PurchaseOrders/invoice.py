import sys
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import logging
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from Application.Components.PurchaseOrders.model import PurchaseOrderManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PurchaseOrderInvoice(QDialog):
    def __init__(self, po_manager, po_id, parent=None):
        super().__init__(parent)
        self.po_manager = po_manager
        self.po_id = po_id
        self.setWindowTitle(f"Purchase Order Invoice - ID: {po_id}")
        self.setMinimumSize(700, 600)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.invoice_text = QTextEdit()
        self.invoice_text.setReadOnly(True)
        self.invoice_text.setStyleSheet(
            "font-family: Arial; font-size: 12pt; border: 1px solid #ccc; padding: 10px;"
        )
        self.layout.addWidget(self.invoice_text)

        self.button_layout = QHBoxLayout()
        self.generate_pdf_btn = QPushButton("Generate PDF")
        self.generate_pdf_btn.clicked.connect(self.generate_pdf)
        self.approve_btn = QPushButton("Approve PO")
        self.approve_btn.clicked.connect(self.approve_po)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.generate_pdf_btn)
        self.button_layout.addWidget(self.approve_btn)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)
        self.generate_invoice()

    def generate_invoice(self):
        try:
            po = self.po_manager.get_purchase_order(self.po_id)
            company = self.po_manager.get_company_info()
            if not po:
                logger.error(f"Purchase order {self.po_id} not found")
                self.invoice_text.setText("Purchase order not found")
                return

            if po["status"] == "Approved" or po["status"] == "Received":
                self.approve_btn.setVisible(False)
            else:
                self.approve_btn.setVisible(True)

            invoice = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; font-size: 12pt; margin: 20px; }}
                    h2 {{ text-align: center; font-size: 16pt; margin-bottom: 10px; }}
                    h3 {{ text-align: center; font-size: 14pt; margin-top: 20px; margin-bottom: 10px; }}
                    p {{ margin: 5px 0; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                    th, td {{ border: 1px solid black; padding: 8px; text-align: left; font-size: 10pt; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    .company-info {{ text-align: center; margin-bottom: 20px; }}
                    .footer {{ margin-top: 20px; text-align: center; font-size: 10pt; color: #555; }}
                </style>
            </head>
            <body>
                <div class="company-info">
                    <h2>{company['company_name']}</h2>
                    <p>{company['address'] or 'N/A'}</p>
                    <p>Phone: {company['phone'] or 'N/A'} | Email: {company['email']}</p>
                    <p>TIN: {company['tin_no'] or 'N/A'} | VRN: {company['vrn_no'] or 'N/A'}</p>
                </div>
                <hr style="border: 1px solid #000; margin: 20px 0;">
                <h3>Purchase Order Invoice</h3>
                <table width="100%">
                    <tr><td><b>Order Number:</b></td><td>{po['order_number']}</td></tr>
                    <tr><td><b>Supplier:</b></td><td>{po['supplier_name']}</td></tr>
                    <tr><td><b>Order Date:</b></td><td>{po['order_date']}</td></tr>
                    <tr><td><b>Expected Delivery:</b></td><td>{po['expected_delivery_date'] or 'N/A'}</td></tr>
                    <tr><td><b>Status:</b></td><td>{po['status']}</td></tr>
                    <tr><td><b>Currency:</b></td><td>{po['currency']}</td></tr>
                    <tr><td><b>Total Amount:</b></td><td>{po['total_amount']:.2f}</td></tr>
                    <tr><td><b>Notes:</b></td><td>{po['notes'] or 'N/A'}</td></tr>
                </table>
                <h4 style="margin-top: 20px;">Items:</h4>
                <table>
                    <tr>
                        <th>Item</th>
                        <th>Unit</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Discount</th>
                        <th>Total</th>
                    </tr>
            """
            for item in po["items"]:
                invoice += f"""
                    <tr>
                        <td>{item['item_name']}</td>
                        <td>{item['unit_name']}</td>
                        <td>{item['quantity']}</td>
                        <td>{item['unit_price']:.2f}</td>
                        <td>{item['discount']:.2f}</td>
                        <td>{item['total_price']:.2f}</td>
                    </tr>
                """
            invoice += """
                </table>
                <div class="footer">
                    <p>Generated by AMALI-POS System</p>
                    <p>Thank you for your business!</p>
                </div>
            </body>
            </html>
            """
            self.invoice_text.setHtml(invoice)
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            self.invoice_text.setText(f"Error generating invoice: {str(e)}")

    def generate_pdf(self):
        try:
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save PDF", f"PO_{self.po_id}.pdf", "PDF Files (*.pdf)"
            )
            if file_name:
                po = self.po_manager.get_purchase_order(self.po_id)
                company = self.po_manager.get_company_info()

                doc = SimpleDocTemplate(file_name, pagesize=A4)
                styles = getSampleStyleSheet()
                elements = []

                elements.append(Paragraph(company["company_name"], styles["Title"]))
                elements.append(
                    Paragraph(company["address"] or "N/A", styles["Normal"])
                )
                elements.append(
                    Paragraph(
                        f"Phone: {company['phone'] or 'N/A'} | Email: {company['email']}",
                        styles["Normal"],
                    )
                )
                elements.append(
                    Paragraph(
                        f"TIN: {company['tin_no'] or 'N/A'} | VRN: {company['vrn_no'] or 'N/A'}",
                        styles["Normal"],
                    )
                )
                elements.append(Spacer(1, 12))

                elements.append(Paragraph("Purchase Order Invoice", styles["Heading2"]))
                elements.append(Spacer(1, 12))

                po_data = [
                    ["Order Number:", po["order_number"]],
                    ["Supplier:", po["supplier_name"]],
                    ["Order Date:", po["order_date"]],
                    ["Expected Delivery:", po["expected_delivery_date"] or "N/A"],
                    ["Status:", po["status"]],
                    ["Currency:", po["currency"]],
                    ["Total Amount:", f"{po['total_amount']:.2f}"],
                    ["Notes:", po["notes"] or "N/A"],
                ]
                po_table = Table(po_data, colWidths=[150, 350])
                po_table.setStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ]
                )
                elements.append(po_table)
                elements.append(Spacer(1, 12))

                elements.append(Paragraph("Items:", styles["Heading3"]))
                items_data = [
                    ["Item", "Unit", "Quantity", "Unit Price", "Discount", "Total"]
                ]
                for item in po["items"]:
                    items_data.append(
                        [
                            item["item_name"],
                            item["unit_name"],
                            str(item["quantity"]),
                            f"{item['unit_price']:.2f}",
                            f"{item['discount']:.2f}",
                            f"{item['total_price']:.2f}",
                        ]
                    )
                items_table = Table(items_data, colWidths=[100, 80, 60, 80, 60, 80])
                items_table.setStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ]
                )
                elements.append(items_table)
                elements.append(Spacer(1, 12))

                elements.append(
                    Paragraph("Generated by AMALI-POS System", styles["Normal"])
                )
                elements.append(
                    Paragraph("Thank you for your business!", styles["Normal"])
                )

                doc.build(elements)
                QMessageBox.information(self, "Success", "PDF generated successfully")
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")

    def approve_po(self):
        try:
            success = self.po_manager.update_purchase_order(
                self.po_id, status="Approved"
            )
            if success:
                QMessageBox.information(self, "Success", "Purchase order approved")
                self.close()  # Close the dialog and return to main view
            else:
                QMessageBox.warning(self, "Warning", "Failed to approve purchase order")
        except Exception as e:
            logger.error(f"Error approving PO: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to approve PO: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    po_manager = PurchaseOrderManager()
    window = PurchaseOrderInvoice(po_manager, 1)
    window.show()
    sys.exit(app.exec_())
