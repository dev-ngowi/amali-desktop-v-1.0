# model.py
import logging
import sqlite3
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class UnitManager:
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

    def get_units(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, created_at FROM units")
            units = [{"id": row[0], "name": row[1], "created_at": row[2]} for row in cursor.fetchall()]
            return units
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve units: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def save_unit(self, name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO units (name, created_at)
                VALUES (?, datetime('now'))
                """,
                (name,),
            )
            logger.info(f"Unit '{name}' saved successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving unit '{name}': {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def update_unit(self, unit_id, name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE units
                SET name = ?
                WHERE id = ?
                """,
                (name, unit_id),
            )
            logger.info(f"Unit with ID {unit_id} updated successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating unit with ID {unit_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)

    def delete_unit(self, unit_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM units WHERE id = ?", (unit_id,))
            logger.info(f"Unit with ID {unit_id} deleted successfully.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting unit with ID {unit_id}: {str(e)}")
            return False
        finally:
            self._commit_and_close(conn)