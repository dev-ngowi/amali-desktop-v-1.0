import logging
import sqlite3
from datetime import datetime
from Helper.db_conn import DatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CustomerManager:
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
            
    def create_customer(self, customer_name, customer_type_id, city_id, phone=None, 
                       email=None, address=None, active=1):
        """Create a new customer"""
        conn = self._get_connection()
        try:
            current_time = datetime.now().isoformat()
            query = """
                INSERT INTO customers (
                    customer_name, customer_type_id, city_id, phone, email, 
                    address, active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (customer_name, customer_type_id, city_id, phone, email, 
                     address, active, current_time, current_time)
            
            cursor = conn.execute(query, values)
            customer_id = cursor.lastrowid
            self._commit_and_close(conn)
            logger.info(f"Created customer with ID: {customer_id}")
            return customer_id
        except sqlite3.Error as e:
            logger.error(f"Error creating customer: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def get_customer(self, customer_id):
        """Retrieve a specific customer by ID"""
        conn = self._get_connection()
        try:
            query = """
                SELECT c.*, ct.name as customer_type_name, ci.name as city_name
                FROM customers c
                JOIN customer_types ct ON c.customer_type_id = ct.id
                JOIN cities ci ON c.city_id = ci.id
                WHERE c.id = ?
            """
            cursor = conn.execute(query, (customer_id,))
            customer = cursor.fetchone()
            conn.close()
            return dict(customer) if customer else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving customer: {str(e)}")
            conn.close()
            raise

    def list_customers(self):
        """List all active customers"""
        conn = self._get_connection()
        try:
            query = """
                SELECT c.*, ct.name as customer_type_name, ci.name as city_name
                FROM customers c
                JOIN customer_types ct ON c.customer_type_id = ct.id
                JOIN cities ci ON c.city_id = ci.id
                WHERE c.active = 1
            """
            cursor = conn.execute(query)
            customers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return customers
        except sqlite3.Error as e:
            logger.error(f"Error listing customers: {str(e)}")
            conn.close()
            raise

    def update_customer(self, customer_id, **kwargs):
        """Update customer details"""
        conn = self._get_connection()
        try:
            allowed_fields = {'customer_name', 'customer_type_id', 'city_id', 
                            'phone', 'email', 'address', 'active'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                conn.close()
                return False
                
            update_fields['updated_at'] = datetime.now().isoformat()
            set_clause = ', '.join(f"{k} = ?" for k in update_fields.keys())
            values = list(update_fields.values()) + [customer_id]
            
            query = f"UPDATE customers SET {set_clause} WHERE id = ?"
            cursor = conn.execute(query, values)
            
            if cursor.rowcount > 0:
                self._commit_and_close(conn)
                logger.info(f"Updated customer with ID: {customer_id}")
                return True
            self._rollback_and_close(conn)
            return False
        except sqlite3.Error as e:
            logger.error(f"Error updating customer: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def delete_customer(self, customer_id):
        """Soft delete a customer by setting active to 0"""
        conn = self._get_connection()
        try:
            query = "UPDATE customers SET active = 0, updated_at = ? WHERE id = ?"
            current_time = datetime.now().isoformat()
            cursor = conn.execute(query, (current_time, customer_id))
            
            if cursor.rowcount > 0:
                self._commit_and_close(conn)
                logger.info(f"Deleted customer with ID: {customer_id}")
                return True
            self._rollback_and_close(conn)
            return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting customer: {str(e)}")
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

    def get_customer_types(self): 
        """List all active customer types"""
        conn = self._get_connection()
        try:
            query = "SELECT * FROM customer_types WHERE is_active = 1"
            cursor = conn.execute(query)
            customer_types = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return customer_types
        except sqlite3.Error as e:
            logger.error(f"Error retrieving customer types: {str(e)}")
            conn.close()
            raise