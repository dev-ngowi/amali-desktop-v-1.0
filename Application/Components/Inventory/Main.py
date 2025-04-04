import sys

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QDockWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QStackedWidget,
)

from PyQt5.QtCore import Qt

from Application.Components.Inventory.Category.category import CategoriesView
from Application.Components.Inventory.Expenses.view import ExpensesView
from Application.Components.Inventory.ItemCosts.view import CostStockView
from Application.Components.Inventory.ItemGroup.item_group import ItemGroupView
from Application.Components.Inventory.ItemType.view import ItemTypeView
from Application.Components.Inventory.Items.model import ItemManager
from Application.Components.Inventory.Items.register import AddItemWindow
from Application.Components.Inventory.Items.update import EditItemWindow
from Application.Components.Inventory.Items.view import ItemsView
from Application.Components.Inventory.Stores.store import StoresView
from Application.Components.Inventory.Units.view import UnitView
from Application.Components.Settings.Payments.view import PaymentsMainView


class InventoryView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("This is the Inventory View"))
        self.setLayout(layout)


class MainInventoryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Application")
        self.setGeometry(100, 100, 800, 600)

        self.item_manager = ItemManager()
        self.sidebar = QDockWidget("Menu", self)
        self.sidebar.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.sidebar.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.sidebar_widget = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)

        self.menu_tree = QTreeWidget()
        self.menu_tree.setHeaderHidden(True)
        self.menu_tree.setStyleSheet(
            """
            QTreeWidget {
                background-color: #f0f0f0;
                border: none;
                font-size: 14px;
            }
            QTreeWidget::item {
                padding: 5px;
                height: 25px;
            }
            QTreeWidget::item:hover {
                background-color: #e0e0e0;
            }
            QTreeWidget::item:selected {
                background-color: #d0d0d0;
                color: black;
            }
            QTreeWidget::branch {
                background: transparent;
            }
        """
        )
        self.menu_tree.setRootIsDecorated(False)

        stores_item = QTreeWidgetItem(self.menu_tree, ["Stores"])
        expenses = QTreeWidgetItem(self.menu_tree, ["Expenses"])
        payments_item = QTreeWidgetItem(self.menu_tree, ["Payments"])
        self.inventory_item = QTreeWidgetItem(self.menu_tree, ["Inventory +"])

        item_category_item = QTreeWidgetItem(self.inventory_item, ["Item Category"])
        item_group_item = QTreeWidgetItem(self.inventory_item, ["Item Group"])
        item_type_item = QTreeWidgetItem(self.inventory_item, ["Item Type"])
        unit_item = QTreeWidgetItem(self.inventory_item, ["Unit"])
        items_item = QTreeWidgetItem(self.inventory_item, ["Items"])
        cost_stock_item = QTreeWidgetItem(self.inventory_item, ["Cost & Stock"])

        self.menu_tree.setIndentation(20)

        self.sidebar_layout.addWidget(self.menu_tree)
        self.sidebar_widget.setLayout(self.sidebar_layout)
        self.sidebar.setWidget(self.sidebar_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.inventory_view = InventoryView()
        self.stores_view = StoresView()
        self.expenses_view = ExpensesView()
        self.payments_view = PaymentsMainView()
        self.item_category_view = CategoriesView()
        self.item_group_view = ItemGroupView()
        self.item_type_view = ItemTypeView()
        self.unit_view = UnitView()
        self.items_view = ItemsView()  # Only ItemsView is added to the stack
        self.cost_stock_view = CostStockView()

        self.central_widget.addWidget(self.stores_view)
        self.central_widget.addWidget(self.expenses_view)
        self.central_widget.addWidget(self.payments_view)
        self.central_widget.addWidget(self.inventory_view)
        self.central_widget.addWidget(self.item_category_view)
        self.central_widget.addWidget(self.item_group_view)
        self.central_widget.addWidget(self.item_type_view)
        self.central_widget.addWidget(self.unit_view)
        self.central_widget.addWidget(self.items_view)
        self.central_widget.addWidget(self.cost_stock_view)

        self.menu_tree.itemClicked.connect(self.handle_menu_click)
        self.menu_tree.itemExpanded.connect(self.update_indicator_expanded)
        self.menu_tree.itemCollapsed.connect(self.update_indicator_collapsed)

        self.central_widget.setCurrentWidget(self.stores_view)

    def update_indicator_expanded(self, item):
        if item.childCount() > 0:
            item.setText(0, item.text(0).replace("+", "-"))

    def update_indicator_collapsed(self, item):
        if item.childCount() > 0:
            item.setText(0, item.text(0).replace("-", "+"))

    def handle_menu_click(self, item, column):
        text = item.text(column)
        if item.childCount() > 0:
            if text.endswith("+"):
                self.menu_tree.expandItem(item)
            elif text.endswith("-"):
                self.menu_tree.collapseItem(item)
            return

        if text == "Stores":
            self.central_widget.setCurrentWidget(self.stores_view)
        elif text == "Expenses":
            self.central_widget.setCurrentWidget(self.expenses_view)
        elif text == "Payments":
            self.central_widget.setCurrentWidget(self.payments_view)
        elif text == "Item Category":
            self.central_widget.setCurrentWidget(self.item_category_view)
        elif text == "Item Group":
            self.central_widget.setCurrentWidget(self.item_group_view)
        elif text == "Item Type":
            self.central_widget.setCurrentWidget(self.item_type_view)
        elif text == "Unit":
            self.central_widget.setCurrentWidget(self.unit_view)
        elif text == "Items":
            self.central_widget.setCurrentWidget(self.items_view)
        elif text == "Cost & Stock":
            self.central_widget.setCurrentWidget(self.cost_stock_view)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainInventoryWindow()
    main_window.show()
    sys.exit(app.exec_())
