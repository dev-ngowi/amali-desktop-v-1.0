# modal.py
import logging
import sqlite3
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CategoryManager:
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
            cursor.execute("SELECT id, name FROM item_groups")
            item_groups = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
            return item_groups
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve item_groups: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def save_categories(self, name, item_group_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO categories (name, item_group_id, created_at, updated_at)
                VALUES (?, ?, datetime('now'), datetime('now'))
                """,
                (name, item_group_id),
            )
            logger.info(f"Category '{name}' saved successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving category '{name}': {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def get_categories_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT 
                    c.id,
                    c.name,
                    ig.name as item_group_id,
                    c.created_at,
                    c.updated_at 
                FROM categories c
                JOIN item_groups ig ON c.item_group_id = ig.id
                """
            )
            categories = [
                {
                    "id": row[0],
                    "name": row[1],
                    "item_group_id": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                }
                for row in cursor.fetchall()
            ]
            logger.info(f"Retrieved {len(categories)} categories.")
            return categories
        except sqlite3.Error as e:
            logger.error(f"Error retrieving categories data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def update_categories(self, category_id, name, item_group_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE categories 
                SET name = ?, item_group_id = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (name, item_group_id, category_id),
            )
            logger.info(f"Category with ID {category_id} updated successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating category with ID {category_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def delete_categories(self, category_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            logger.info(f"Category with ID {category_id} deleted successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting category with ID {category_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)