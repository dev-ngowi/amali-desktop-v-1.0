# modal.py
import logging
import sqlite3
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PaymentsManager:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_connection(self):
        """Get a new database connection."""
        # Use the lock directly from DatabaseManager to ensure thread safety
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

    def get_payment_types(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, name
                FROM payment_types
                """
            )
            payment_types = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(payment_types)} payment types.")
            return payment_types
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve payment types: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_payment_type(self, payment_type_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, name
                FROM payment_types
                WHERE id = ?
                """,
                (payment_type_id,),
            )
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1]}
            return None
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve payment type with ID {payment_type_id}: {str(e)}")
            return None
        finally:
            self._commit_and_close(conn)

    def save_payment(self, short_code, payment_method, payment_type_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO payments (short_code, payment_method, payment_type_id, created_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (short_code, payment_method, payment_type_id),
            )
            logger.info(f"Payment with short code '{short_code}' saved successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving payment with short code '{short_code}': {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def get_payments_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, short_code, payment_method, payment_type_id, created_at
                FROM payments
                """
            )
            payments = [
                {
                    "id": row[0],
                    "short_code": row[1],
                    "payment_method": row[2],
                    "payment_type_id": row[3],
                    "created_at": row[4],
                }
                for row in cursor.fetchall()
            ]
            logger.info(f"Retrieved {len(payments)} payments.")
            return payments
        except sqlite3.Error as e:
            logger.error(f"Error retrieving payments data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def update_payment(self, payment_id, short_code=None, payment_method=None, payment_type_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT short_code, payment_method, payment_type_id FROM payments WHERE id = ?",
                (payment_id,),
            )
            current = cursor.fetchone()
            if not current:
                logger.warning(f"Payment with ID {payment_id} not found for update.")
                raise Exception("Payment not found")

            new_short_code = short_code if short_code is not None else current[0]
            new_payment_method = payment_method if payment_method is not None else current[1]
            new_payment_type_id = payment_type_id if payment_type_id is not None else current[2]

            cursor.execute(
                """
                UPDATE payments
                SET short_code = ?, payment_method = ?, payment_type_id = ?
                WHERE id = ?
                """,
                (new_short_code, new_payment_method, new_payment_type_id, payment_id),
            )
            logger.info(f"Payment with ID {payment_id} updated successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating payment with ID {payment_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def delete_payment(self, payment_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM payments WHERE id = ?", (payment_id,))
            if not cursor.fetchone():
                logger.warning(f"Payment with ID {payment_id} not found for deletion.")
                raise Exception("Payment not found")
            cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
            logger.info(f"Payment with ID {payment_id} deleted successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting payment with ID {payment_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)