import logging
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class OrderSummaryModel:
    def __init__(self):
        """Initialize the model with a DatabaseManager instance."""
        self.db_manager = DatabaseManager()
        logger.debug("OrderSummaryModel initialized")

    def get_orders_by_status(self, status=None, date=None):
        """
        Fetch orders from the database based on status and/or date.

        Args:
            status (str, optional): Filter orders by status ('completed', 'settled', 'voided', 'in-cart').
            date (str, optional): Filter orders by date in 'yyyy-MM-dd' format.

        Returns:
            list: List of order dictionaries with order details.
        """
        logger.debug(f"Fetching orders with status: {status}, date: {date}")
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                # Base query for orders
                query = """
                SELECT order_number, date, receipt_number, status, total_amount
                FROM orders
                WHERE is_active = 1
                """
                params = []
                
                # Apply date filter if provided
                if date:
                    query += " AND DATE(date) = ?"
                    params.append(date)
                    logger.debug(f"Added date filter: {date}")
                
                # Apply status filter if provided
                if status:
                    query += " AND status = ?"
                    params.append(status)
                    logger.debug(f"Added status filter: {status}")
                
                logger.debug(f"Executing query: {query} with params: {params}")
                cursor.execute(query, params)
                rows = cursor.fetchall()
                logger.debug(f"Retrieved {len(rows)} rows from database")
                
                # Process rows into a list of dictionaries
                orders = []
                for row in rows:
                    logger.debug(f"Raw row data: {row}")
                    orders.append({
                        "order_no": row[0],
                        "time": row[1],
                        "receipt_no": row[2],
                        "status": row[3],
                        "total_amount": float(row[4]) if row[4] else 0.0,
                    })
                logger.debug(f"Processed orders: {orders}")
                return orders
        except Exception as e:
            logger.error(f"Database error getting orders: {e}")
            return []

    def get_order_details(self, order_id):
        """
        Fetch detailed information for a specific order.

        Args:
            order_id (int): The ID of the order to retrieve.

        Returns:
            dict: Detailed order information or None if not found.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_number, receipt_number, date, customer_type_id, total_amount, tip, discount, ground_total, status
                    FROM orders WHERE id = ?
                    """,
                    (order_id,),
                )
                order_row = cursor.fetchone()
                if not order_row:
                    return None

                # Fetch related customer info
                cursor.execute(
                    "SELECT customer_id FROM customer_orders WHERE order_id = ?",
                    (order_id,),
                )
                customer_row = cursor.fetchone()
                customer_id = customer_row[0] if customer_row else None

                # Fetch payment info
                cursor.execute(
                    "SELECT payment_id FROM order_payments WHERE order_id = ?",
                    (order_id,),
                )
                payment_row = cursor.fetchone()
                payment_id = payment_row[0] if payment_row else None

                # Fetch order items
                cursor.execute(
                    """
                    SELECT item_id, quantity, price FROM order_items WHERE order_id = ?
                    """,
                    (order_id,),
                )
                items = [
                    {"item_id": row[0], "quantity": row[1], "price": row[2]}
                    for row in cursor.fetchall()
                ]

                return {
                    "order_number": order_row[0],
                    "receipt_number": order_row[1],
                    "date": order_row[2],
                    "customer_type_id": order_row[3],
                    "customer_id": customer_id,
                    "payment_id": payment_id,
                    "total_amount": float(order_row[4]),
                    "tip": float(order_row[5]) if order_row[5] is not None else 0,
                    "discount": float(order_row[6]) if order_row[6] is not None else 0,
                    "ground_total": float(order_row[7]),
                    "status": order_row[8],
                    "items": items,
                }
        except Exception as e:
            logger.error(f"Database error getting order details for order_id {order_id}: {e}")
            return None

    def get_order_counts(self):
        """
        Get counts of orders by status for button updates.

        Returns:
            dict: Counts of orders for each status.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT status, COUNT(*) 
                    FROM orders 
                    WHERE is_active = 1 
                    GROUP BY status
                    """
                )
                rows = cursor.fetchall()
                counts = {
                    "completed": 0,
                    "in_cart": 0,
                    "settled": 0,
                    "voided": 0,
                }
                for row in rows:
                    status = row[0].lower() if row[0] else "unknown"
                    count = row[1]
                    if status in counts:
                        counts[status] = count
                    elif status == "in-cart":  # Handle hyphenated status from carts
                        counts["in_cart"] = count
                return counts
        except Exception as e:
            logger.error(f"Database error getting order counts: {e}")
            return {
                "completed": 0,
                "in_cart": 0,
                "settled": 0,
                "voided": 0,
            }