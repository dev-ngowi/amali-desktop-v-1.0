import logging
import sqlite3
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReportManager:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_connection(self):
        """Get a new database connection."""
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

    def get_stores_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, name
                FROM stores
                """
            )
            stores = [
                {
                    "id": row[0],
                    "name": row[1],
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

    def get_company_details(self):
        """Fetch company details from local database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, company_name, address, state, phone, tin_no, vrn_no FROM companies"
                )
                results = [
                    {
                        "id": row[0],
                        "company_name": row[1],
                        "address": row[2],
                        "state": row[3],
                        "phone": row[4],
                        "tin_no": row[5],
                        "vrn_no": row[6],
                    }
                    for row in cursor.fetchall()
                ]
                return results if results else []
        except sqlite3.Error as e:
            print(f"Database error getting company details: {e}")
            return []

    def get_sales_summary_data(self, start_date, end_date, store_id=None):
        """Fetch sales summary data from the orders table, grouped by date."""
        conn = self._get_connection()
        cursor = conn.cursor()
        sales_data = []
        try:
            query = """
            SELECT DATE(date),
                   SUM(total_amount),
                   SUM(discount),
                   SUM(tip),
                   SUM(ground_total)
            FROM orders
            WHERE DATE(date) BETWEEN ? AND ?
            AND status = 'completed'
            """
            params = (start_date, end_date)

            logger.info(f"Store ID type: {type(store_id)}, value: {store_id}")
            if store_id is not None:
                query += " AND store_id = ?"
                params += (store_id,)

            query += " GROUP BY DATE(date)"
            query += " ORDER BY DATE(date)"  # Optional: Order the results by date

            logger.info(f"Executing sales summary query: {query} with params: {params}")

            cursor.execute(query, params)
            rows = cursor.fetchall()
            logger.info(f"Retrieved {len(rows)} rows from the database.")
            for row in rows:
                logger.info(f"Raw row data: {row}")
                sales_data.append(
                    {
                        "date": row[0],  # Date from the grouped result
                        "sub_total": float(row[1]) if row[1] is not None else 0.00,
                        "tax_total": 0.00,  # Assuming tax is not a separate field
                        "discount": float(row[2]) if row[2] is not None else 0.00,
                        "others": 0.00,  # Assuming no 'others' field
                        "tip": float(row[3]) if row[3] is not None else 0.00,
                        "ground_total": float(row[4]) if row[4] is not None else 0.00,
                        "payment_total": float(row[4]) if row[4] is not None else 0.00,
                        "amount_due": 0.00,  # Assuming completed orders have no amount due
                    }
                )
            logger.info(
                f"Processed {len(sales_data)} daily sales summaries "
                f"between {start_date} and {end_date}."
            )
            return sales_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving sales summary data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_reports_data(self, report_date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT order_number, receipt_number, date, customer_type_id, total_amount, ground_total, status
                FROM orders WHERE date = ?
                """,
                (report_date,),
            )
            order_row = cursor.fetchone()
            if not order_row:
                return None

            return {
                "order_number": order_row[0],
                "receipt_number": order_row[1],
                "status": order_row[6],
                "date": order_row[2],
                "total_amount": float(order_row[4]),
                "ground_total": float(order_row[5]),
            }
        except sqlite3.Error as e:
            print(f"Database error getting order for sync: {e}")
            return None
        finally:
            self._commit_and_close(conn)
