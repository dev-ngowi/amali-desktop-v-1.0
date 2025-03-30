import random
import sqlite3
import os
import logging
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
import usb
from Helper.api import get_payments_from_api
from Helper.db_conn import db
import json
from datetime import datetime
from escpos.printer import Usb

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


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


class HoverFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.apply_default_shadow()
        self.original_y = None

    def apply_default_shadow(self):
        default_shadow = QGraphicsDropShadowEffect()
        default_shadow.setBlurRadius(6)
        default_shadow.setXOffset(0)
        default_shadow.setYOffset(4)
        default_shadow.setColor(Qt.black)
        self.setGraphicsEffect(default_shadow)

    def apply_hover_shadow(self):
        hover_shadow = QGraphicsDropShadowEffect()
        hover_shadow.setBlurRadius(8)
        hover_shadow.setXOffset(0)
        hover_shadow.setYOffset(6)
        hover_shadow.setColor(Qt.black)
        self.setGraphicsEffect(hover_shadow)

    def enterEvent(self, event):
        if self.original_y is None:
            self.original_y = self.pos().y()
        self.apply_hover_shadow()
        self.move(self.pos().x(), self.original_y - 5)

    def leaveEvent(self, event):
        self.apply_default_shadow()
        if self.original_y is not None:
            self.move(self.pos().x(), self.original_y)


# class ProductCard(HoverFrame):
#     clicked = pyqtSignal(dict)

#     def __init__(self, item):
#         super().__init__()
#         self.item = item
#         self.item["stock_quantity"] = float(self.item["stock_quantity"])
#         self.setFixedWidth(115)
#         self.setFixedHeight(170)
#         self.setStyleSheet(
#             """
#             ProductCard {
#                 background-color: #ffffff;
#                 border-radius: 12px;
#                 border: 1px solid #e0e0e0;
#                 padding: 0px;
#             }
#             ProductCard:hover {
#                 border: 1px solid #3498db;
#             }
#             """
#         )
#         self.setCursor(Qt.PointingHandCursor)

#         layout = QVBoxLayout(self)
#         layout.setSpacing(0)
#         layout.setContentsMargins(0, 0, 0, 0)

#         self.image_label = QLabel()
#         pixmap = QPixmap()
#         if "image_url" in item and item["image_url"]:
#             pixmap.load(get_resource_path(item["image_url"]))  # Updated path
#         if pixmap.isNull():
#             pixmap = QPixmap(
#                 get_resource_path("Resources/Images/shopping-bag.jpg")
#             ).scaled(  # Updated path
#                 100, 70, Qt.KeepAspectRatio
#             )
#             self.image_label.setPixmap(pixmap)
#         else:
#             self.image_label.setText("No Image")
#             self.image_label.setAlignment(Qt.AlignCenter)
#             self.image_label.setStyleSheet(
#                 """
#                 color: #999999;
#                 background-color: #f5f5f5;
#                 font-size: 12px;
#                 """
#             )
#         self.image_label.setFixedHeight(70)
#         self.image_label.setAlignment(Qt.AlignCenter)
#         self.image_label.setStyleSheet(
#             """
#             border-radius: 12px 12px 0 0;
#             background-color: #f5f5f5;
#             """
#         )
#         layout.addWidget(self.image_label)

#         details = QWidget()
#         details.setStyleSheet(
#             """
#             QWidget {
#                 background-color: #ffffff;
#                 border-radius: 12px;
#                 padding: 6px;
#             }
#             """
#         )
#         details_layout = QVBoxLayout(details)
#         details_layout.setSpacing(4)
#         details_layout.setContentsMargins(6, 6, 6, 6)

#         self.name_label = QLabel(item["item_name"].upper())
#         initial_font_size = 9
#         font = QFont("Arial", initial_font_size, QFont.Bold)
#         self.name_label.setFont(font)
#         self.name_label.setStyleSheet(
#             """
#             color: #2c3e50;
#             background: transparent;
#             border: none;
#             """
#         )
#         self.name_label.setWordWrap(True)
#         self.name_label.setFixedHeight(40)
#         details_layout.addWidget(self.name_label, alignment=Qt.AlignCenter)

#         self.price_label = QLabel(
#             f"<b>Price:</b> {item['item_price']}<br>Qty: {item['stock_quantity']:.2f} {item['item_unit']}"
#         )
#         self.price_label.setFont(QFont("Arial", 10))
#         self.price_label.setStyleSheet(
#             """
#             color: #7f8c8d;
#             background: transparent;
#             border: none;
#             """
#         )
#         details_layout.addWidget(self.price_label, alignment=Qt.AlignCenter)

#         font_metrics = QFontMetrics(self.name_label.font())
#         elided_text = font_metrics.elidedText(
#             self.name_label.text(), Qt.ElideRight, self.width() - 12
#         )
#         if elided_text != self.name_label.text():
#             current_font_size = initial_font_size
#             while current_font_size > 6:
#                 current_font_size -= 0.5
#                 font.setPointSize(int(current_font_size))
#                 self.name_label.setFont(font)
#                 font_metrics = QFontMetrics(self.name_label.font())
#                 elided_text = font_metrics.elidedText(
#                     self.name_label.text(), Qt.ElideRight, self.width() - 12
#                 )
#                 if elided_text == self.name_label.text():
#                     break
#         self.name_label.setText(elided_text)

#         layout.addWidget(details)

#     def mousePressEvent(self, event):
#         if event.button() == Qt.LeftButton:
#             self.clicked.emit(self.item)
#         super().mousePressEvent(event)

#     def update_stock_display(self, new_quantity):
#         self.item["stock_quantity"] = new_quantity
#         self.price_label.setText(
#             f"<b>Price:</b> {self.item['item_price']}<br>Qty: {self.item['stock_quantity']:.2f} {self.item['item_unit']}"
#         )


class ProductCard(HoverFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, item):
        super().__init__()
        self.item = item
        self.item["stock_quantity"] = float(self.item["stock_quantity"])
        self.setMinimumWidth(115)
        self.setMinimumHeight(170)
        # Remove fixed width/height to allow dynamic sizing
        # self.setMinimumWidth(120)  # Slightly wider minimum for better fit
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet(
            """
            ProductCard {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                padding: 0px;
            }
            ProductCard:hover {
                border: 1px solid #3498db;
            }
            """
        )
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Image Label
        self.image_label = QLabel()
        pixmap = QPixmap()
        if "image_url" in item and item["image_url"]:
            pixmap.load(get_resource_path(item["image_url"]))
        if pixmap.isNull():
            pixmap = QPixmap(
                get_resource_path("Resources/Images/shopping-bag.jpg")
            ).scaled(100, 70, Qt.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("No Image")
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setStyleSheet(
                """
                color: #999999;
                background-color: #f5f5f5;
                font-size: 12px;
                """
            )
        self.image_label.setFixedHeight(70)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            """
            border-radius: 12px 12px 0 0;
            background-color: #f5f5f5;
            """
        )
        layout.addWidget(self.image_label)

        # Details Widget
        details = QWidget()
        details.setStyleSheet(
            """
            QWidget {
                background-color: #ffffff;
                border-radius: 12px;
                padding: 6px;
            }
            """
        )
        details_layout = QVBoxLayout(details)
        details_layout.setSpacing(4)
        details_layout.setContentsMargins(6, 6, 6, 6)

        # Product Name Label
        self.name_label = QLabel(item["item_name"].upper())
        font = QFont("Arial", 10, QFont.Bold)  # Fixed larger font size
        self.name_label.setFont(font)
        self.name_label.setStyleSheet(
            """
            color: #2c3e50;
            background: transparent;
            border: none;
            """
        )
        self.name_label.setWordWrap(True)  # Allow text to wrap
        # Remove fixed height to let it grow with content
        details_layout.addWidget(self.name_label, alignment=Qt.AlignCenter)

        # Price and Quantity Label
        self.price_label = QLabel(
            f"<b>Price:</b> {item['item_price']}<br>Qty: {item['stock_quantity']:.2f} {item['item_unit']}"
        )
        self.price_label.setFont(QFont("Arial", 10))
        self.price_label.setStyleSheet(
            """
            color: #7f8c8d;
            background: transparent;
            border: none;
            """
        )
        details_layout.addWidget(self.price_label, alignment=Qt.AlignCenter)

        layout.addWidget(details)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.item)
        super().mousePressEvent(event)

    def update_stock_display(self, new_quantity):
        self.item["stock_quantity"] = new_quantity
        self.price_label.setText(
            f"<b>Price:</b> {self.item['item_price']}<br>Qty: {self.item['stock_quantity']:.2f} {self.item['item_unit']}"
        )


# Sidebar class remains unchanged
class Sidebar(QWidget):
    group_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8f9fa;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search Groups")
        self.search.setStyleSheet(
            """
            background-color: white;
            border-radius: none;
            padding: 5px 10px;
            border: 1px solid #ced4da;
            font-size: 12px;
            """
        )
        self.layout.addWidget(self.search)
        self.search.textChanged.connect(self.filter_groups)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            "background: #f8f9fa; border: none; padding: 15px;"
        )

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)

        self.item_groups_data = db.get_local_item_groups()
        self.update_group_buttons(self.item_groups_data)

        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

    def update_group_buttons(self, groups):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        if groups:
            for group in groups:
                btn = QPushButton(group)
                btn.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #ffffff;
                        color: #333333;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        padding: 5px;
                        text-align: left;
                        font-size: 14px;
                        min-height: 30px;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                        border: 1px solid #3498db;
                    }
                    QPushButton:pressed {
                        background-color: #e0e0e0;
                    }
                    """
                )
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(
                    lambda checked, g=group: self.group_selected.emit(g)
                )
                self.scroll_layout.addWidget(btn)
        else:
            no_data_label = QLabel("No groups available")
            no_data_label.setStyleSheet("color: #333333; padding: 10px;")
            self.scroll_layout.addWidget(no_data_label)

    def filter_groups(self, text):
        filtered_groups = []
        if text:
            filtered_groups = [
                group
                for group in self.item_groups_data
                if text.lower() in group.lower()
            ]
        else:
            filtered_groups = self.item_groups_data
        self.update_group_buttons(filtered_groups)


class PaymentConfirmationDialog(QDialog):
    def __init__(self, parent, order_data, items, payment_id, customer_id):
        super().__init__(parent)
        self.setWindowTitle("Confirm Payment")
        self.setModal(True)
        self.setFixedSize(600, 500)
        self.order_data = order_data
        self.items = items
        self.payment_id = payment_id
        self.customer_id = customer_id
        self.parent_widget = parent

        # Initialize attributes from order_data
        self.total_amount = order_data.get("total_amount", 0.0)
        self.tip = order_data.get("tip", 0.0)
        self.discount = order_data.get("discount", 0.0)

        layout = QVBoxLayout(self)

        summary_label = QLabel("Payment Summary")
        summary_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")
        summary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(summary_label)

        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.addWidget(QLabel(f"Order No: {order_data['order_number']}"))
        details_layout.addWidget(QLabel(f"Date: {order_data['date']}"))
        details_layout.addWidget(
            QLabel(f"Total Amount: {order_data['total_amount']:.2f}")
        )
        details_layout.addWidget(QLabel(f"Tip: {order_data['tip']:.2f}"))
        details_layout.addWidget(QLabel(f"Discount: {order_data['discount']:.2f}"))
        details_layout.addWidget(
            QLabel(f"Ground Total: {order_data['ground_total']:.2f}")
        )
        layout.addWidget(details_widget)

        items_label = QLabel("Items:")
        items_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(items_label)
        items_list = QListWidget()
        for item in items:
            items_list.addItem(
                f"{item['item_id']} - Qty: {item['quantity']} - Price: {item['price']:.2f}"
            )
        layout.addWidget(items_list)

        button_layout = QHBoxLayout()
        preview_btn = QPushButton("Preview Receipt")
        preview_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #138496; }
            """
        )
        preview_btn.clicked.connect(self.preview_receipt)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #218838; }
            """
        )
        confirm_btn.clicked.connect(self.confirm_payment)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #c82333; }
            """
        )
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(preview_btn)
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def preview_receipt(self):
        """Show a preview of the receipt in a new window"""
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Receipt Preview")
        preview_dialog.setFixedSize(400, 600)

        layout = QVBoxLayout(preview_dialog)

        company_details = db.get_company_details()
        company = (
            company_details[0]
            if company_details
            else {
                "company_name": "Unknown Company",
                "address": "N/A",
                "state": "N/A",
                "phone": "N/A",
                "tin_no": "N/A",
                "vrn_no": "N/A",
            }
        )

        receipt_text = self.generate_receipt_text(company)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(receipt_text)
        text_edit.setFont(QFont("Courier", 10))
        layout.addWidget(text_edit)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(preview_dialog.accept)
        layout.addWidget(close_btn)

        preview_dialog.exec_()

    def generate_receipt_text(self, company):
        """Generate receipt text for preview with dynamic company details"""
        receipt = []
        company_name = company["company_name"].replace("22", "").strip()
        receipt.append(f"{company_name}".center(32))
        receipt.append(f"{company['address']}".center(32))
        if company["state"]:
            receipt.append(f"{company['state']}".center(32))
        receipt.append(f"Tel: {company['phone']}".center(32))
        receipt.append(f"TIN: {company['tin_no']}  VRN: {company['vrn_no']}".center(32))
        receipt.append("")

        receipt.append("RECEIPT".center(32))
        receipt.append("")

        receipt.append(f"Order: {self.order_data['order_number']}")
        receipt.append(f"Date: {self.order_data['date']}")
        receipt.append(f"Payment: {self.parent_widget.payment_method.currentText()}")
        receipt.append("")

        receipt.append("-" * 32)
        receipt.append("Item               Qty   Price  Total")
        receipt.append("-" * 32)

        table = self.parent_widget.dashboard_view.table
        for row in range(table.rowCount()):
            item = table.item(row, 0).text()[:18].ljust(18)
            qty = table.item(row, 2).text().rjust(3)
            price = f"{float(table.item(row, 3).text()):.2f}".rjust(6)
            total = f"{float(qty) * float(price):.2f}".rjust(6)
            receipt.append(f"{item} {qty} {price} {total}")

        receipt.append("")
        receipt.append("-" * 32)
        receipt.append(f"Subtotal: {self.order_data['total_amount']:.2f}".rjust(32))
        receipt.append(f"Tip:      {self.order_data['tip']:.2f}".rjust(32))
        receipt.append(f"Discount: {self.order_data['discount']:.2f}".rjust(32))
        receipt.append("-" * 32)
        receipt.append(f"TOTAL:    {self.order_data['ground_total']:.2f}".rjust(32))
        receipt.append("")

        receipt.append("Thank you for your purchase!".center(32))
        receipt.append("Visit us again!".center(32))

        return "\n".join(receipt)

    def confirm_payment(self):
        print("Starting confirm_payment...")
        try:
            success = db.save_order(
                self.order_data, self.items, self.payment_id, self.customer_id
            )
            if success:
                print("Save order succeeded, updating stock and UI...")
                item_quantities = {}
                for item in self.items:
                    item_id = item["item_id"]
                    quantity_purchased = item["quantity"]
                    if item_id in item_quantities:
                        item_quantities[item_id] += quantity_purchased
                    else:
                        item_quantities[item_id] = quantity_purchased

                processed_items = set()
                for item_id, total_quantity in item_quantities.items():
                    for (
                        card_name,
                        card,
                    ) in self.parent_widget.dashboard_view.product_cards.items():
                        if (
                            card.item["item_id"] == item_id
                            and item_id not in processed_items
                        ):
                            current_quantity = float(card.item["stock_quantity"])
                            new_quantity = current_quantity - total_quantity
                            if new_quantity < 0:
                                print(
                                    f"Warning: Stock for item {item_id} would go negative ({new_quantity})"
                                )
                                new_quantity = 0
                            card.update_stock_display(new_quantity)
                            db.update_item_stock(item_id, new_quantity)
                            print(f"Updated stock for item {item_id}: {new_quantity}")
                            processed_items.add(item_id)
                            break

                self.parent_widget.order_no_label.setText(
                    f"Order No: {self.order_data['order_number']}"
                )
                self.parent_widget.print_receipt()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Payment of {self.order_data['ground_total']:.2f} completed!\nOrder: {self.order_data['order_number']}\nReceipt: {self.order_data['receipt_number']}",
                )
                self.parent_widget.dashboard_view.clear_checkout()
                self.parent_widget.hide_payment()
                print("Closing dialog after success...")
                self.accept()
            else:
                print("Save order failed, keeping dialog open...")
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Failed to save order to database. Please try again.",
                )
        except sqlite3.OperationalError as se:
            print(f"Database error: {se}")
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to save order due to database lock: {str(se)}. Please wait a moment and try again.",
            )
        except Exception as e:
            print(f"Unexpected error: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred: {str(e)}. Please try again or contact support.",
            )


class PaymentCard(QWidget):
    def __init__(self, total_amount, dashboard_view):
        super().__init__()
        self.total_amount = total_amount
        self.dashboard_view = dashboard_view
        self.tip = 0.0
        self.discount = 0.0
        self.setStyleSheet(
            "background-color: #e9ecef; border-radius: 8px; padding: 10px;"
        )
        self.setFixedWidth(300)
        self.setVisible(False)

        layout = QVBoxLayout(self)

        # Header with payment method selection
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)

        payment_method_label = QLabel("Payment Method *")
        payment_method_label.setStyleSheet(
            "font-weight: bold; color: #333; margin-bottom: 5px;"
        )
        self.payment_method = QComboBox()

        # Fetch and populate payment methods
        self.payment_method_data = db.get_payments()  # Local DB payments
        if not self.payment_method_data:  # Fallback to API if DB is empty
            logger.warning("No payment methods found in local DB, fetching from API")
            self.payment_method_data = get_payments_from_api()

        if not self.payment_method_data:
            logger.error("No payment methods available from DB or API")
            self.payment_method.addItem("No Payment Methods Available")
            self.payment_method.setEnabled(False)
        else:
            for payment in self.payment_method_data:
                self.payment_method.addItem(payment["short_code"], payment)
            cash_index = self.payment_method.findText("Cash", Qt.MatchFixedString)
            if cash_index != -1:
                self.payment_method.setCurrentIndex(cash_index)

        self.payment_method.setStyleSheet(
            """
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                width: 100%;
            }
        """
        )
        header_layout.addWidget(payment_method_label)
        header_layout.addWidget(self.payment_method)

        # Order info
        order_info_layout = QHBoxLayout()
        order_number = f"ORD-{random.randint(1000, 9999)}"
        self.order_no_label = QLabel(f"Order No: {order_number}")
        self.date_label = QLabel(f"Date: {datetime.now().strftime('%d/%m/%Y')}")
        self.order_no_label.setStyleSheet("color: #333;")
        self.date_label.setStyleSheet("color: #333;")
        order_info_layout.addWidget(self.order_no_label)
        order_info_layout.addStretch()
        order_info_layout.addWidget(self.date_label)
        header_layout.addLayout(order_info_layout)

        layout.addWidget(header_widget)

        # Totals section
        totals_widget = QWidget()
        totals_layout = QVBoxLayout(totals_widget)

        self.total_amount_label = QLabel(f"TOTAL AMOUNT: {self.total_amount:.2f}")
        self.total_amount_label.setStyleSheet("font-weight: bold; color: #333;")
        totals_layout.addWidget(self.total_amount_label)

        tip_layout = QHBoxLayout()
        tip_label = QLabel("Add Tip:")
        self.tip_input = QLineEdit("0")
        self.tip_input.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
        """
        )
        self.tip_input.setFixedWidth(50)
        tip_minus = QPushButton("-")
        tip_minus.setStyleSheet("background-color: #ddd; border: none; padding: 5px;")
        tip_minus.clicked.connect(lambda: self.adjust_tip(-1))
        tip_plus = QPushButton("+")
        tip_plus.setStyleSheet("background-color: #ddd; border: none; padding: 5px;")
        tip_plus.clicked.connect(lambda: self.adjust_tip(1))
        tip_layout.addWidget(tip_label)
        tip_layout.addWidget(self.tip_input)
        tip_layout.addWidget(tip_minus)
        tip_layout.addWidget(tip_plus)
        totals_layout.addLayout(tip_layout)

        discount_layout = QHBoxLayout()
        discount_label = QLabel("Add Discount:")
        self.discount_input = QLineEdit("0")
        self.discount_input.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
        """
        )
        self.discount_input.setFixedWidth(50)
        discount_minus = QPushButton("-")
        discount_minus.setStyleSheet(
            "background-color: #ddd; border: none; padding: 5px;"
        )
        discount_minus.clicked.connect(lambda: self.adjust_discount(-1))
        discount_plus = QPushButton("+")
        discount_plus.setStyleSheet(
            "background-color: #ddd; border: none; padding: 5px;"
        )
        discount_plus.clicked.connect(lambda: self.adjust_discount(1))
        discount_layout.addWidget(discount_label)
        discount_layout.addWidget(self.discount_input)
        discount_layout.addWidget(discount_minus)
        discount_layout.addWidget(discount_plus)
        totals_layout.addLayout(discount_layout)

        self.ground_total_label = QLabel(
            f"GROUND TOTAL AMOUNT: {self.total_amount:.2f}"
        )
        self.ground_total_label.setStyleSheet("font-weight: bold; color: #333;")
        totals_layout.addWidget(self.ground_total_label)

        layout.addWidget(totals_widget)

        # Numpad
        numpad_widget = QWidget()
        numpad_layout = QGridLayout(numpad_widget)
        buttons = [
            ("1", 0, 0),
            ("2", 0, 1),
            ("3", 0, 2),
            ("More", 0, 3),
            ("4", 1, 0),
            ("5", 1, 1),
            ("6", 1, 2),
            ("C", 1, 3),
            ("7", 2, 0),
            ("8", 2, 1),
            ("9", 2, 2),
            ("Pay", 2, 3),
            ("0", 3, 0),
            ("00", 3, 1),
            (".", 3, 2),
            ("X", 3, 3),
        ]
        for text, row, col in buttons:
            button = QPushButton(text)
            button_style = """
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 10px;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #e9ecef; }
            """
            if text == "C":
                button_style = """
                    QPushButton {
                        background-color: #ff0000;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 10px;
                        font-size: 14px;
                    }
                    QPushButton:hover { background-color: #cc0000; }
                """
            elif text in ["Pay", "X"]:
                button_style = """
                    QPushButton {
                        background-color: #007bff;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 10px;
                        font-size: 14px;
                    }
                    QPushButton:hover { background-color: #0056b3; }
                """
            elif text == "More":
                button_style = """
                    QPushButton {
                        background-color: #ff8c00;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 10px;
                        font-size: 14px;
                    }
                    QPushButton:hover { background-color: #cc7000; }
                """
            button.setStyleSheet(button_style)
            if text == "C":
                button.clicked.connect(self.clear_payment)
            elif text == "Pay":
                button.clicked.connect(self.confirm_payment)
            elif text == "X":
                button.clicked.connect(self.hide_payment)
            elif text == "More":
                button.clicked.connect(self.show_more_options)
            else:
                button.clicked.connect(lambda checked, t=text: self.num_pad_input(t))
            numpad_layout.addWidget(button, row, col)
        layout.addWidget(numpad_widget)

        # Bottom buttons
        bottom_buttons_layout = QHBoxLayout()
        split_bill_btn = QPushButton("Split Bill")
        split_bill_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #87ceeb;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #6ab8e3; }
        """
        )
        split_bill_btn.clicked.connect(self.split_bill)
        checkout_btn = QPushButton("Check Out")
        checkout_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ff8c00;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #cc7000; }
        """
        )
        checkout_btn.clicked.connect(self.confirm_payment)
        hide_btn = QPushButton("Hide")
        hide_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """
        )
        hide_btn.clicked.connect(self.hide_payment)
        bottom_buttons_layout.addWidget(split_bill_btn)
        bottom_buttons_layout.addWidget(checkout_btn)
        bottom_buttons_layout.addWidget(hide_btn)
        layout.addLayout(
            bottom_buttons_layout
        )  # Fixed variable name from your original code

        # Connect signals
        self.payment_method.currentTextChanged.connect(self.update_payment_method)
        self.update_ground_total()

    def num_pad_input(self, value):
        if not hasattr(self, "current_input"):
            self.current_input = ""
        self.current_input += value
        self.update_payment_input()

    def clear_payment(self):
        self.current_input = ""
        self.update_payment_input()

    def update_payment_input(self):
        pass  # Placeholder for future numpad functionality if needed

    def adjust_tip(self, delta):
        self.tip = max(0, self.tip + delta)
        self.tip_input.setText(str(self.tip))
        self.update_ground_total()

    def adjust_discount(self, delta):
        self.discount = max(0, self.discount + delta)
        self.discount_input.setText(str(self.discount))
        self.update_ground_total()

    def update_ground_total(self):
        ground_total = self.total_amount + self.tip - self.discount
        self.ground_total_label.setText(f"GROUND TOTAL AMOUNT: {ground_total:.2f}")

    def update_payment_method(self, method):
        logger.debug(f"Payment method changed to: {method}")

    def show_more_options(self):
        QMessageBox.information(
            self, "More Options", "More options functionality to be implemented."
        )

    def split_bill(self):
        QMessageBox.information(
            self, "Split Bill", "Split bill functionality to be implemented."
        )

    def print_receipt(self):
        """Print receipt to an 80mm USB printer using python-escpos and open cash drawer."""
        logger.debug("Starting print_receipt using python-escpos")
        company_details = db.get_company_details()
        logger.debug(f"Raw company details from DB: {company_details}")
        company = (
            company_details[0]
            if company_details
            else {
                "company_name": "Unknown Company",
                "address": "N/A",
                "state": "N/A",
                "phone": "N/A",
                "tin_no": "N/A",
                "vrn_no": "N/A",
            }
        )

        company["company_name"] = company["company_name"].replace("22", "").strip()
        logger.debug(f"Company name after cleanup: '{company['company_name']}'")

        try:
            VENDOR_ID = 0x1D90
            PRODUCT_ID = 0x2060
            printer = Usb(VENDOR_ID, PRODUCT_ID, in_ep=0x81, out_ep=0x2)
            logger.info(
                f"Connected to USB printer with VID: {VENDOR_ID:04x}, PID: {PRODUCT_ID:04x}"
            )

            printer.cashdraw([0, 25, 25])
            logger.debug("Sent cash drawer open command (pin 2)")

            printer.set(align="center")
            printer.text(f"{company['company_name']}\n")
            printer.text(f"{company['address']}\n")
            if company["state"]:
                printer.text(f"{company['state']}\n")
            printer.text(f"Tel: {company['phone']}\n")
            printer.text(f"TIN: {company['tin_no']} VRN: {company['vrn_no']}\n")
            printer.text("\n")
            printer.text("RECEIPT\n")
            printer.text("\n")
            printer.set(align="left")
            printer.text(
                f"Order: {self.order_no_label.text().replace('Order No: ', '')}\n"
            )
            printer.text(f"Date: {self.date_label.text().replace('Date: ', '')}\n")
            printer.text(f"Payment: {self.payment_method.currentText()}\n")
            printer.text("-" * 42 + "\n")
            printer.text("Item                Qty  Price Total\n")
            printer.text("-" * 42 + "\n")

            table = self.dashboard_view.table
            for row in range(table.rowCount()):
                item = table.item(row, 0).text()[:18].ljust(18)
                qty = table.item(row, 2).text().rjust(3)
                price = f"{float(table.item(row, 3).text()):.2f}".rjust(6)
                total = f"{float(qty) * float(price):.2f}".rjust(6)
                printer.text(f"{item} {qty} {price} {total}\n")

            printer.text("-" * 42 + "\n")
            printer.set(align="right")
            printer.text(f"Subtotal: {self.total_amount:.2f}\n")
            printer.text(f"Tip:      {self.tip:.2f}\n")
            printer.text(f"Discount: {self.discount:.2f}\n")
            printer.text("-" * 32 + "\n")
            printer.text(
                f"TOTAL:    {self.total_amount + self.tip - self.discount:.2f}\n"
            )
            printer.set(align="center")
            printer.text("\nThank you for your purchase!\n")
            printer.text("Visit us again!\n")
            printer.text("\n\n\n")

            printer.cut()
            printer.close()
            logger.info("Receipt printed successfully and cash drawer opened")

        except usb.core.USBError as e:
            logger.error(f"USB error: {str(e)}")
            QMessageBox.critical(
                self,
                "Print Error",
                f"USB error: {str(e)}\nCheck printer connection or permissions.",
            )
        except Exception as e:
            logger.error(f"Failed to print receipt or open cash drawer: {str(e)}")
            QMessageBox.critical(
                self,
                "Print Error",
                f"Failed to print or open cash drawer:\n{str(e)}\nCheck printer and cash drawer setup.",
            )

    def render_receipt(self, printer, company):
        """Render the receipt content to the 80mm printer with debugging."""
        logger.debug("Starting render_receipt")
        company["company_name"] = company["company_name"].replace("22", "").strip()
        logger.debug(f"Company name after cleanup: '{company['company_name']}'")

        painter = QPainter()
        if not painter.begin(printer):
            logger.error("Failed to initialize painter for printing")
            raise Exception("Failed to initialize painter for printing")

        try:
            font = QFont("Courier", 8)
            painter.setFont(font)
            metrics = QFontMetrics(font)

            x, y = 5, 5
            line_height = metrics.height()

            receipt_lines = [
                f"{company['company_name'][:32]:^32}",
                f"{company['address'][:32]:^32}",
            ]
            if company["state"]:
                receipt_lines.append(f"{company['state'][:32]:^32}")
            receipt_lines.extend(
                [
                    f"Tel: {company['phone'][:28]:^32}",
                    f"TIN: {company['tin_no']} VRN: {company['vrn_no'][:20]:^32}",
                    "",
                    "RECEIPT".center(32),
                    "",
                    f"Order: {self.order_no_label.text().replace('Order No: ', '')[:26]}",
                    f"Date: {self.date_label.text().replace('Date: ', '')}",
                    f"Payment: {self.payment_method.currentText()[:24]}",
                    "",
                    "-" * 32,
                    "Item          Qty  Price Total",
                    "-" * 32,
                ]
            )

            table = self.dashboard_view.table
            for row in range(table.rowCount()):
                item = table.item(row, 0).text()[:13].ljust(13)
                qty = table.item(row, 2).text().rjust(3)
                price = f"{float(table.item(row, 3).text()):.2f}".rjust(6)
                total = f"{float(qty) * float(price):.2f}".rjust(6)
                receipt_lines.append(f"{item} {qty} {price} {total}")

            receipt_lines.extend(
                [
                    "",
                    "-" * 32,
                    f"Subtotal: {self.total_amount:.2f}".rjust(32),
                    f"Tip:      {self.tip:.2f}".rjust(32),
                    f"Discount: {self.discount:.2f}".rjust(32),
                    "-" * 32,
                    f"TOTAL:    {self.total_amount + self.tip - self.discount:.2f}".rjust(
                        32
                    ),
                    "",
                    "Thank you for your purchase!".center(32),
                    "Visit us again!".center(32),
                    "",
                ]
            )

            for line in receipt_lines:
                painter.drawText(x, y, line)
                y += line_height

            logger.debug(f"Rendered {len(receipt_lines)} lines on receipt")
            painter.end()
            logger.debug("Painter ended successfully")

        except Exception as e:
            painter.end()
            logger.error(f"Rendering error: {str(e)}")
            raise Exception(f"Rendering error: {str(e)}")

    def confirm_payment(self):
        logger.debug("Starting confirm_payment")
        try:
            ground_total = self.total_amount + self.tip - self.discount

            table = self.dashboard_view.table
            items = []
            for row in range(table.rowCount()):
                item_name_widget = table.item(row, 0)
                if not item_name_widget:
                    raise ValueError(f"No item name found at row {row}")
                item_name = item_name_widget.text()
                item_id = item_name_widget.data(Qt.UserRole)
                if not item_id:
                    raise ValueError(f"Item ID not found for {item_name} at row {row}")

                qty = int(table.item(row, 2).text())
                price = float(table.item(row, 3).text())
                items.append({"item_id": item_id, "quantity": qty, "price": price})

            customer_type_name = self.dashboard_view.customer_type.currentText()
            customer_type_id = next(
                (
                    ct["id"]
                    for ct in self.dashboard_view.customer_types_data
                    if ct["name"] == customer_type_name
                ),
                None,
            )
            if not customer_type_id:
                raise ValueError(f"Customer type ID not found for {customer_type_name}")

            customer_id = (
                self.dashboard_view.customer_select.currentData()
                if customer_type_name.lower() == "registered"
                else None
            )

            payment_index = self.payment_method.currentIndex()
            payment_data = self.payment_method.itemData(payment_index)
            if not payment_data:
                raise ValueError(
                    f"No payment data found for selected method: {self.payment_method.currentText()}"
                )

            payment_id = payment_data["id"]
            payment_method = payment_data["short_code"]
            logger.debug(f"Selected payment: {payment_method} (ID: {payment_id})")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            order_number = f"ORD-{random.randint(1000, 9999)}"
            receipt_number = f"REC-{datetime.now().strftime('%H%M%S')}"
            order_data = {
                "order_number": order_number,
                "receipt_number": receipt_number,
                "date": timestamp,
                "customer_type_id": customer_type_id,
                "total_amount": self.total_amount,
                "tip": self.tip,
                "discount": self.discount,
                "ground_total": ground_total,
                "status": "all",
                "is_active": 1,
            }

            dialog = PaymentConfirmationDialog(
                self, order_data, items, payment_id, customer_id
            )
            dialog.exec_()

        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            QMessageBox.critical(self, "Error", str(ve))
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Error", f"An unexpected error occurred: {str(e)}"
            )

    def hide_payment(self):
        self.setVisible(False)
        self.dashboard_view.checkout_widget.setVisible(True)


if __name__ == "__main__":
    app = QApplication([])

    app.exec_()
