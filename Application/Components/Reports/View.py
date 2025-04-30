# main_report.py
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
    QListWidgetItem,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
from Application.Components.Reports.business_health_report import BusinessHealthReport
from Application.Components.Reports.daily_financials_report import DailyFinancialsReport
from Application.Components.Reports.dead_stock_report import DeadStockReport
from Application.Components.Reports.expenses_detailed_report import (
    ExpensesDetailedReport,
)
from Application.Components.Reports.expenses_report import ExpensesReport
from Application.Components.Reports.modal import ReportManager
from Application.Components.Reports.sales_detailed_report import SalesDetailedReport
from Application.Components.Reports.sales_summary_report import SalesSummaryReport
from Application.Components.Reports.stock_ledger_report import StockLedgerReport
from Application.Components.Reports.stock_level_report import StockLevelReport
from Application.Components.Reports.top_selling_items_report import (
    TopSellingItemsReport,
)


class ReportView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Report View")
        self.setGeometry(100, 100, 900, 700)

        self.report_manager = ReportManager()
        self.stores_data = self.report_manager.get_stores_data()

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # Sidebar with styling
        self.sidebar = QListWidget()
        self.sidebar.setMinimumWidth(200)  # Fixed width for consistency
        self.sidebar.setMaximumWidth(250)
        self.sidebar.setFont(QFont("Arial", 10))

        # Sidebar items with icons (optional: add icon paths if available)
        report_items = [
            ("Sales Summary", "icons/sales_summary.png"),
            ("Sales Detailed Report", "icons/sales_detailed.png"),
            ("Top Selling Items Reports", "icons/top_selling.png"),
            ("Stock Ledger Report", "icons/stock_ledger.png"),
            ("Stock Level Report", "icons/stock_level.png"),
            ("Dead Stock Report", "icons/dead_stock.png"),
            ("Expenses Report", "icons/expenses.png"),
            ("Expenses Detailed Report", "icons/expenses_detailed.png"),
            ("Daily Financial Report", "icons/daily_financials.png"),
            ("Business Health", "icons/business_health.png"),
        ]

        for text, icon_path in report_items:
            item = QListWidgetItem(text)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            # Uncomment and adjust icon_path if you have icons
            # item.setIcon(QIcon(icon_path))
            self.sidebar.addItem(item)

        # Apply stylesheet to sidebar
        self.sidebar.setStyleSheet(
            """
            QListWidget {
                background-color: #2b2d42;  /* Dark blue-gray background */
                color: #edf2f4;             /* Light text color */
                border: none;
                padding: 10px;
            }
            QListWidget::item {
                padding: 12px 15px;         /* Increased padding for spacing */
                border-bottom: 1px solid #3d405b; /* Subtle separator */
            }
            QListWidget::item:selected {
                background-color: #ef233c;  /* Bright red for selection */
                color: white;
                border-radius: 5px;
            }
            QListWidget::item:hover:!selected {
                background-color: #ADD8E6;  /* Lighter hover effect */
                color: #000000;
                border-radius: 5px;
            }
        """
        )

        self.sidebar.currentRowChanged.connect(self.switch_report_view)
        main_layout.addWidget(self.sidebar)

        # Main Report Area
        self.report_area = QStackedWidget()

        # Initialize report views
        self.sales_summary_view = SalesSummaryReport(
            self.report_manager, self.stores_data
        )
        self.report_area.addWidget(self.sales_summary_view)

        self.sales_detailed_report_view = SalesDetailedReport(
            self.report_manager, self.stores_data
        )
        self.report_area.addWidget(self.sales_detailed_report_view)

        self.top_selling_items_view = TopSellingItemsReport(
            self.report_manager, self.stores_data
        )
        self.report_area.addWidget(self.top_selling_items_view)

        self.stock_ledger_view = StockLedgerReport(
            self.report_manager, self.stores_data
        )
        self.report_area.addWidget(self.stock_ledger_view)

        self.stock_level_view = StockLevelReport(self.report_manager, self.stores_data)
        self.report_area.addWidget(self.stock_level_view)

        self.dead_stock_view = DeadStockReport(self.report_manager, self.stores_data)
        self.report_area.addWidget(self.dead_stock_view)

        self.expenses_view = ExpensesReport(self.report_manager, self.stores_data)
        self.report_area.addWidget(self.expenses_view)

        self.expenses_detailed_view = ExpensesDetailedReport(
            self.report_manager, self.stores_data
        )
        self.report_area.addWidget(self.expenses_detailed_view)

        self.daily_financials_view = DailyFinancialsReport(self.report_manager)
        self.report_area.addWidget(self.daily_financials_view)

        self.business_health_view = BusinessHealthReport(
            self.report_manager, self.stores_data
        )
        self.report_area.addWidget(self.business_health_view)

        main_layout.addWidget(self.report_area)

        # Adjust layout stretch
        main_layout.setStretch(0, 2)  # Sidebar 20%
        main_layout.setStretch(1, 8)  # Report area 80%

        self.setLayout(main_layout)

    def switch_report_view(self, index):
        self.report_area.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Optional: Set a global stylesheet for consistency
    app.setStyleSheet(
        """
        QWidget {
            font-family: Arial;
            font-size: 12px;
        }
    """
    )
    window = ReportView()
    window.show()
    sys.exit(app.exec_())
