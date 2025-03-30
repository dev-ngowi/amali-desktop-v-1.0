import sqlite3
from datetime import datetime
import time
from Helper.db_conn import db  # Import the db instance from db_conn.py

# No need to redefine DatabaseManager or instantiate db here


def get_local_item_groups():
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM item_groups")
            return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error getting item groups: {e}")
        return []


def get_local_categories_for_group(group_name):
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM item_groups WHERE name = ?", (group_name,))
            group_data = cursor.fetchone()
            if not group_data:
                return []
            group_id = group_data[0]
            cursor.execute(
                "SELECT id, name FROM categories WHERE item_group_id = ? AND deleted_at IS NULL",
                (group_id,),
            )
            return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error getting categories for group: {e}")
        return []


def get_local_items_for_category(category_id):
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    i.id,
                    i.name as item_name,
                    u.name as item_unit,
                    ip.amount as item_price,
                    s.min_quantity as stock_quantity,
                    COALESCE(im.file_path, 'default.jpg') as image_url
                FROM items i
                LEFT JOIN item_units iu ON i.id = iu.item_id
                LEFT JOIN units u ON iu.selling_unit_id = u.id
                LEFT JOIN item_prices ip ON i.id = ip.item_id
                LEFT JOIN stocks s ON i.id = s.item_id
                LEFT JOIN item_images ii ON i.id = ii.item_id
                LEFT JOIN images im ON ii.image_id = im.id
                WHERE i.category_id = ? AND i.status = 'active'
                """,
                (category_id,),
            )
            return [
                {
                    "item_id": row[0],
                    "item_name": row[1],
                    "item_unit": row[2] if row[2] else "pcs",
                    "item_price": float(row[3]) if row[3] is not None else 0.0,
                    "stock_quantity": float(row[4]) if row[4] is not None else 0.0,
                    "image_url": f"/uploads/item_images/{row[5]}",
                }
                for row in cursor.fetchall()
            ]
    except sqlite3.Error as e:
        print(f"Database error getting items for category: {e}")
        return []


def insert_item_group(name):
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO item_groups (name, created_at)
                VALUES (?, CURRENT_TIMESTAMP)
                """,
                (name,),
            )
    except sqlite3.Error as e:
        print(f"Database error inserting item group: {e}")


def insert_category(category_id, category_name, item_group_id):
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO categories (id, name, item_group_id, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (category_id, category_name, item_group_id),
            )
    except sqlite3.Error as e:
        print(f"Database error inserting category: {e}")


def insert_item(item_id, item_name, item_unit, item_price, stock_quantity, category_id):
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # Insert item
            cursor.execute(
                """
                INSERT OR IGNORE INTO items (id, name, category_id, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (item_id, item_name, category_id),
            )

            # Get unit id or create new
            cursor.execute("SELECT id FROM units WHERE name = ?", (item_unit,))
            unit_id = cursor.fetchone()
            if not unit_id:
                cursor.execute(
                    """
                    INSERT INTO units (name, created_at)
                    VALUES (?, CURRENT_TIMESTAMP)
                    """,
                    (item_unit,),
                )
                unit_id = cursor.lastrowid
            else:
                unit_id = unit_id[0]

            # Insert item unit
            cursor.execute(
                """
                INSERT OR IGNORE INTO item_units (item_id, buying_unit_id, selling_unit_id, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (item_id, unit_id, unit_id),
            )

            # Insert price
            cursor.execute(
                """
                INSERT OR IGNORE INTO item_prices (item_id, store_id, unit_id, amount, created_at)
                VALUES (?, 1, ?, ?, CURRENT_TIMESTAMP)
                """,
                (item_id, unit_id, item_price),
            )

            # Insert stock
            cursor.execute(
                """
                INSERT OR IGNORE INTO stocks (item_id, store_id, min_quantity, max_quantity, created_at)
                VALUES (?, 1, ?, ?, CURRENT_TIMESTAMP)
                """,
                (item_id, stock_quantity, stock_quantity * 2),
            )

    except sqlite3.Error as e:
        print(f"Database error inserting item: {e}")


def get_customer_types():
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM customer_types WHERE is_active = 1")
            return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error getting customer types: {e}")
        return []


def get_customers():
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, customer_name FROM customers WHERE active = 1")
            return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error getting customers: {e}")
        return []


def get_payment_types():
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM payment_types")
            return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error getting payment types: {e}")
        return []


def get_payments():
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, short_code, payment_method, payment_type_id FROM payments"
            )
            return [
                {
                    "id": row[0],
                    "short_code": row[1],
                    "payment_method": row[2],
                    "payment_type_id": row[3],
                }
                for row in cursor.fetchall()
            ]
    except sqlite3.Error as e:
        print(f"Database error getting payments: {e}")
        return []


def save_order(order_data, items, payment_id, customer_id):
    print(f"Type of items in save_order: {type(items)}")
    if items and isinstance(items, list):
        print(f"Type of first element in items: {type(items[0]) if items else None}")
    else:
        print("Items is not a list or is empty!")
        return False

    print(f"Debugging save_order - order_data keys: {order_data.keys()}")

    # Validate items
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        print("Error: items must be a list of dictionaries")
        return False

    last_error = None
    retries = 3

    for attempt in range(retries):
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                print("Executing INSERT INTO orders query...")
                cursor.execute(
                    """
                    INSERT INTO orders (order_number, receipt_number, date, customer_type_id, total_amount, tip, discount, ground_total, created_at, updated_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                    """,
                    (
                        str(order_data["order_number"]),
                        str(order_data["receipt_number"]),
                        str(order_data["date"]),
                        int(order_data["customer_type_id"]),
                        float(order_data["total_amount"]),
                        float(order_data["tip"]),
                        float(order_data["discount"]),
                        float(order_data["ground_total"]),
                    ),
                )

                order_id = cursor.lastrowid  # Get the last inserted order ID

                # Insert into customer_orders table
                cursor.execute(
                    """
                    INSERT INTO customer_orders (customer_id, order_id)
                    VALUES (?, ?)
                    """,
                    (int(customer_id), order_id),
                )

                # Insert into order_payments
                cursor.execute(
                    """
                    INSERT INTO order_payments (order_id, payment_id)
                    VALUES (?, ?)
                    """,
                    (order_id, int(payment_id)),
                )

                # Insert into order_items table
                for item in items:
                    if not all(key in item for key in ["item_id", "quantity", "price"]):
                        print(f"Error: Missing required keys in item: {item}")
                        raise ValueError("Missing required keys in item")

                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, item_id, quantity, price, created_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (
                            order_id,
                            int(item["item_id"]),
                            int(item["quantity"]),
                            float(item["price"]),
                        ),
                    )

                # Stock Movement
                for item in items:
                    cursor.execute(
                        """
                        INSERT INTO stock_movements (item_id, order_id, movement_type, quantity, movement_date)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (
                            int(item["item_id"]),
                            order_id,
                            "sale",
                            -int(item["quantity"]),  # Negative for sale
                        ),
                    )

                print("Order saved successfully!")
                return True

        except sqlite3.OperationalError as e:
            last_error = e
            if "database is locked" in str(e).lower() and attempt < retries - 1:
                print(
                    f"Database locked, retrying in 1 second... ({attempt+1}/{retries})"
                )
                time.sleep(1)
                continue
            else:
                print(f"Database operational error: {e}")
                return False
        except ValueError as e:
            print(f"Value error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    print(f"Failed to save order after retries. Last error: {last_error}")
    return False


# Test the connection using the imported db
try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()
        print(f"Database connected successfully! SQLite version: {version[0]}")
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
        )
        if cursor.fetchone():
            print("Table 'users' exists.")
        else:
            print("Table 'users' does not exist.")
except sqlite3.Error as e:
    print(f"Database connection failed: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

if db.db_path.exists():
    print(f"Database file created at: {db.db_path}")
else:
    print(f"Database file NOT found at: {db.db_path}")
