# model.py
import logging
import sqlite3
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExpenseManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        # Removed self._create_item_prices_table()

    def _get_connection(self):
        """Get a new database connection."""
        with self.db_manager.lock:
            conn = sqlite3.connect(self.db_manager.db_path, timeout=30)
        return conn

    def _commit_and_close(self, conn):
        """Commit changes and close the connection."""
        try:
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error committing changes: {str(e)}")
        finally:
            conn.close()

    def get_users(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, username
                FROM users
                """
            )
            users = [{"id": row[0], "username": row[1]} for row in cursor.fetchall()]
            if not users:
                logger.warning("No users found in the database.")
            else:
                logger.info(f"Successfully retrieved {len(users)} users for expenses.")
            return users
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve users for expenses: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_items(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, name
                FROM items
                """
            )
            items = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
            logger.info(f"Successfully retrieved {len(items)} items for expenses.")
            return items
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve items for expenses: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_item_price(self, item_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT amount
                FROM item_prices
                WHERE item_id = ?
                LIMIT 1 -- Assuming one price per item for simplicity
                """,
                (item_id,),
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            return 0.0
        except sqlite3.Error as e:
            logger.error(f"Error getting price for item ID {item_id}: {e}")
            return 0.0
        finally:
            self._commit_and_close(conn)

    def save_expense(
        self,
        expense_type,
        user_id,
        expense_date,
        amount,
        description=None,
        reference_number=None,
        receipt_path=None,
        linked_shop_item_ids=None,  # Changed to a list
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO expenses (
                    expense_type, user_id, expense_date, amount, description,
                    reference_number, receipt_path,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                (
                    expense_type,
                    user_id,
                    expense_date,
                    amount,
                    description,
                    reference_number,
                    receipt_path,
                ),
            )
            expense_id = cursor.lastrowid
            if linked_shop_item_ids:
                for item_id in linked_shop_item_ids:
                    cursor.execute(
                        """
                        INSERT INTO expense_items (expense_id, item_id)
                        VALUES (?, ?)
                        """,
                        (expense_id, item_id),
                    )
            logger.info(
                f"Expense of type '{expense_type}' saved successfully with ID: {expense_id}."
            )
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving expense of type '{expense_type}': {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def get_expenses_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    e.id, e.expense_type, e.user_id, e.expense_date, e.amount,
                    e.description, e.reference_number, e.receipt_path,
                    e.created_at, e.updated_at,
                    u.username
                FROM expenses e
                JOIN users u ON e.user_id = u.id
                """
            )
            expenses = [
                {
                    "id": row[0],
                    "expense_type": row[1],
                    "user_id": row[2],
                    "expense_date": row[3],
                    "amount": row[4],
                    "description": row[5],
                    "reference_number": row[6],
                    "receipt_path": row[7],
                    "created_at": row[8],
                    "updated_at": row[9],
                    "username": row[10],
                    "linked_item_names": [],  # Initialize as empty list
                }
                for row in cursor.fetchall()
            ]

            # Fetch linked items for each expense
            for expense in expenses:
                cursor.execute(
                    """
                    SELECT i.name
                    FROM expense_items ei
                    JOIN items i ON ei.item_id = i.id
                    WHERE ei.expense_id = ?
                    """,
                    (expense["id"],),
                )
                linked_items = [row[0] for row in cursor.fetchall()]
                expense["linked_item_names"] = ", ".join(linked_items)  # Join names

            logger.info(f"Retrieved {len(expenses)} expenses.")
            return expenses
        except sqlite3.Error as e:
            logger.error(f"Error retrieving expenses data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def update_expense(
        self,
        expense_id,
        expense_type=None,
        user_id=None,
        expense_date=None,
        amount=None,
        description=None,
        reference_number=None,
        receipt_path=None,
        linked_shop_item_ids=None,  # Changed to a list
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE expenses
                SET
                    expense_type = ?,
                    user_id = ?,
                    expense_date = ?,
                    amount = ?,
                    description = ?,
                    reference_number = ?,
                    receipt_path = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    expense_type,
                    user_id,
                    expense_date,
                    amount,
                    description,
                    reference_number,
                    receipt_path,
                    expense_id,
                ),
            )

            # Update linked items
            cursor.execute(
                "DELETE FROM expense_items WHERE expense_id = ?", (expense_id,)
            )
            if linked_shop_item_ids:
                for item_id in linked_shop_item_ids:
                    cursor.execute(
                        """
                        INSERT INTO expense_items (expense_id, item_id)
                        VALUES (?, ?)
                        """,
                        (expense_id, item_id),
                    )

            logger.info(f"Expense with ID {expense_id} updated successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating expense with ID {expense_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def delete_expense(self, expense_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            logger.info(f"Expense with ID {expense_id} deleted successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting expense with ID {expense_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def get_linked_item_ids(self, expense_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT item_id
                FROM expense_items
                WHERE expense_id = ?
                """,
                (expense_id,),
            )
            item_ids = [row[0] for row in cursor.fetchall()]
            return item_ids
        except sqlite3.Error as e:
            logger.error(
                f"Error getting linked item IDs for expense {expense_id}: {str(e)}"
            )
            return []
        finally:
            self._commit_and_close(conn)
