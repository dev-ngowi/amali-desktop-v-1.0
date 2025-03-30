# model.py
import logging
import sqlite3
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ItemTypeManager:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_connection(self):
        with self.db_manager.lock:
            conn = sqlite3.connect(self.db_manager.db_path, timeout=30)
        return conn

    def _commit_and_close(self, conn):
        try:
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error committing changes: {str(e)}")
        finally:
            conn.close()

    def get_item_types(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, created_at FROM item_types")
            item_types = [{"id": row[0], "name": row[1], "created_at": row[2]} for row in cursor.fetchall()]
            return item_types
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve item types: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def save_item_type(self, name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO item_types (name, created_at)
                VALUES (?, datetime('now'))
                """,
                (name,),
            )
            logger.info(f"Item type '{name}' saved successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving item type '{name}': {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def update_item_type(self, item_type_id, name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE item_types
                SET name = ?
                WHERE id = ?
                """,
                (name, item_type_id),
            )
            logger.info(f"Item type with ID {item_type_id} updated successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating item type with ID {item_type_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def delete_item_type(self, item_type_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM item_types WHERE id = ?", (item_type_id,))
            logger.info(f"Item type with ID {item_type_id} deleted successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting item type with ID {item_type_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)