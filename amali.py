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
from datetime import date, timedelta
from Application.Components.DayClose.day_close import DayCloseView
from Application.Components.DayClose.modal import DayCloseManager


def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Boot(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AMALI Login")
        self.db_helper = DayCloseManager()
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        width = screen_size.width()
        height = screen_size.height()

        self.setGeometry(0, 0, width, height)
        self.setStyleSheet("background-color: #ffffff;")

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        backgroundWidget = QWidget()
        backgroundWidget.setStyleSheet("background-color: #2c3e50;")
        backgroundLayout = QVBoxLayout()
        backgroundLayout.setContentsMargins(0, 0, 0, 50)

        self.logo_label = QLabel()
        logo_path = get_resource_path("Resources/Images/logo.png")
        self.logo_pixmap = QPixmap(logo_path)
        if not self.logo_pixmap.isNull():
            self.logo_label.setPixmap(
                self.logo_pixmap.scaled(
                    200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
            print(f"Logo loaded from: {logo_path}")
        else:
            self.logo_label.setText("Logo Not Found")
            self.logo_label.setStyleSheet("color: white; font-size: 20px;")
            print(f"Failed to load logo from: {logo_path}")
        self.logo_label.setAlignment(Qt.AlignCenter)

        centerContainer = QWidget()
        centerContainer.setMaximumWidth(400)
        centerContainer.setStyleSheet(
            "QWidget { background-color: white; border-radius: 8px; }"
        )

        formLayout = QVBoxLayout()
        formLayout.setSpacing(15)
        formLayout.setContentsMargins(40, 40, 40, 40)

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
            QLineEdit { padding: 10px; border: 1px solid #bdc3c7; border-radius: 5px; margin: 5px 0; }
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

        centeringLayout = QHBoxLayout()
        centeringLayout.addStretch()
        centeringLayout.addWidget(centerContainer)
        centeringLayout.addStretch()

        backgroundLayout.addWidget(self.logo_label)
        backgroundLayout.addLayout(centeringLayout)
        backgroundWidget.setLayout(backgroundLayout)
        self.mainLayout.addWidget(backgroundWidget)
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
                    print("Login successful!")
                    self.ensure_store_exists()
                    self.check_day_close()
                else:
                    QMessageBox.warning(self, "Error", "Incorrect username or password")
            else:
                QMessageBox.warning(self, "Error", "Incorrect username or password")
        except sqlite3.OperationalError as e:
            QMessageBox.critical(self, "Error", f"Database error: {e}")

    def ensure_store_exists(self):
        stores = self.db_helper.get_stores_data()
        if not stores:
            print("No stores found. Creating default store after login.")
            with db.get_connection() as conn:
                cursor = conn.cursor()
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
                print("Default store 'Mohalal Shop' created successfully.")
        else:
            print(f"Found {len(stores)} existing stores: {stores}")

    def check_day_close(self):
        current_date = date.today() - timedelta(days=1)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM day_close WHERE working_date = ?",
                (current_date.strftime("%Y-%m-%d"),),
            )
            count = cursor.fetchone()[0]

        if count == 0:
            reply = QMessageBox.question(
                self,
                "Day Close Required",
                f"No day close record found for {current_date.strftime('%Y-%m-%d')}. Would you like to perform it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                day_close_window = DayCloseView(db_helper=self.db_helper)
                day_close_window.show()
                # Wait for the day close window to close before proceeding
                loop = QEventLoop()
                day_close_window.destroyed.connect(loop.quit)
                loop.exec_()
                # After day close, proceed to dashboard
                self.accept()
            else:
                self.accept()
        else:
            self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    bootUI = Boot()
    if bootUI.exec_() == QDialog.Accepted:
        print("Opening DashboardView...")
        main_window = DashboardView()
        main_window.showMaximized()
    else:
        print("Login dialog was rejected or closed.")
    sys.exit(app.exec_())
