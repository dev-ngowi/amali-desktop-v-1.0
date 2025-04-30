# modal.py
import logging
import sqlite3
from datetime import date, timedelta
from Helper.db_conn import DatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DayCloseManager:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_connection(self):
        with self.db_manager.lock:
            conn = sqlite3.connect(self.db_manager.db_path, timeout=30)
            conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _commit_and_close(self, conn):
        try:
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error committing changes: {str(e)}")
        finally:
            conn.close()

    def get_stores_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name FROM stores")
            stores = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

            if not stores:
                logger.warning("No stores found. Inserting default store.")
                # Check if admin user exists first
                cursor.execute("SELECT id FROM users WHERE username = 'admin'")
                admin = cursor.fetchone()
                if not admin:
                    hashed_password = (
                        "$2y$12$BlLtxbg53w4RNZmkwRq7T.R/6NMzKD0maVtGpMe1aeVBcCjghcckG"
                    )
                    cursor.execute(
                        """
                        INSERT INTO users (id, fullname, username, password, pin, created_at, updated_at)
                        VALUES (1, 'Administrator', 'admin', ?, 1234, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (hashed_password,),
                    )

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO stores (id, name, location, manager_id, created_at, updated_at)
                    VALUES (1, 'Mohalal Shop', 'Forest', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                )
                conn.commit()
                cursor.execute("SELECT id, name FROM stores")
                stores = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

            logger.info(f"Retrieved {len(stores)} stores: {stores}")
            return stores
        except sqlite3.Error as e:
            logger.error(f"Error retrieving stores data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    # Rest of the methods remain unchanged
    def get_orders_status(self, working_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(*) FROM orders
                WHERE DATE(date) = ? AND status = 'settled'
                """,
                (working_date.strftime("%Y-%m-%d"),),
            )
            completed_orders_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT SUM(ground_total) FROM orders
                WHERE DATE(date) = ? AND status = 'settled'
                """,
                (working_date.strftime("%Y-%m-%d"),),
            )
            total_amount = cursor.fetchone()[0] or 0.0

            cursor.execute(
                """
                SELECT COUNT(*) FROM orders
                WHERE DATE(date) = ? AND status = 'voided'
                """,
                (working_date.strftime("%Y-%m-%d"),),
            )
            voided_orders_count = cursor.fetchone()[0]

            return completed_orders_count, total_amount, voided_orders_count
        except sqlite3.Error as e:
            logger.error(f"Error getting orders status: {str(e)}")
            return 0, 0.0, 0
        finally:
            self._commit_and_close(conn)

    def check_day_close_exists(self, store_id, working_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(*) FROM day_close
                WHERE store_id = ? AND working_date = ?
                """,
                (store_id, working_date.strftime("%Y-%m-%d")),
            )
            count = cursor.fetchone()[0]
            return count > 0
        except sqlite3.Error as e:
            logger.error(f"Error checking day close: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def perform_day_close(self, store_id, working_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            next_working_date = working_date + timedelta(days=1)
            completed_orders, total_amount, voided_orders = self.get_orders_status(
                working_date
            )

            cursor.execute(
                """
                INSERT INTO day_close (store_id, working_date, next_working_date, running_orders, total_amount, voided_orders)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    store_id,
                    working_date.strftime("%Y-%m-%d"),
                    next_working_date.strftime("%Y-%m-%d"),
                    completed_orders,
                    total_amount,
                    voided_orders,
                ),
            )
            logger.info(f"Day close performed for store {store_id} on {working_date}")
            self._commit_and_close(conn)
            return True
        except sqlite3.Error as e:
            logger.error(f"Error performing day close: {str(e)}")
            self._commit_and_close(conn)
            return False

    def save_day_close_data(
        self,
        store_id,
        working_date,
        next_working_date,
        running_orders=0,
        total_amount=0.0,
        voided_orders=0,
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO day_close (store_id, working_date, next_working_date, running_orders, total_amount, voided_orders)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    store_id,
                    working_date,
                    next_working_date,
                    running_orders,
                    total_amount,
                    voided_orders,
                ),
            )
            logger.info("Day close data saved successfully.")
            self._commit_and_close(conn)
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving day close data: {str(e)}")
            self._commit_and_close(conn)
            return False 
    def is_operational(self):
        """Check if the application can operate based on the latest day close."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT next_working_date 
                FROM day_close 
                ORDER BY working_date DESC 
                LIMIT 1
                """
            )
            result = cursor.fetchone()
            if result:
                next_working_date = date.fromisoformat(result[0])
                current_date = date.today()
                if current_date < next_working_date:
                    logger.info(f"Application locked until {next_working_date}")
                    return False, f"Application is locked until {next_working_date}. No actions allowed."
            return True, "Application is operational."
        except sqlite3.Error as e:
            logger.error(f"Error checking operational status: {str(e)}")
            return False, f"Database error: {str(e)}"
        finally:
            self._commit_and_close(conn)