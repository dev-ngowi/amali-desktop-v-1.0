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
            status (str, optional): Filter orders by status ('completed', 'settled', 'voided').
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

                # Apply status filter if provided (special handling for 'completed')
                if status:
                    if status == "completed":
                        # Include both 'completed' and 'voided' under 'completed' filter
                        query += " AND status IN ('completed', 'voided')"
                    else:
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
                    orders.append(
                        {
                            "order_no": row[0],
                            "date": row[
                                1
                            ],  # Changed 'time' to 'date' to match DB schema
                            "receipt_no": row[2],
                            "status": row[3],
                            "total_amount": float(row[4]) if row[4] else 0.0,
                        }
                    )
                logger.debug(f"Processed orders: {orders}")
                return orders
        except Exception as e:
            logger.error(f"Database error getting orders: {e}", exc_info=True)
            return []

    def get_order_details(self, order_number):
        """
        Fetch detailed information for a specific order by order_number.

        Args:
            order_number (str): The order number of the order to retrieve.

        Returns:
            dict: Detailed order information or None if not found.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                # Fetch order details
                cursor.execute(
                    """
                    SELECT id, order_number, receipt_number, date, customer_type_id, total_amount, tip, discount, ground_total, status
                    FROM orders 
                    WHERE order_number = ?
                    """,
                    (order_number,),
                )
                order_row = cursor.fetchone()
                if not order_row:
                    logger.warning(f"No order found with order_number: {order_number}")
                    return None

                # Fetch related customer info
                cursor.execute(
                    """
                    SELECT customer_id 
                    FROM customer_orders 
                    WHERE order_id = ?
                    """,
                    (order_row[0],),
                )
                customer_row = cursor.fetchone()
                customer_id = customer_row[0] if customer_row else None

                # Fetch payment info (corrected query)
                cursor.execute(
                    """
                    SELECT p.short_code 
                    FROM order_payments op 
                    JOIN payments p ON op.payment_id = p.id 
                    WHERE op.order_id = ?
                    """,
                    (order_row[0],),
                )
                payment_row = cursor.fetchone()
                payment_method = payment_row[0] if payment_row else "N/A"

                # Fetch order items with item names
                cursor.execute(
                    """
                    SELECT oi.item_id, i.name, oi.quantity, oi.price 
                    FROM order_items oi
                    JOIN items i ON oi.item_id = i.id
                    WHERE oi.order_id = ?
                    """,
                    (order_row[0],),
                )
                items = [
                    {
                        "item_id": row[0],
                        "name": row[1],
                        "quantity": row[2],
                        "price": float(row[3]),
                    }
                    for row in cursor.fetchall()
                ]

                order_details = {
                    "order_id": order_row[0],
                    "order_number": order_row[1],
                    "receipt_number": order_row[2],
                    "date": order_row[3],
                    "customer_type_id": order_row[4],
                    "customer_id": customer_id,
                    "payment_method": payment_method,
                    "total_amount": float(order_row[5]),
                    "tip": float(order_row[6]) if order_row[6] is not None else 0.0,
                    "discount": (
                        float(order_row[7]) if order_row[7] is not None else 0.0
                    ),
                    "ground_total": (
                        float(order_row[8])
                        if order_row[8] is not None
                        else float(order_row[5])
                    ),
                    "status": order_row[9],
                    "items": items,
                }
                logger.debug(f"Order details fetched: {order_details}")
                return order_details
        except Exception as e:
            logger.error(
                f"Database error getting order details for order_number {order_number}: {e}",
                exc_info=True,
            )
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
                    "settled": 0,
                    "voided": 0,
                }
                for row in rows:
                    status = row[0].lower() if row[0] else "unknown"
                    count = row[1]
                    if status == "completed":
                        counts["completed"] += count
                    elif status == "settled":
                        counts["settled"] = count
                    elif status == "voided":
                        counts["voided"] = count
                # 'completed' filter shows both completed and voided
                counts["completed"] += counts["voided"]
                logger.debug(f"Order counts: {counts}")
                return counts
        except Exception as e:
            logger.error(f"Database error getting order counts: {e}", exc_info=True)
            return {"completed": 0, "settled": 0, "voided": 0}
