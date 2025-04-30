# sales_detailed_model.py
import logging
import sqlite3
from Application.Components.Reports.modal import ReportManager
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SalesDetailedModel(ReportManager):
    def get_sales_detailed_data(self, start_date, end_date, store_id=None):
        """Fetch detailed sales data including order items from the orders and order_items tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        sales_data = []
        try:
            query = """
            SELECT o.order_number, o.date, o.discount, o.ground_total,
                   i.name AS item_name, oi.quantity, oi.price
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN items i ON oi.item_id = i.id
            WHERE DATE(o.date) BETWEEN ? AND ?
            AND o.status = 'completed'
            """
            params = (start_date, end_date)

            if store_id is not None:
                query += " AND o.store_id = ?"
                params += (store_id,)

            query += " ORDER BY o.date, o.order_number"

            logger.info(f"Executing sales detailed query: {query} with params: {params}")
            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Group items by order
            orders_dict = {}
            for row in rows:
                order_number = row[0]
                if order_number not in orders_dict:
                    orders_dict[order_number] = {
                        "order_number": order_number,
                        "date": row[1],
                        "discount": float(row[2]) if row[2] is not None else 0.00,
                        "ground_total": float(row[3]) if row[3] is not None else 0.00,
                        "items": []
                    }
                if row[4]:  # Check if item_name exists (not NULL)
                    orders_dict[order_number]["items"].append({
                        "item_name": row[4],
                        "quantity": row[5],
                        "price": float(row[6]),
                        "total": float(row[5] * row[6])
                    })

            sales_data = list(orders_dict.values())
            logger.info(
                f"Processed {len(sales_data)} detailed sales records "
                f"between {start_date} and {end_date}."
            )
            return sales_data

        except sqlite3.Error as e:
            logger.error(f"Error retrieving sales detailed data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)