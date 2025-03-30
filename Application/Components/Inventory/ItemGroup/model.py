# model.py
import logging
import sqlite3
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ItemGroupManager:
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

    def get_item_groups(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, created_at FROM item_groups")
            item_groups = [
                {"id": row[0], "name": row[1], "created_at": row[2]}
                for row in cursor.fetchall()
            ]
            return item_groups
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve item_groups: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def save_item_group(self, name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO item_groups (name, created_at)
                VALUES (?, datetime('now'))
                """,
                (name,),
            )
            logger.info(f"Item group '{name}' saved successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving item group '{name}': {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def update_item_group(self, item_group_id, name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE item_groups
                SET name = ?
                WHERE id = ?
                """,
                (name, item_group_id),
            )
            logger.info(f"Item group with ID {item_group_id} updated successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating item group with ID {item_group_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def delete_item_group(self, item_group_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM item_groups WHERE id = ?", (item_group_id,))
            logger.info(f"Item group with ID {item_group_id} deleted successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting item group with ID {item_group_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)
