import sys
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from Helper.db_conn import db 

class Users(QWidget):
    def __init__(self):
        super().__init__()
        self.current_page = 1
        self.items_per_page = 10
        self.total_users = 0
        self.sort_column = 0
        self.sort_order = Qt.AscendingOrder

        self.initUI()
        self.loadUsers()

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f9;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header = self.createHeader()
        main_layout.addWidget(header)

        user_card = self.createUserManagementCard()  # Corrected method name
        main_layout.addWidget(user_card)

        self.setLayout(main_layout)
        self.setWindowTitle("User  Management")

    def createHeader(self):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)

        title = QLabel("User  Management")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        """)

        subtitle = QLabel("Manage users and their access")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(subtitle)

        return header_widget

    def createUserManagementCard(self):  # Corrected method name
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 20px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        action_layout = self.createActionLayout()
        card_layout.addLayout(action_layout)

        self.table = self.createUserTable()  # Ensure this method is defined correctly
        card_layout.addWidget(self.table)

        pagination_layout = self.createPaginationLayout()
        card_layout.addLayout(pagination_layout)

        return card

    def createActionLayout(self):
        action_layout = QHBoxLayout()

        self.searchInput = QLineEdit()
        self.searchInput.setPlaceholderText("🔍 Search users...")
        self.searchInput.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """)
        self.searchInput.textChanged.connect(self.searchUsers)
        action_layout.addWidget(self.searchInput)

        addBtn = QPushButton("+ Add User")
        addBtn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 15px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        addBtn.clicked.connect(self.showAddDialog)
        action_layout.addWidget(addBtn)

        return action_layout

    def createUserTable(self):  # Ensure this method is defined correctly
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Username", "Edit", "Delete"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().sectionClicked.connect(self.sortTable)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        return table

    def createPaginationLayout(self):
        pagination_layout = QHBoxLayout()

        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prevPage)

        self.page_label = QLabel("Page 1")

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.nextPage)

        self.items_per_page_combo = QComboBox()
        self.items_per_page_combo.addItems(["10", "25", "50", "100"])
        self.items_per_page_combo.currentTextChanged.connect(self.changeItemsPerPage)

        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addWidget(QLabel("Items per page:"))
        pagination_layout.addWidget(self.items_per_page_combo)

        return pagination_layout

    def loadUsers(self, search_term=""):
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                base_query = "SELECT id, username FROM users"
                count_query = "SELECT COUNT(*) FROM users"
                params = []

                if search_term:
                    base_query += " WHERE username LIKE ?"
                    count_query += " WHERE username LIKE ?"
                    params.append(f"%{search_term}%")

                sort_columns = ["id", "username"]
                base_query += f" ORDER BY {sort_columns[self.sort_column]} {'ASC' if self.sort_order == Qt.AscendingOrder else 'DESC'}"

                offset = (self.current_page - 1) * self.items_per_page
                base_query += " LIMIT ? OFFSET ?"
                params.extend([self.items_per_page, offset])

                cursor.execute(count_query, params[:-2] if search_term else [])
                self.total_users = cursor.fetchone()[0]

                cursor.execute(base_query, params)
                users = cursor.fetchall()

                self.populateTable(users)
                self.updatePaginationControls()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load users: {str(e)}")

    def populateTable(self, users):
        self.table.setRowCount(0)
        for row_num, (user_id, username) in enumerate(users):
            self.table.insertRow(row_num)

            self.table.setItem(row_num, 0, QTableWidgetItem(str(user_id)))
            self.table.setItem(row_num, 1, QTableWidgetItem(username))

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _, uid=user_id: self.showEditDialog(uid))
            self.table.setCellWidget(row_num, 2, edit_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda _, uid=user_id: self.deleteUser (uid))
            self.table.setCellWidget(row_num, 3, delete_btn)

    def updatePaginationControls(self):
        total_pages = (self.total_users + self.items_per_page - 1) // self.items_per_page
        self.page_label.setText(f"Page {self.current_page} of {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)

    def searchUsers(self):
        search_term = self.searchInput.text()
        self.current_page = 1
        self.loadUsers(search_term)

    def sortTable(self, column):
        if self.sort_column == column:
            self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.sort_column = column
            self.sort_order = Qt.AscendingOrder

        self.loadUsers(self.searchInput.text())

    def prevPage(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.loadUsers(self.searchInput.text())

    def nextPage(self):
        total_pages = (self.total_users + self.items_per_page - 1) // self.items_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self.loadUsers(self.searchInput.text())

    def changeItemsPerPage(self, value):
        self.items_per_page = int(value)
        self.current_page = 1
        self.loadUsers(self.searchInput.text())

    def showAddDialog(self):
        dialog = UserDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.loadUsers()

    def showEditDialog(self, user_id):
        dialog = UserDialog(user_id)
        if dialog.exec_() == QDialog.Accepted:
            self.loadUsers()

    def deleteUser (self, user_id):
        reply = QMessageBox.question(self, "Delete User", "Are you sure you want to delete this user?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    conn.commit()
                self.loadUsers()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Could not delete user: {str(e)}")


class UserDialog(QDialog):
    def __init__(self, user_id=None):
        super().__init__()
        self.user_id = user_id
        self.initUI()
        self.setWindowTitle("Edit User" if user_id else "Add User")
        self.setMinimumSize(400, 250)

    def initUI(self):
        layout = QVBoxLayout()
        
        self.setStyleSheet(
            """
            QDialog {
                background-color: white;
                border-radius: 12px;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """
        )

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        if self.user_id:
            self.loadUserData()

    def loadUserData(self):
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE id = ?", (self.user_id,))
                user = cursor.fetchone()
                if user:
                    self.username_input.setText(user[0])
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Could not load user data: {str(e)}")

    def save(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password are required")
            return

        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                if self.user_id:
                    cursor.execute("UPDATE users SET username = ?, password = ? WHERE id = ?", (username, password, self.user_id))
                else:
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
            self.accept()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Could not save user: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Users()
    window.show()
    sys.exit(app.exec_())