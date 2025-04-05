import hashlib
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import os
from Helper.db_conn import db
from Application.Components.main import DashboardView
import bcrypt


def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Boot(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AMALI Login")

        # Set fixed size for the dialog to 500x500
        self.setFixedSize(500, 500)

        # Center the dialog on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2
        )

        self.setStyleSheet("background-color: #2c3e50;")  # Changed to match background

        # Main layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        # Center everything vertically and horizontally
        centerLayout = QVBoxLayout()
        centerLayout.addStretch(1)  # Add space above

        # Logo
        self.logo_label = QLabel()
        logo_path = get_resource_path("Resources/Images/logo.png")
        self.logo_pixmap = QPixmap(logo_path)
        if not self.logo_pixmap.isNull():
            self.logo_label.setPixmap(
                self.logo_pixmap.scaled(
                    200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
            print(f"Boot: Logo loaded from: {logo_path}")
        else:
            self.logo_label.setText("Logo Not Found")
            self.logo_label.setStyleSheet("color: white; font-size: 20px;")
            print(f"Boot: Failed to load logo from: {logo_path}")
        self.logo_label.setAlignment(Qt.AlignCenter)

        # Login container
        centerContainer = QWidget()
        centerContainer.setFixedWidth(350)  # Fixed width for login form
        centerContainer.setStyleSheet(
            "QWidget { background-color: white; border-radius: 8px; }"
        )

        formLayout = QVBoxLayout()
        formLayout.setSpacing(8)
        formLayout.setContentsMargins(20, 20, 20, 20)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Password")
        self.loginBtn = QPushButton("Login")
        self.loginBtn.clicked.connect(self.onClickLogin)

        centerContainer.setStyleSheet(
            """
            QWidget { background-color: white; border-radius: 8px; }
            QLineEdit { padding: 8px; border: 1px solid #bdc3c7; border-radius: 5px; margin: 2px 0; }
            QPushButton { background-color: #3498db; color: white; padding: 10px; border: none; border-radius: 5px; font-weight: bold; min-width: 100px; }
            QPushButton:hover { background-color: #2980b9; }
            QLabel { color: #2c3e50; }
            """
        )

        formLayout.addWidget(QLabel("Username"))
        formLayout.addWidget(self.username)
        formLayout.addWidget(QLabel("Password"))
        formLayout.addWidget(self.password)
        formLayout.addSpacing(20)
        formLayout.addWidget(self.loginBtn)
        centerContainer.setLayout(formLayout)

        # Add widgets to center layout
        centerLayout.addWidget(self.logo_label)
        centerLayout.addWidget(centerContainer, alignment=Qt.AlignHCenter)
        centerLayout.addStretch(1)  # Add space below

        # Add centerLayout to mainLayout with horizontal centering
        mainWidget = QWidget()
        mainWidget.setLayout(centerLayout)
        self.mainLayout.addWidget(mainWidget, alignment=Qt.AlignCenter)
        self.setLayout(self.mainLayout)

    def onClickLogin(self):
        username = self.username.text().strip()
        password = self.password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password are required!")
            return

        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                sql_query = "SELECT password FROM users WHERE username = ?"
                cursor.execute(sql_query, (username,))
                result = cursor.fetchone()

            if result:
                stored_hashed_password = result[0]
                if bcrypt.checkpw(
                    password.encode("utf-8"), stored_hashed_password.encode("utf-8")
                ):
                    print("Boot: Login successful!")
                    self.ensure_store_exists()
                    self.accept() 
                else:
                    QMessageBox.warning(self, "Error", "Incorrect username or password")
            else:
                QMessageBox.warning(self, "Error", "Incorrect username or password")
        except sqlite3.OperationalError as e:
            QMessageBox.critical(self, "Error", f"Boot: Database error: {e}")

    def ensure_store_exists(self):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stores")
            store_count = cursor.fetchone()[0]
            if store_count == 0:
                print("Boot: No stores found. Creating default store after login.")
                cursor.execute("SELECT id FROM users WHERE username = 'admin'")
                admin = cursor.fetchone()
                if not admin:
                    hashed_password = bcrypt.hashpw(
                        "admin123".encode("utf-8"), bcrypt.gensalt()
                    )
                    cursor.execute(
                        """
                        INSERT INTO users (fullname, username, password, pin, created_at, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        ("Administrator", "admin", hashed_password, 1234),
                    )
                    conn.commit()
                    admin_id = cursor.lastrowid
                else:
                    admin_id = admin[0]

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO stores (id, name, location, manager_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (1, "Mohalal Shop", "Forest", admin_id),
                )
                conn.commit()
                print("Boot: Default store 'Mohalal Shop' created successfully.")
            else:
                print(f"Boot: Found {store_count} existing stores.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    bootUI = Boot()
    if bootUI.exec_() == QDialog.Accepted:
        print("Boot: Opening DashboardView...")
        main_window = DashboardView()
        main_window.showMaximized()
    else:
        print("Boot: Login dialog was rejected or closed.")
    sys.exit(app.exec_())
