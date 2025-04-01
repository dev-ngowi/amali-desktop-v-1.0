import logging
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CartModel:
    def __init__(self):
        """Initialize the CartModel with a DatabaseManager instance."""
        self.db_manager = DatabaseManager()
        logger.debug("CartModel initialized")

    # CREATE
    def create_cart(self, cart_data):
        """
        Create a new cart in the database.

        Args:
            cart_data (dict): Dictionary containing cart information with keys:
                - order_number (str)
                - customer_type_id (int)
                - customer_id (int, optional)
                - total_amount (float)
                - date (str, in 'yyyy-MM-dd HH:MM:SS' format)
                - items (list of dicts with item_id, name, unit, quantity, amount)
                - status (str, optional, defaults to 'in-cart')

        Returns:
            dict: Result with success status, message, and cart_id if successful.
        """
        try:
            # Validate required fields
            required_fields = ["order_number", "customer_type_id", "total_amount", "date", "items"]
            for field in required_fields:
                if field not in cart_data or cart_data[field] is None:
                    raise ValueError(f"Missing or None required field: {field}")

            if not isinstance(cart_data["items"], list) or not cart_data["items"]:
                raise ValueError("Items must be a non-empty list")

            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                conn.execute("BEGIN TRANSACTION")

                # Check if order_number is unique
                cursor.execute(
                    "SELECT id FROM carts WHERE order_number = ?",
                    (cart_data["order_number"],),
                )
                if cursor.fetchone():
                    raise ValueError(f"Order number {cart_data['order_number']} already exists")

                # Validate customer_type_id
                cursor.execute(
                    "SELECT id FROM customer_types WHERE id = ?",
                    (cart_data["customer_type_id"],),
                )
                if not cursor.fetchone():
                    raise ValueError(f"Customer type ID {cart_data['customer_type_id']} does not exist")

                # Validate customer_id if provided
                customer_id = cart_data.get("customer_id")
                if customer_id:
                    cursor.execute(
                        "SELECT id FROM customers WHERE id = ?",
                        (customer_id,),
                    )
                    if not cursor.fetchone():
                        raise ValueError(f"Customer ID {customer_id} does not exist")

                # Insert cart
                cursor.execute(
                    """
                    INSERT INTO carts (order_number, customer_type_id, customer_id, total_amount, date, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cart_data["order_number"],
                        cart_data["customer_type_id"],
                        customer_id,
                        float(cart_data["total_amount"]),
                        cart_data["date"],
                        cart_data.get("status", "in-cart"),
                    ),
                )
                cart_id = cursor.lastrowid

                # Insert cart items
                for item in cart_data["items"]:
                    required_item_fields = ["item_id", "name", "unit", "quantity", "amount"]
                    for field in required_item_fields:
                        if field not in item or item[field] is None:
                            raise ValueError(f"Missing or None required item field: {field}")

                    # Validate item_id
                    cursor.execute(
                        "SELECT id FROM items WHERE id = ?",
                        (item["item_id"],),
                    )
                    if not cursor.fetchone():
                        raise ValueError(f"Item ID {item['item_id']} does not exist")

                    cursor.execute(
                        """
                        INSERT INTO cart_items (cart_id, item_id, name, unit, quantity, amount)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cart_id,
                            item["item_id"],
                            item["name"],
                            item["unit"],
                            int(item["quantity"]),
                            float(item["amount"]),
                        ),
                    )

                conn.commit()
                logger.debug(f"Cart created with ID: {cart_id}")
                return {
                    "success": True,
                    "message": "Cart created successfully",
                    "cart_id": cart_id,
                }

        except ValueError as e:
            if "conn" in locals():
                conn.rollback()
            logger.error(f"Validation error: {str(e)}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            if "conn" in locals():
                conn.rollback()
            logger.error(f"Database error creating cart: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}

    # READ
    def get_cart(self, cart_id):
        """
        Retrieve a cart and its items by cart ID.

        Args:
            cart_id (int): The ID of the cart to retrieve.

        Returns:
            dict: Cart details including items, or None if not found.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_number, customer_type_id, customer_id, total_amount, status, date
                    FROM carts WHERE id = ?
                    """,
                    (cart_id,),
                )
                cart_row = cursor.fetchone()
                if not cart_row:
                    return None

                cursor.execute(
                    """
                    SELECT item_id, name, unit, quantity, amount
                    FROM cart_items WHERE cart_id = ?
                    """,
                    (cart_id,),
                )
                items = [
                    {
                        "item_id": row[0],
                        "name": row[1],
                        "unit": row[2],
                        "quantity": row[3],
                        "amount": float(row[4]),
                    }
                    for row in cursor.fetchall()
                ]

                cart = {
                    "cart_id": cart_id,
                    "order_number": cart_row[0],
                    "customer_type_id": cart_row[1],
                    "customer_id": cart_row[2],
                    "total_amount": float(cart_row[3]),
                    "status": cart_row[4],
                    "date": cart_row[5],
                    "items": items,
                }
                logger.debug(f"Retrieved cart: {cart}")
                return cart

        except Exception as e:
            logger.error(f"Database error retrieving cart {cart_id}: {str(e)}")
            return None

    def get_carts_by_status(self, status=None, date=None):
        """
        Retrieve carts filtered by status and/or date.

        Args:
            status (str, optional): Filter by status ('in-cart', 'settled', 'voided').
            date (str, optional): Filter by date in 'yyyy-MM-dd' format.

        Returns:
            list: List of cart dictionaries.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                SELECT id, order_number, customer_type_id, customer_id, total_amount, status, date
                FROM carts
                """
                params = []
                conditions = []

                if status:
                    conditions.append("status = ?")
                    params.append(status)
                if date:
                    conditions.append("DATE(date) = ?")
                    params.append(date)

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                cursor.execute(query, params)
                rows = cursor.fetchall()
                carts = [
                    {
                        "cart_id": row[0],
                        "order_number": row[1],
                        "customer_type_id": row[2],
                        "customer_id": row[3],
                        "total_amount": float(row[4]),
                        "status": row[5],
                        "date": row[6],
                    }
                    for row in rows
                ]
                logger.debug(f"Retrieved {len(carts)} carts with status {status} and date {date}")
                return carts

        except Exception as e:
            logger.error(f"Database error retrieving carts: {str(e)}")
            return []

    # UPDATE
    def update_cart(self, cart_id, cart_data):
        """
        Update an existing cart and its items.

        Args:
            cart_id (int): The ID of the cart to update.
            cart_data (dict): Dictionary with fields to update (same as create_cart).

        Returns:
            dict: Result with success status and message.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                conn.execute("BEGIN TRANSACTION")

                # Check if cart exists
                cursor.execute("SELECT id FROM carts WHERE id = ?", (cart_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Cart ID {cart_id} does not exist")

                # Prepare update fields
                update_fields = []
                params = []
                if "order_number" in cart_data and cart_data["order_number"]:
                    update_fields.append("order_number = ?")
                    params.append(cart_data["order_number"])
                if "customer_type_id" in cart_data and cart_data["customer_type_id"] is not None:
                    cursor.execute("SELECT id FROM customer_types WHERE id = ?", (cart_data["customer_type_id"],))
                    if not cursor.fetchone():
                        raise ValueError(f"Customer type ID {cart_data['customer_type_id']} does not exist")
                    update_fields.append("customer_type_id = ?")
                    params.append(cart_data["customer_type_id"])
                if "customer_id" in cart_data:
                    if cart_data["customer_id"] is not None:
                        cursor.execute("SELECT id FROM customers WHERE id = ?", (cart_data["customer_id"],))
                        if not cursor.fetchone():
                            raise ValueError(f"Customer ID {cart_data['customer_id']} does not exist")
                    update_fields.append("customer_id = ?")
                    params.append(cart_data["customer_id"])
                if "total_amount" in cart_data and cart_data["total_amount"] is not None:
                    update_fields.append("total_amount = ?")
                    params.append(float(cart_data["total_amount"]))
                if "status" in cart_data and cart_data["status"]:
                    if cart_data["status"] not in ("in-cart", "settled", "voided"):
                        raise ValueError(f"Invalid status: {cart_data['status']}")
                    update_fields.append("status = ?")
                    params.append(cart_data["status"])
                if "date" in cart_data and cart_data["date"]:
                    update_fields.append("date = ?")
                    params.append(cart_data["date"])

                if update_fields:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(cart_id)
                    query = f"UPDATE carts SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(query, params)

                # Update cart items if provided
                if "items" in cart_data and cart_data["items"]:
                    # Delete existing items
                    cursor.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))
                    # Insert new items
                    for item in cart_data["items"]:
                        required_item_fields = ["item_id", "name", "unit", "quantity", "amount"]
                        for field in required_item_fields:
                            if field not in item or item[field] is None:
                                raise ValueError(f"Missing or None required item field: {field}")

                        cursor.execute(
                            "SELECT id FROM items WHERE id = ?",
                            (item["item_id"],),
                        )
                        if not cursor.fetchone():
                            raise ValueError(f"Item ID {item['item_id']} does not exist")

                        cursor.execute(
                            """
                            INSERT INTO cart_items (cart_id, item_id, name, unit, quantity, amount)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                cart_id,
                                item["item_id"],
                                item["name"],
                                item["unit"],
                                int(item["quantity"]),
                                float(item["amount"]),
                            ),
                        )

                conn.commit()
                logger.debug(f"Cart {cart_id} updated successfully")
                return {"success": True, "message": "Cart updated successfully"}

        except ValueError as e:
            if "conn" in locals():
                conn.rollback()
            logger.error(f"Validation error updating cart {cart_id}: {str(e)}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            if "conn" in locals():
                conn.rollback()
            logger.error(f"Database error updating cart {cart_id}: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}

    # DELETE
    def delete_cart(self, cart_id):
        """
        Delete a cart and its associated items.

        Args:
            cart_id (int): The ID of the cart to delete.

        Returns:
            dict: Result with success status and message.
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                conn.execute("BEGIN TRANSACTION")

                # Check if cart exists
                cursor.execute("SELECT id FROM carts WHERE id = ?", (cart_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Cart ID {cart_id} does not exist")

                # Delete cart items
                cursor.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))
                # Delete cart
                cursor.execute("DELETE FROM carts WHERE id = ?", (cart_id,))

                conn.commit()
                logger.debug(f"Cart {cart_id} deleted successfully")
                return {"success": True, "message": "Cart deleted successfully"}

        except ValueError as e:
            if "conn" in locals():
                conn.rollback()
            logger.error(f"Validation error deleting cart {cart_id}: {str(e)}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            if "conn" in locals():
                conn.rollback()
            logger.error(f"Database error deleting cart {cart_id}: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
