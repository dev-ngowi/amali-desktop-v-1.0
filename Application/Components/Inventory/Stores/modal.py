# modal.py
import logging
import sqlite3
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StoreManager:
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
                logger.info(f"Successfully retrieved {len(users)} users.")
            return users
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve users: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def save_stores(self, name, location, manager_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO stores (name, location, manager_id, created_at, updated_at)
                VALUES (?, ?, ?, datetime('now'), datetime('now'))
                """,
                (name, location, manager_id),
            )
            logger.info(f"Store '{name}' saved successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving store '{name}': {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def get_stores_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, name, location, manager_id, created_at, updated_at 
                FROM stores
                """
            )
            stores = [
                {
                    "id": row[0],
                    "name": row[1],
                    "location": row[2],
                    "manager_id": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                }
                for row in cursor.fetchall()
            ]
            logger.info(f"Retrieved {len(stores)} stores.")
            return stores
        except sqlite3.Error as e:
            logger.error(f"Error retrieving stores data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def update_stores(self, store_id, name=None, location=None, manager_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT name, location, manager_id FROM stores WHERE id = ?",
                (store_id,),
            )
            current = cursor.fetchone()
            if not current:
                logger.warning(f"Store with ID {store_id} not found for update.")
                raise Exception("Store not found")
            new_name = name if name is not None else current[0]
            new_location = location if location is not None else current[1]
            new_manager_id = manager_id if manager_id is not None else current[2]
            cursor.execute(
                """
                UPDATE stores 
                SET name = ?, location = ?, manager_id = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (new_name, new_location, new_manager_id, store_id),
            )
            logger.info(f"Store with ID {store_id} updated successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating store with ID {store_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def delete_stores(self, store_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM stores WHERE id = ?", (store_id,))
            if not cursor.fetchone():
                logger.warning(f"Store with ID {store_id} not found for deletion.")
                raise Exception("Store not found")
            cursor.execute("DELETE FROM stores WHERE id = ?", (store_id,))
            logger.info(f"Store with ID {store_id} deleted successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting store with ID {store_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)
