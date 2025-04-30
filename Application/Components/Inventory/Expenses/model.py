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

    def _get_connection(self):
        with self.db_manager.lock:
            conn = sqlite3.connect(
                self.db_manager.db_path, timeout=60
            )  # Increased timeout
        return conn

    def _commit_and_close(self, conn):
        try:
            logger.debug("Attempting to commit changes")
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error committing changes: {str(e)}")
            conn.rollback()
            raise
        finally:
            try:
                logger.debug("Closing database connection")
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")

    def get_users(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, username FROM users")
            users = [{"id": row[0], "username": row[1]} for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(users)} users.")
            return users
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve users: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_items(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name FROM items")
            items = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(items)} items.")
            return items
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve items: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_item_price(self, item_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT amount FROM item_prices WHERE item_id = ? LIMIT 1", (item_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0.0
        except sqlite3.Error as e:
            logger.error(f"Error getting price for item ID {item_id}: {e}")
            return 0.0
        finally:
            self._commit_and_close(conn)

    def _get_total_sales_for_date_with_conn(self, expense_date, conn):
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT SUM(ground_total) FROM orders WHERE DATE(date) = ? AND status = 'completed'",
                (expense_date,),
            )
            result = cursor.fetchone()
            total_sales = result[0] if result[0] is not None else 0.0
            logger.info(
                f"Total sales for {expense_date} (in transaction): {total_sales}"
            )
            return total_sales
        except sqlite3.Error as e:
            logger.error(f"Error retrieving total sales for {expense_date}: {str(e)}")
            return 0.0

    def _get_total_expenses_for_date_with_conn(self, expense_date, conn):
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT SUM(amount) FROM expenses WHERE expense_date = ?",
                (expense_date,),
            )
            result = cursor.fetchone()
            total_expenses = result[0] if result[0] is not None else 0.0
            logger.info(
                f"Total expenses for {expense_date} (in transaction): {total_expenses}"
            )
            return total_expenses
        except sqlite3.Error as e:
            logger.error(
                f"Error retrieving total expenses for {expense_date}: {str(e)}"
            )
            return 0.0

    def get_total_sales_for_date(self, expense_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT SUM(ground_total) FROM orders WHERE DATE(date) = ? AND status = 'completed'",
                (expense_date,),
            )
            result = cursor.fetchone()
            total_sales = result[0] if result[0] is not None else 0.0
            logger.info(f"Total sales for {expense_date}: {total_sales}")
            return total_sales
        except sqlite3.Error as e:
            logger.error(f"Error retrieving total sales for {expense_date}: {str(e)}")
            return 0.0
        finally:
            self._commit_and_close(conn)

    def get_total_expenses_for_date(self, expense_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT SUM(amount) FROM expenses WHERE expense_date = ?",
                (expense_date,),
            )
            result = cursor.fetchone()
            total_expenses = result[0] if result[0] is not None else 0.0
            logger.info(f"Total expenses for {expense_date}: {total_expenses}")
            return total_expenses
        except sqlite3.Error as e:
            logger.error(
                f"Error retrieving total expenses for {expense_date}: {str(e)}"
            )
            return 0.0
        finally:
            self._commit_and_close(conn)

    def _update_daily_financials_with_conn(self, date, conn):
        cursor = conn.cursor()
        try:
            logger.info(f"Updating daily financials for {date} within transaction")
            total_orders = self._get_total_sales_for_date_with_conn(date, conn)
            total_expenses = self._get_total_expenses_for_date_with_conn(date, conn)
            after_expenses = total_orders - total_expenses

            logger.info(
                f"Calculated: total_orders={total_orders}, total_expenses={total_expenses}, after_expenses={after_expenses}"
            )

            # Check if record exists
            cursor.execute(
                "SELECT id FROM daily_financials WHERE DATE(date) = ?", (date,)
            )
            existing = cursor.fetchone()

            if existing:
                logger.info(f"Updating existing daily_financials record for {date}")
                cursor.execute(
                    """
                    UPDATE daily_financials
                    SET total_orders = ?, total_expenses = ?, after_expenses = ?, updated_at = datetime('now')
                    WHERE DATE(date) = ?
                    """,
                    (total_orders, total_expenses, after_expenses, date),
                )
            else:
                logger.info(f"Inserting new daily_financials record for {date}")
                cursor.execute(
                    """
                    INSERT INTO daily_financials (date, total_orders, total_expenses, after_expenses, created_at, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (date, total_orders, total_expenses, after_expenses),
                )

            logger.info(
                f"Successfully updated daily financials for {date} within transaction"
            )
        except sqlite3.Error as e:
            logger.error(
                f"Database error updating daily financials for {date}: {str(e)}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error updating daily financials for {date}: {str(e)}"
            )
            raise

    def update_daily_financials(self, date):
        conn = self._get_connection()
        try:
            logger.info(f"Starting standalone update_daily_financials for {date}")
            self._update_daily_financials_with_conn(date, conn)
            conn.commit()
            logger.info(f"Standalone update_daily_financials for {date} completed")
        except sqlite3.Error as e:
            logger.error(
                f"Error in standalone update_daily_financials for {date}: {str(e)}"
            )
            conn.rollback()
            raise
        finally:
            self._commit_and_close(conn)

    def get_daily_financials(self, date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT total_orders, total_expenses, after_expenses FROM daily_financials WHERE DATE(date) = ?",
                (date,),
            )
            result = cursor.fetchone()
            if result:
                return {
                    "total_orders": result[0],
                    "total_expenses": result[1],
                    "after_expenses": result[2],
                }
            return {"total_orders": 0.0, "total_expenses": 0.0, "after_expenses": 0.0}
        except sqlite3.Error as e:
            logger.error(f"Error retrieving daily financials for {date}: {str(e)}")
            return {"total_orders": 0.0, "total_expenses": 0.0, "after_expenses": 0.0}
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
        linked_shop_item_ids=None,
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Validate inputs
            if not expense_type in ["home", "shop"]:
                raise ValueError(f"Invalid expense_type: {expense_type}")
            if not isinstance(amount, (int, float)) or amount < 0:
                raise ValueError(f"Invalid amount: {amount}")

            # Validate user_id exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                raise ValueError(f"User ID {user_id} does not exist")

            # Check total sales constraint
            total_sales = self._get_total_sales_for_date_with_conn(expense_date, conn)
            logger.info(
                f"Checking total sales ({total_sales}) against expense amount ({amount})"
            )
            if amount > total_sales:
                return (
                    False,
                    f"Expense amount ({amount}) exceeds total sales ({total_sales}) for {expense_date}.",
                )

            # Start transaction
            logger.info("Starting transaction for expense save")
            conn.execute("BEGIN TRANSACTION")

            # Insert expense
            logger.info(
                f"Inserting expense: type={expense_type}, user_id={user_id}, date={expense_date}, amount={amount}"
            )
            cursor.execute(
                """
                INSERT INTO expenses (
                    expense_type, user_id, expense_date, amount, description,
                    reference_number, receipt_path, created_at, updated_at
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

            # Insert linked items if provided
            if linked_shop_item_ids:
                logger.info(f"Linking items: {linked_shop_item_ids}")
                for item_id in linked_shop_item_ids:
                    cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
                    if not cursor.fetchone():
                        raise ValueError(f"Item ID {item_id} does not exist")
                    cursor.execute(
                        "INSERT INTO expense_items (expense_id, item_id) VALUES (?, ?)",
                        (expense_id, item_id),
                    )

            # Update daily financials using the same connection
            logger.info(
                f"Calling update_daily_financials for {expense_date} with same connection"
            )
            self._update_daily_financials_with_conn(expense_date, conn)

            # Commit transaction
            logger.info("Committing transaction")
            conn.commit()
            logger.info(f"Expense saved successfully with ID: {expense_id}")
            return True, "Expense saved successfully."
        except ValueError as ve:
            logger.error(f"Validation error saving expense: {str(ve)}")
            conn.rollback()
            return False, f"Validation error: {str(ve)}"
        except sqlite3.OperationalError as oe:
            logger.error(f"Database operational error saving expense: {str(oe)}")
            conn.rollback()
            return False, f"Database operational error: {str(oe)}"
        except sqlite3.IntegrityError as ie:
            logger.error(f"Database integrity error saving expense: {str(ie)}")
            conn.rollback()
            return False, f"Database integrity error: {str(ie)}"
        except Exception as e:
            logger.error(f"Unexpected error saving expense: {str(e)}")
            conn.rollback()
            return False, f"Unexpected error: {str(e)}"
        finally:
            logger.info("Closing connection in finally block")
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
                    e.created_at, e.updated_at, u.username
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
                    "linked_item_names": "",
                }
                for row in cursor.fetchall()
            ]

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
                expense["linked_item_names"] = ", ".join(linked_items)

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
        expense_type,
        user_id,
        expense_date,
        amount,
        description,
        reference_number,
        receipt_path,
        linked_shop_item_ids,
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            logger.info(f"Starting update for expense ID {expense_id}")
            cursor.execute(
                "SELECT expense_date, amount FROM expenses WHERE id = ?",
                (expense_id,),
            )
            old_data = cursor.fetchone()
            old_date, old_amount = old_data[0], old_data[1]

            conn.execute("BEGIN TRANSACTION")

            cursor.execute(
                """
                    UPDATE expenses
                    SET
                        expense_type = ?, user_id = ?, expense_date = ?, amount = ?,
                        description = ?, reference_number = ?, receipt_path = ?,
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

            cursor.execute(
                "DELETE FROM expense_items WHERE expense_id = ?", (expense_id,)
            )
            if linked_shop_item_ids:
                for item_id in linked_shop_item_ids:
                    cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
                    if not cursor.fetchone():
                        raise ValueError(f"Item ID {item_id} does not exist")
                    cursor.execute(
                        "INSERT INTO expense_items (expense_id, item_id) VALUES (?, ?)",
                        (expense_id, item_id),
                    )

            # Update daily financials for both old and new dates if changed
            if old_date != expense_date:
                logger.info(f"Updating financials for old date {old_date}")
                self.update_daily_financials(old_date)
            logger.info(f"Updating financials for new date {expense_date}")
            self._update_daily_financials_with_conn(expense_date, conn)

            conn.commit()
            logger.info(f"Expense with ID {expense_id} updated successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating expense with ID {expense_id}: {str(e)}")
            conn.rollback()
            return False
        except ValueError as ve:
            logger.error(f"Validation error updating expense: {str(ve)}")
            conn.rollback()
            return False
        finally:
            self._commit_and_close(conn)

    def delete_expense(self, expense_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT expense_date FROM expenses WHERE id = ?", (expense_id,)
            )
            expense_date = cursor.fetchone()[0]

            conn.execute("BEGIN TRANSACTION")
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            cursor.execute(
                "DELETE FROM expense_items WHERE expense_id = ?", (expense_id,)
            )
            self._update_daily_financials_with_conn(expense_date, conn)
            conn.commit()
            logger.info(f"Expense with ID {expense_id} deleted.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting expense with ID {expense_id}: {str(e)}")
            conn.rollback()
            return False
        finally:
            self._commit_and_close(conn)

    def delete_expense(self, expense_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT expense_date FROM expenses WHERE id = ?", (expense_id,)
            )
            expense_date = cursor.fetchone()[0]

            conn.execute("BEGIN TRANSACTION")
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            cursor.execute(
                "DELETE FROM expense_items WHERE expense_id = ?", (expense_id,)
            )
            self._update_daily_financials_with_conn(expense_date, conn)
            conn.commit()
            logger.info(f"Expense with ID {expense_id} deleted.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting expense with ID {expense_id}: {str(e)}")
            conn.rollback()
            return False
        finally:
            self._commit_and_close(conn)

    def get_linked_item_ids(self, expense_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT item_id FROM expense_items WHERE expense_id = ?", (expense_id,)
            )
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(
                f"Error getting linked items for expense {expense_id}: {str(e)}"
            )
            return []
        finally:
            self._commit_and_close(conn)
