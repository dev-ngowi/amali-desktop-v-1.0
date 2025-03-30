from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *

class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
        QWidget {
            background-color: #2c3e50;
            color: white;
        }
        QPushButton {
            border: none;
            text-align: left;
            padding: 15px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #34495e;
        }
        QPushButton:checked {
            background-color: #3498db;
        }
        """)
        self.setFixedWidth(230)
        self.resize(300, 800)

        # Create scroll area
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Container widget for scroll area
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Logo
        self.company_label = QLabel()
        self.logo_pixmap = QPixmap("Resources/Images/logo.png")
        self.company_label.setPixmap(self.logo_pixmap.scaled(120, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.company_label.setStyleSheet("padding: 12px; background-color: #1a2634;")
        self.company_label.setFixedHeight(70)
        self.layout.addWidget(self.company_label)

        # Menu buttons
        self.buttons = {}
        self.create_button("Dashboard")
        self.create_button("Stock")
        self.create_button("Sales")
        self.create_button("Reports")
        self.create_button("Users") 

        # Submenus
        self.setup_submenu("Inventory", ["Item Category", "Item Group", "Item Type", "Items"])
        self.setup_submenu("Purchases", ["Purchase Order", "Good Receive Note", "Goods Returns", "Goods Issued Note"])
        self.setup_submenu("User Management", ["User Role", "Users", "Permissions"])
        self.setup_submenu("Settings", ["Company Details", "Virtual Devices"])

        self.layout.addStretch()

       # Add Logout button at the bottom
        logout_button = QPushButton("Logout")
        logout_icon = QIcon("Resources/Images/logout_logo.png")  
        logout_button.setIcon(logout_icon) 

        # Style the QPushButton
        logout_button.setStyleSheet("""
            QPushButton {
                color: white;  /* Text color */
                font-weight: bold;
                padding: 10px 15px;  /* Adjust padding */
                font-size: 14px;
                border-radius: 5px;  /* Add rounded corners */
            }
            QPushButton:hover {
                background-color: #2c3e50;  /* Darker color on hover */
            }
            QPushButton::icon {
                color: white;  /* Icon color is handled via the SVG itself */
            }
        """)

        logout_button.setFixedHeight(50)

        # Add the button to the layout
        if hasattr(self, "layout"):  # Check if the layout attribute exists
            self.layout.addWidget(logout_button)
        else:
            raise AttributeError("The 'self.layout' attribute is not defined. Please ensure the layout is set up.")

        # Connect the logout button to the logout handler function
        logout_button.clicked.connect(self.handle_logout)

        # Set container as scroll area widget
        self.scroll.setWidget(container)

        # Main layout for sidebar
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll)

    def create_button(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setFixedHeight(40)
        self.layout.addWidget(btn)
        self.buttons[text] = btn
        return btn

    def setup_submenu(self, title, items):
        main_btn = QPushButton(title)
        main_btn.setCheckable(True)
        main_btn.setFixedHeight(40)
        self.layout.addWidget(main_btn)

        submenu = QWidget()
        submenu_layout = QVBoxLayout(submenu)
        submenu_layout.setContentsMargins(0, 0, 0, 0)
        submenu_layout.setSpacing(0)
        submenu.setVisible(False)

        for item in items:
            sub_btn = QPushButton(item)
            sub_btn.setStyleSheet("padding-left: 30px;")
            sub_btn.setFixedHeight(45)
            submenu_layout.addWidget(sub_btn)

        self.layout.addWidget(submenu)
        main_btn.clicked.connect(lambda: submenu.setVisible(not submenu.isVisible()))
        
    def handle_logout(self):
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.quit()
