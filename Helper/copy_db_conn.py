import sqlite3
from pathlib import Path
from contextlib import contextmanager
import threading
import time


class DatabaseManager:
    def __init__(self):
        self.db_path = Path("Helper/pos_amali_local.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self.lock = threading.Lock()  # Thread synchronization
        self.init_database()

    @contextmanager
    def get_connection(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30)
            try:
                yield conn
            finally:
                conn.close()

    def init_database(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Create tables if they don’t exist (example schema, adjust as needed)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS item_groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        item_group_id INTEGER,
                        created_at TIMESTAMP,
                        deleted_at TIMESTAMP,
                        FOREIGN KEY (item_group_id) REFERENCES item_groups(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        category_id INTEGER,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP,
                        FOREIGN KEY (category_id) REFERENCES categories(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS units (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS item_units (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER,
                        buying_unit_id INTEGER,
                        selling_unit_id INTEGER,
                        created_at TIMESTAMP,
                        FOREIGN KEY (item_id) REFERENCES items(id),
                        FOREIGN KEY (buying_unit_id) REFERENCES units(id),
                        FOREIGN KEY (selling_unit_id) REFERENCES units(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS item_prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER,
                        store_id INTEGER,
                        unit_id INTEGER,
                        amount REAL,
                        created_at TIMESTAMP,
                        FOREIGN KEY (item_id) REFERENCES items(id),
                        FOREIGN KEY (unit_id) REFERENCES units(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS stocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER,
                        store_id INTEGER,
                        min_quantity REAL,
                        max_quantity REAL,
                        created_at TIMESTAMP,
                        FOREIGN KEY (item_id) REFERENCES items(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        created_at TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS item_images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER,
                        image_id INTEGER,
                        created_at TIMESTAMP,
                        FOREIGN KEY (item_id) REFERENCES items(id),
                        FOREIGN KEY (image_id) REFERENCES images(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS customer_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        created_at TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_name TEXT NOT NULL,
                        active INTEGER DEFAULT 1,
                        created_at TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS payment_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        short_code TEXT NOT NULL,
                        payment_method TEXT,
                        payment_type_id INTEGER,
                        created_at TIMESTAMP,
                        FOREIGN KEY (payment_type_id) REFERENCES payment_types(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_number TEXT NOT NULL,
                        receipt_number TEXT NOT NULL,
                        date TEXT NOT NULL,
                        customer_type_id INTEGER,
                        total_amount REAL,
                        tip REAL,
                        discount REAL,
                        ground_total REAL,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP,
                        is_active INTEGER DEFAULT 1,
                        FOREIGN KEY (customer_type_id) REFERENCES customer_types(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS customer_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id INTEGER,
                        order_id INTEGER,
                        FOREIGN KEY (customer_id) REFERENCES customers(id),
                        FOREIGN KEY (order_id) REFERENCES orders(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS order_payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER,
                        payment_id INTEGER,
                        FOREIGN KEY (order_id) REFERENCES orders(id),
                        FOREIGN KEY (payment_id) REFERENCES payments(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS order_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER,
                        item_id INTEGER,
                        quantity INTEGER,
                        price REAL,
                        created_at TIMESTAMP,
                        FOREIGN KEY (order_id) REFERENCES orders(id),
                        FOREIGN KEY (item_id) REFERENCES items(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS stock_movements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER,
                        order_id INTEGER,
                        movement_type TEXT,
                        quantity INTEGER,
                        movement_date TIMESTAMP,
                        FOREIGN KEY (item_id) REFERENCES items(id),
                        FOREIGN KEY (order_id) REFERENCES orders(id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS virtual_devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        is_active INTEGER NOT NULL DEFAULT 1,
                        created_at DATETIME DEFAULT NULL,
                        updated_at DATETIME DEFAULT NULL
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS printer_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        virtual_device_id INTEGER NOT NULL,
                        printer_name TEXT NOT NULL,
                        printer_ip TEXT DEFAULT NULL,  -- For Network Printer
                        printer_type TEXT NOT NULL,
                        paper_size TEXT DEFAULT NULL,  -- For Network and Bluetooth Printers
                        bluetooth_address TEXT DEFAULT NULL,  -- For Bluetooth Printer
                        associated_printer TEXT DEFAULT NULL,  -- For Cash Drawer
                        drawer_code TEXT DEFAULT NULL,  -- For Cash Drawer
                        created_at DATETIME DEFAULT NULL,
                        updated_at DATETIME DEFAULT NULL,
                        FOREIGN KEY (virtual_device_id) REFERENCES virtual_devices(id)
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE barcodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                # Create item_barcodes table
                cursor.execute(
                    """
                    CREATE TABLE item_barcodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER NOT NULL,
                        barcode_id INTEGER NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                        FOREIGN KEY (barcode_id) REFERENCES barcodes(id) ON DELETE CASCADE
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXIST item_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    stock_id INTEGER NOT NULL,
                    stock_quantity REAL NOT NULL DEFAULT 0.00,
                    created_at timestamp NULL DEFAULT NULL,
                    updated_at timestamp NULL DEFAULT NULL,
                    deleted_at timestamp NULL DEFAULT NULL
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE companies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name TEXT NOT NULL,
                        country_id INTEGER NOT NULL,
                        state TEXT DEFAULT NULL,
                        email TEXT NOT NULL,
                        website TEXT DEFAULT NULL,
                        phone TEXT DEFAULT NULL,
                        post_code TEXT DEFAULT NULL,
                        tin_no TEXT DEFAULT NULL,
                        vrn_no TEXT DEFAULT NULL,
                        company_logo TEXT DEFAULT NULL,
                        address TEXT DEFAULT NULL,
                        is_active INTEGER NOT NULL DEFAULT 1,
                        created_at DATETIME DEFAULT NULL,
                        updated_at DATETIME DEFAULT NULL
                    );
                    """
                )

                conn.commit()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")

    def get_local_item_groups(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM item_groups")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error getting item groups: {e}")
            return []

    def get_local_categories_for_group(self, group_name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM item_groups WHERE name = ?", (group_name,)
                )
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

    def get_local_items_for_category(self, category_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        i.id,
                        i.name as item_name,
                        COALESCE(u.name, 'pcs') as item_unit,
                        COALESCE(ip.amount, 0.0) as item_price,
                        COALESCE(s.stock_quantity, 0.0) as stock_quantity,
                        COALESCE(im.file_path, 'default.jpg') as image_url
                    FROM items i
                    LEFT JOIN item_units iu ON i.id = iu.item_id
                    LEFT JOIN units u ON iu.selling_unit_id = u.id
                    LEFT JOIN item_prices ip ON i.id = ip.item_id
                    LEFT JOIN item_stocks s ON i.id = s.item_id
                    LEFT JOIN item_images ii ON i.id = ii.item_id
                    LEFT JOIN images im ON ii.image_id = im.id
                    WHERE i.category_id = ? AND i.status = 'active'
                    """,
                    (category_id,),
                )
                results = cursor.fetchall()
                items = [
                    {
                        "item_id": row[0],
                        "item_name": row[1],
                        "item_unit": row[2],
                        "item_price": float(row[3]),
                        "stock_quantity": float(row[4]),
                        "image_url": f"/uploads/item_images/{row[5]}",
                    }
                    for row in results
                ]
                print(f"Processed {len(items)} items for category {category_id}")
                return items
        except sqlite3.Error as e:
            print(f"Database error getting items for category {category_id}: {e}")
            return []

    def insert_item_group(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO item_groups (name, created_at)
                    VALUES (?, CURRENT_TIMESTAMP)
                    """,
                    (name,),
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database error inserting item group: {e}")

    def insert_category(self, category_id, category_name, item_group_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO categories (id, name, item_group_id, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (category_id, category_name, item_group_id),
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database error inserting category: {e}")

    def insert_item(
        self, item_id, item_name, item_unit, item_price, stock_quantity, category_id
    ):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO items (id, name, category_id, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (item_id, item_name, category_id),
                )

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

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO item_units (item_id, selling_unit_id, created_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (item_id, unit_id),
                )

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO item_prices (item_id, unit_id, amount, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (item_id, unit_id, item_price),
                )

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO item_stocks (item_id, stock_quantity, created_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (item_id, stock_quantity),
                )
                conn.commit()
                print(
                    f"Successfully inserted item {item_id} with category {category_id}"
                )
        except sqlite3.Error as e:
            print(f"Database error inserting item {item_id}: {e}")

    def get_customer_types(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name FROM customer_types WHERE is_active = 1"
                )
                return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error getting customer types: {e}")
            return []

    def get_customers(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, customer_name FROM customers WHERE active = 1"
                )
                return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error getting customers: {e}")
            return []

    def get_payment_types(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM payment_types")
                return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error getting payment types: {e}")
            return []

    def get_payments(self):
        try:
            with self.get_connection() as conn:
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

    def save_order(self, order_data, items, payment_id, customer_id):
        print(f"Type of items in save_order: {type(items)}")
        if items and isinstance(items, list):
            print(
                f"Type of first element in items: {type(items[0]) if items else None}"
            )
        else:
            print("Items is not a list or is empty!")
            return False

        print(f"Debugging save_order - order_data keys: {order_data.keys()}")

        if not isinstance(items, list) or not all(
            isinstance(item, dict) for item in items
        ):
            print("Error: items must be a list of dictionaries")
            return False

        try:
            with self.get_connection() as conn:
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
                order_id = cursor.lastrowid
                print(f"Order inserted with ID: {order_id}")

                if customer_id is not None:
                    cursor.execute(
                        "INSERT INTO customer_orders (customer_id, order_id) VALUES (?, ?)",
                        (int(customer_id), order_id),
                    )
                    print("Customer order inserted")

                cursor.execute(
                    "INSERT INTO order_payments (order_id, payment_id) VALUES (?, ?)",
                    (order_id, int(payment_id)),
                )
                print("Order payment inserted")

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
                    print(f"Order item inserted for item_id: {item['item_id']}")
                    cursor.execute(
                        """
                        INSERT INTO stock_movements (item_id, order_id, movement_type, quantity, movement_date)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (
                            int(item["item_id"]),
                            order_id,
                            "sale",
                            -int(item["quantity"]),
                        ),
                    )
                    print(f"Stock movement inserted for item_id: {item['item_id']}")

                conn.commit()
                print("Order saved successfully!")
                return True

        except sqlite3.OperationalError as e:
            print(f"Database operational error: {e}")
            return False
        except ValueError as e:
            print(f"Value error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    def update_item_stock(self, item_id, new_quantity):
        """Update the stock quantity of an item in the stocks table."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE item_stocks SET stock_quantity = ? WHERE item_id = ?",
                    (new_quantity, item_id),
                )
                conn.commit()
                print(f"Database updated: Item {item_id} stock set to {new_quantity}")
                return True
        except sqlite3.Error as e:
            print(f"Failed to update stock for item {item_id}: {e}")
            return False

    def get_virtual_device_data(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM virtual_devices")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error getting virtual devices: {e}")
            return []

    def insert_printer_settings(
        self,
        virtual_device_id,
        printer_type,
        printer_name,
        printer_ip=None,
        paper_size=None,
        bluetooth_address=None,
        associated_printer=None,
        drawer_code=None,
    ):
        """
        Insert printer settings into the printer_settings table.

        Args:
            virtual_device_id (int): ID of the virtual device from virtual_devices table
            printer_type (str): Type of the device ("Network Printer", "Bluetooth Printer", "Cash Drawer")
            printer_name (str): Name of the printer or device
            printer_ip (str, optional): IP address for Network Printer
            paper_size (str, optional): Paper size for Network/Bluetooth Printer
            bluetooth_address (str, optional): Bluetooth address for Bluetooth Printer
            associated_printer (str, optional): Associated printer for Cash Drawer
            drawer_code (str, optional): Drawer code for Cash Drawer
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO printer_settings (
                        virtual_device_id, printer_name, printer_type, printer_ip, paper_size,
                        bluetooth_address, associated_printer, drawer_code, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (
                        virtual_device_id,
                        printer_name,
                        printer_type,
                        printer_ip,
                        paper_size,
                        bluetooth_address,
                        associated_printer,
                        drawer_code,
                    ),
                )
                conn.commit()
                print(
                    f"Successfully inserted settings for {printer_type} with virtual_device_id {virtual_device_id}"
                )
        except sqlite3.Error as e:
            print(f"Database error inserting printer settings: {e}")
            raise

    def get_item_by_barcode(self, barcode):
        """Retrieve item details by barcode from the database."""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        i.id AS item_id,
                        i.name AS item_name,
                        u.name AS item_unit,
                        ip.amount AS item_price,
                        s.stock_quantity AS stock_quantity,
                        COALESCE(im.file_path, 'default.jpg') AS image_url
                    FROM barcodes b
                    JOIN item_barcodes ib ON b.id = ib.barcode_id
                    JOIN items i ON ib.item_id = i.id
                    LEFT JOIN item_units iu ON i.id = iu.item_id
                    LEFT JOIN units u ON iu.selling_unit_id = u.id
                    LEFT JOIN item_prices ip ON i.id = ip.item_id
                    LEFT JOIN item_stocks s ON i.id = s.item_id
                    LEFT JOIN item_images ii ON i.id = ii.item_id
                    LEFT JOIN images im ON ii.image_id = im.id
                    WHERE b.code = ? AND i.status = 'active'
                    """,
                    (barcode,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "item_id": row[0],
                        "item_name": row[1],
                        "item_unit": row[2] if row[2] else "pcs",
                        "item_price": float(row[3]) if row[3] is not None else 0.0,
                        "stock_quantity": float(row[4]) if row[4] is not None else 0.0,
                        "image_url": f"/uploads/item_images/{row[5]}",
                    }
                return None
        except sqlite3.Error as e:
            print(f"Database error retrieving item by barcode: {e}")
            return None

    def get_company_details(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, company_name, address, state, phone, tin_no, vrn_no FROM companies"
                )
                return [
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
        except sqlite3.Error as e:
            print(f"Database error getting company details: {e}")
            return []

    def get_all_local_items(self):
        """Get all items from local database for comparison"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        i.id,
                        i.name,
                        i.category_id,
                        u.name as unit_name,
                        ip.amount as price,
                        s.stock_quantity
                    FROM items i
                    LEFT JOIN item_units iu ON i.id = iu.item_id
                    LEFT JOIN units u ON iu.selling_unit_id = u.id
                    LEFT JOIN item_prices ip ON i.id = ip.item_id
                    LEFT JOIN item_stocks s ON i.id = s.item_id
                    WHERE i.status = 'active'
                """
                )
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "category_id": row[2],
                        "unit_name": row[3],
                        "price": float(row[4]) if row[4] else 0.0,
                        "stock_quantity": float(row[5]) if row[5] else 0.0,
                    }
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            print(f"Error getting all local items: {e}")
            return []

    def update_item(self, item_id, name, unit_name, price, stock_quantity, category_id):
        """Update existing item in local database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Update item name and category
                cursor.execute(
                    """
                    UPDATE items 
                    SET name = ?, category_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (name, category_id, item_id),
                )

                # Get or create unit
                cursor.execute("SELECT id FROM units WHERE name = ?", (unit_name,))
                unit_id = cursor.fetchone()
                if not unit_id:
                    cursor.execute(
                        """
                        INSERT INTO units (name, created_at)
                        VALUES (?, CURRENT_TIMESTAMP)
                    """,
                        (unit_name,),
                    )
                    unit_id = cursor.lastrowid
                else:
                    unit_id = unit_id[0]

                # Update item_units
                cursor.execute(
                    """
                    UPDATE item_units 
                    SET selling_unit_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                """,
                    (unit_id, item_id),
                )

                # Update price
                cursor.execute(
                    """
                    UPDATE item_prices 
                    SET amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                """,
                    (price, item_id),
                )

                # Update stock
                cursor.execute(
                    """
                    UPDATE item_stocks 
                    SET stock_quantity = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                """,
                    (stock_quantity, item_id),
                )

                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error updating item {item_id}: {e}")
            return False


db = DatabaseManager()

try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()
        print(f"Database connected successfully! SQLite version: {version}")
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
        )
        table_exists = cursor.fetchone()
        if table_exists:
            print("Table 'users' exists.")
        else:
            print(
                "Table 'users' does NOT exist. There might be an issue with table creation in init_database."
            )
except sqlite3.Error as e:
    print(f"Database connection failed: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

if db.db_path.exists():
    print(f"Database file created at: {db.db_path}")
else:
    print(
        f"Database file was NOT created at: {db.db_path}. There might be an issue with file path or permissions."
    )
