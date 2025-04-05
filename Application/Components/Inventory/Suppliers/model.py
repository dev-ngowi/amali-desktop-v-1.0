import logging
import sqlite3
from datetime import datetime
from Helper.db_conn import DatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SupplierManager:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_connection(self):
        """Get database connection with thread safety"""
        with self.db_manager.lock:
            conn = sqlite3.connect(self.db_manager.db_path, timeout=30)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            return conn

    def _commit_and_close(self, conn):
        """Commit changes and close connection"""
        try:
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error committing changes: {str(e)}")
            raise
        finally:
            conn.close()

    def _rollback_and_close(self, conn):
        """Rollback changes and close connection"""
        try:
            conn.rollback()
        except sqlite3.Error as e:
            logger.error(f"Error rolling back changes: {str(e)}")
        finally:
            conn.close()

    def create_supplier(
        self,
        name,
        email,
        phone,
        address,
        city_id,
        state,
        country_id,
        contact_person=None,
        tin=None,
        vrn=None,
        postal_code=None,
        status="active",
    ):
        """Create a new supplier"""
        conn = self._get_connection()
        try:
            current_time = datetime.now().isoformat()
            query = """
                INSERT INTO vendors (
                    name, email, phone, address, city_id, state, country_id, contact_person,
                    tin, vrn, postal_code, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
                name,
                email,
                phone,
                address,
                city_id,
                state,
                country_id,
                contact_person,
                tin,
                vrn,
                postal_code,
                status,
                current_time,
                current_time,
            )

            cursor = conn.execute(query, values)
            supplier_id = cursor.lastrowid
            self._commit_and_close(conn)
            logger.info(f"Created supplier with ID: {supplier_id}")
            return supplier_id
        except sqlite3.Error as e:
            logger.error(f"Error creating supplier: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def get_supplier(self, supplier_id):
        """Retrieve a specific supplier by ID"""
        conn = self._get_connection()
        try:
            query = """
                SELECT v.*, ci.name as city_name, co.name as country_name
                FROM vendors v
                JOIN cities ci ON v.city_id = ci.id
                JOIN countries co ON v.country_id = co.id
                WHERE v.id = ?
            """
            cursor = conn.execute(query, (supplier_id,))
            supplier = cursor.fetchone()
            conn.close()
            return dict(supplier) if supplier else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving supplier: {str(e)}")
            conn.close()
            raise

    def list_suppliers(self):
        """List all active suppliers"""
        conn = self._get_connection()
        try:
            query = """
                SELECT v.*, ci.name as city_name, co.name as country_name
                FROM vendors v
                JOIN cities ci ON v.city_id = ci.id
                JOIN countries co ON v.country_id = co.id
                WHERE v.status = 'active'
            """
            cursor = conn.execute(query)
            suppliers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return suppliers
        except sqlite3.Error as e:
            logger.error(f"Error listing suppliers: {str(e)}")
            conn.close()
            raise

    def update_supplier(self, supplier_id, **kwargs):
        """Update supplier details"""
        conn = self._get_connection()
        try:
            allowed_fields = {
                "name",
                "email",
                "phone",
                "address",
                "city_id",
                "state",
                "country_id",
                "contact_person",
                "tin",
                "vrn",
                "postal_code",
                "status",
            }
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not update_fields:
                conn.close()
                return False

            update_fields["updated_at"] = datetime.now().isoformat()
            set_clause = ", ".join(f"{k} = ?" for k in update_fields.keys())
            values = list(update_fields.values()) + [supplier_id]

            query = f"UPDATE vendors SET {set_clause} WHERE id = ?"
            cursor = conn.execute(query, values)

            if cursor.rowcount > 0:
                self._commit_and_close(conn)
                logger.info(f"Updated supplier with ID: {supplier_id}")
                return True
            self._rollback_and_close(conn)
            return False
        except sqlite3.Error as e:
            logger.error(f"Error updating supplier: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def delete_supplier(self, supplier_id):
        """Soft delete a supplier by setting status to 'inactive'"""
        conn = self._get_connection()
        try:
            query = (
                "UPDATE vendors SET status = 'inactive', updated_at = ? WHERE id = ?"
            )
            current_time = datetime.now().isoformat()
            cursor = conn.execute(query, (current_time, supplier_id))

            if cursor.rowcount > 0:
                self._commit_and_close(conn)
                logger.info(f"Deleted supplier with ID: {supplier_id}")
                return True
            self._rollback_and_close(conn)
            return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting supplier: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def get_cities(self):
        """List all cities"""
        conn = self._get_connection()
        try:
            query = "SELECT * FROM cities WHERE deleted_at IS NULL"
            cursor = conn.execute(query)
            cities = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return cities
        except sqlite3.Error as e:
            logger.error(f"Error retrieving cities: {str(e)}")
            conn.close()
            raise

    def get_countries(self):
        """List all countries"""
        conn = self._get_connection()
        try:
            query = "SELECT * FROM countries"
            cursor = conn.execute(query)
            countries = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return countries
        except sqlite3.Error as e:
            logger.error(f"Error retrieving countries: {str(e)}")
            conn.close()
            raise
