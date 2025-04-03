import hashlib
import logging
import sqlite3
from pathlib import Path
from contextlib import contextmanager
import threading
import time


class DatabaseManager:
    def __init__(self):
        self.db_path = Path("Helper/main_amali.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self.sync_in_progress = False
        self.init_database()

    @contextmanager
    def get_connection(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            try:
                yield conn
            finally:
                conn.close()

    def init_database(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                   CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    fullname TEXT NOT NULL,
                    username TEXT NOT NULL,
                    email TEXT DEFAULT NULL,
                    phone TEXT DEFAULT NULL,
                    email_verified_at TEXT DEFAULT NULL,
                    phone_verified_at TEXT DEFAULT NULL,
                    password TEXT NOT NULL,
                    pin INTEGER NOT NULL,
                    remember_token TEXT DEFAULT NULL,
                    created_at TEXT DEFAULT NULL,
                    updated_at TEXT DEFAULT NULL
                    );
                """
                )
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
                        updated_at TIMESTAMP,
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
                    category_id INTEGER NOT NULL,
                    item_type_id INTEGER,  -- Nullable
                    item_group_id INTEGER,  -- Nullable
                    exprire_date TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    FOREIGN KEY (item_type_id) REFERENCES item_types(id),
                    FOREIGN KEY (item_group_id) REFERENCES item_groups(id)
                );
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS item_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    item_id INTEGER NOT NULL,
                    buying_unit_id INTEGER NOT NULL,
                    selling_unit_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                    FOREIGN KEY (buying_unit_id) REFERENCES units(id),
                    FOREIGN KEY (selling_unit_id) REFERENCES units(id)
                );
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS item_prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER NOT NULL,
                        store_id INTEGER NOT NULL,
                        unit_id INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                        FOREIGN KEY (store_id) REFERENCES stores(id),
                        FOREIGN KEY (unit_id) REFERENCES units(id)
                    );
                """
                )
                cursor.execute(
                    """
                   CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    store_id INTEGER NOT NULL,
                    min_quantity REAL,
                    max_quantity REAL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id),
                    FOREIGN KEY (store_id) REFERENCES stores(id),
                    UNIQUE(item_id, store_id)  -- Ensure uniqueness per item and store
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
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
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
                        status TEXT CHECK(status IN ('completed', 'settled', 'voided')) DEFAULT 'completed',  -- Added status column
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
                    CREATE TABLE IF NOT EXISTS barcodes (
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
                    CREATE TABLE IF NOT EXISTS item_barcodes (
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
                    CREATE TABLE IF NOT EXISTS item_stocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER NOT NULL,
                        stock_id INTEGER NOT NULL,
                        stock_quantity REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                        FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS companies (
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
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS stores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        location TEXT NOT NULL,
                        manager_id INTEGER NOT NULL,
                        created_at DATETIME DEFAULT NULL,
                        updated_at DATETIME DEFAULT NULL,
                        FOREIGN KEY (manager_id) REFERENCES users(id)
                    );

                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS item_stores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    store_id INTEGER NOT NULL,
                    created_at timestamp NULL DEFAULT NULL,
                    updated_at timestamp NULL DEFAULT NULL
                    );
                    """
                )

                cursor.execute(
                    """
                        CREATE TABLE IF NOT EXISTS carts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_number TEXT NOT NULL UNIQUE,
                            customer_type_id INTEGER NOT NULL,
                            customer_id INTEGER,
                            total_amount REAL NOT NULL DEFAULT 0.00,
                            status TEXT CHECK(status IN ('in-cart', 'settled', 'voided')) NOT NULL DEFAULT 'in-cart',
                            date DATETIME NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (customer_type_id) REFERENCES customer_types(id),
                            FOREIGN KEY (customer_id) REFERENCES customers(id)
                        )
                    """
                )

                # Add cart_items table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cart_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cart_id INTEGER NOT NULL,
                        item_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        unit TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (cart_id) REFERENCES carts(id),
                        FOREIGN KEY (item_id) REFERENCES items(id)
                    )
                """
                )

                # Add cart_extra_charges table
                cursor.execute(
                    """
                        CREATE TABLE IF NOT EXISTS cart_extra_charges (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            cart_id INTEGER NOT NULL,
                            name TEXT NOT NULL,
                            amount REAL NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (cart_id) REFERENCES carts(id)
                        )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        expense_type TEXT NOT NULL CHECK (expense_type IN ('home', 'shop')),
                        user_id INTEGER NOT NULL,
                        expense_date DATE NOT NULL,
                        amount REAL NOT NULL,
                        description TEXT DEFAULT NULL,
                        reference_number TEXT DEFAULT NULL,
                        receipt_path TEXT DEFAULT NULL,
                        linked_shop_item_id INTEGER DEFAULT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        
                        FOREIGN KEY (linked_shop_item_id) REFERENCES items(id)
                        );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS expense_items (
                        expense_id INTEGER NOT NULL,
                        item_id INTEGER NOT NULL,
                        FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
                        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                        PRIMARY KEY (expense_id, item_id)
                    );
                    """
                )

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO item_types (id, name, created_at)
                    VALUES (1, 'Inventory', CURRENT_TIMESTAMP)
                    """
                )
                cursor.execute(
                    """
                   CREATE TABLE IF NOT EXISTS day_close (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        store_id INTEGER NOT NULL,
                        total_amount REAL DEFAULT 0.0,
                        working_date DATE NOT NULL,
                        next_working_date DATE NOT NULL,
                        running_orders INTEGER DEFAULT 0,
                        voided_orders INTEGER DEFAULT 0,
                        FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
                    )
                    """
                )

                hashed_password = (
                    "$2y$12$BlLtxbg53w4RNZmkwRq7T.R/6NMzKD0maVtGpMe1aeVBcCjghcckG"
                )
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO users (id, fullname, username, password, pin, created_at, updated_at)
                    VALUES (1, 'Administrator', 'admin', ?, 1234, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (hashed_password,),
                )

                # Insert default store
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO stores (id, name, location, manager_id, created_at, updated_at)
                    VALUES (1, 'Mohalal Shop', 'Forest', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                )

                # Insert default payment type
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO payment_types (id, name, created_at, updated_at)
                    VALUES (1, 'Cash', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                )

                # Insert default payment
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO payments (id, short_code, payment_method, payment_type_id, created_at)
                    VALUES (1, 'Cash', 'Cash payment', 1, CURRENT_TIMESTAMP)
                    """
                )

                conn.commit()
                # Verify insertions
                cursor.execute("SELECT id FROM users WHERE username = 'admin'")
                admin_user = cursor.fetchone()
                if admin_user:
                    print(f"Admin user created with ID: {admin_user[0]}")
                else:
                    print("Failed to create admin user!")

                cursor.execute("SELECT id FROM stores WHERE name = 'Mohalal Shop'")
                store = cursor.fetchone()
                if store:
                    print(f"Store created with ID: {store[0]}")
                else:
                    print("Failed to create default store!")

                cursor.execute("SELECT id FROM payment_types WHERE name = 'Cash'")
                payment_type = cursor.fetchone()
                if payment_type:
                    print(f"Payment type created with ID: {payment_type[0]}")
                else:
                    print("Failed to create default payment type!")

                cursor.execute("SELECT id FROM payments WHERE short_code = 'Cash'")
                payment = cursor.fetchone()
                if payment:
                    print(f"Payment created with ID: {payment[0]}")
                else:
                    print("Failed to create default payment!")

        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            if "conn" in locals():
                conn.rollback()
            raise

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
                        u.name as item_unit,
                        ip.amount as item_price,
                        s.stock_quantity as stock_quantity,
                        COALESCE(im.file_path, 'default.jpg') as image_url
                    FROM items i
                    LEFT JOIN item_units iu ON i.id = iu.item_id
                    LEFT JOIN units u ON iu.selling_unit_id = u.id
                    LEFT JOIN item_prices ip ON i.id = ip.item_id
                    LEFT JOIN item_stocks s ON i.id = s.item_id
                    LEFT JOIN item_images ii ON i.id = ii.item_id
                    LEFT JOIN images im ON ii.image_id = im.id
                    WHERE i.category_id = ?
                    """,
                    (category_id,),
                )
                results = cursor.fetchall()
                items = [
                    {
                        "item_id": row[0],
                        "item_name": row[1],
                        "item_unit": row[2],
                        "item_price": float(row[3]) if row[3] is not None else 0.0,
                        "stock_quantity": float(row[4]) if row[4] is not None else 0.0,
                        "image_url": f"/uploads/item_images/{row[5]}",
                    }
                    for row in results
                ]
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
        self, item_id, name, barcode, item_unit, item_price, stock_quantity, category_id
    ):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Insert or update item (this part is fine as is)
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO items (id, name, category_id, item_type_id, item_group_id, status, created_at, updated_at)
                    VALUES (?, ?, ?, 1, NULL, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (item_id, name, category_id),
                )

                # Handle barcode: Check if the barcode already exists for this item
                if barcode and barcode.strip():
                    cursor.execute("SELECT id FROM barcodes WHERE code = ?", (barcode,))
                    barcode_row = cursor.fetchone()
                    if barcode_row:
                        barcode_id = barcode_row[0]
                    else:
                        cursor.execute(
                            "INSERT INTO barcodes (code, created_at, updated_at) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                            (barcode,),
                        )
                        barcode_id = cursor.lastrowid

                    # Check if the item already has this barcode to avoid duplicates
                    cursor.execute(
                        "SELECT id FROM item_barcodes WHERE item_id = ? AND barcode_id = ?",
                        (item_id, barcode_id),
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            """
                            INSERT INTO item_barcodes (item_id, barcode_id, created_at, updated_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """,
                            (item_id, barcode_id),
                        )

                # Handle unit: Check if the unit exists, create if not
                unit_name = item_unit if item_unit and item_unit.strip() else "Unit"
                cursor.execute("SELECT id FROM units WHERE name = ?", (unit_name,))
                unit_row = cursor.fetchone()
                if unit_row:
                    unit_id = unit_row[0]
                else:
                    cursor.execute(
                        "INSERT INTO units (name, created_at) VALUES (?, CURRENT_TIMESTAMP)",
                        (unit_name,),
                    )
                    unit_id = cursor.lastrowid

                # Check if item_units already exists to avoid duplicates
                cursor.execute(
                    "SELECT id FROM item_units WHERE item_id = ? AND buying_unit_id = ? AND selling_unit_id = ?",
                    (item_id, unit_id, unit_id),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        """
                        INSERT INTO item_units (item_id, buying_unit_id, selling_unit_id, created_at, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (item_id, unit_id, unit_id),
                    )

                # Insert or update item_prices: Check if price exists for this item and store
                price = float(item_price) if item_price is not None else 0.0
                cursor.execute(
                    "SELECT id FROM item_prices WHERE item_id = ? AND store_id = ? AND unit_id = ?",
                    (item_id, 1, unit_id),
                )
                price_row = cursor.fetchone()
                if price_row:
                    cursor.execute(
                        """
                        UPDATE item_prices 
                        SET amount = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                        """,
                        (price, price_row[0]),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO item_prices (item_id, store_id, unit_id, amount, created_at, updated_at)
                        VALUES (?, 1, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (item_id, unit_id, price),
                    )

                # Insert or update stocks: Check if stock exists for this item and store
                cursor.execute(
                    "SELECT id FROM stocks WHERE item_id = ? AND store_id = 1",
                    (item_id,),
                )
                stock_row = cursor.fetchone()
                if stock_row:
                    stock_id = stock_row[0]
                else:
                    cursor.execute(
                        """
                        INSERT INTO stocks (item_id, store_id, min_quantity, max_quantity, created_at, updated_at)
                        VALUES (?, 1, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (item_id,),
                    )
                    stock_id = cursor.lastrowid

                # Insert or update item_stocks: Check if item_stocks exists for this item
                stock_qty = float(stock_quantity) if stock_quantity is not None else 0.0
                cursor.execute(
                    "SELECT id FROM item_stocks WHERE item_id = ? AND stock_id = ?",
                    (item_id, stock_id),
                )
                item_stock_row = cursor.fetchone()
                if item_stock_row:
                    cursor.execute(
                        """
                        UPDATE item_stocks 
                        SET stock_quantity = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                        """,
                        (stock_qty, item_stock_row[0]),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO item_stocks (item_id, stock_id, stock_quantity, created_at, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (item_id, stock_id, stock_qty),
                    )

                conn.commit()
                print(f"Inserted/Updated item {item_id} ({name}) into local database")
        except sqlite3.Error as e:
            print(f"Error inserting item {item_id} ({name}): {e}")
            if "conn" in locals():
                conn.rollback()
            raise

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

    def save_order(self, order_data, items, payment_id, customer_id):
        print(f"Type of items in save_order: {type(items)}")
        if items and isinstance(items, list):
            print(
                f"Type of first element in items: {type(items[0]) if items else None}"
            )
        else:
            print("Items is not a list or is empty!")
            return None

        print(f"Debugging save_order - order_data: {order_data}")
        print(f"Items: {items}")

        if not isinstance(items, list) or not all(
            isinstance(item, dict) for item in items
        ):
            print("Error: items must be a list of dictionaries")
            return None

        stock_changes = []  # To track stock updates for server sync

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
                        (
                            int(order_data["customer_type_id"])
                            if order_data["customer_type_id"]
                            else None
                        ),
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

                    # Update local stock and track changes
                    cursor.execute(
                        "SELECT stock_id, stock_quantity FROM item_stocks WHERE item_id = ?",
                        (int(item["item_id"]),),
                    )
                    stock_row = cursor.fetchone()
                    if not stock_row:
                        raise ValueError(
                            f"No stock found for item_id: {item['item_id']}"
                        )
                    stock_id, current_quantity = stock_row
                    if current_quantity < item["quantity"]:
                        raise ValueError(
                            f"Insufficient stock for item_id: {item['item_id']}"
                        )

                    # Deduct the quantity
                    cursor.execute(
                        "UPDATE item_stocks SET stock_quantity = stock_quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE item_id = ?",
                        (int(item["quantity"]), int(item["item_id"])),
                    )

                    # Fetch the updated stock quantity
                    cursor.execute(
                        "SELECT stock_quantity FROM item_stocks WHERE item_id = ?",
                        (int(item["item_id"]),),
                    )
                    updated_quantity = cursor.fetchone()[0]

                    stock_changes.append(
                        {
                            "item_id": int(item["item_id"]),
                            "quantity_change": -int(
                                item["quantity"]
                            ),  # Track the change (deduction)
                            "new_quantity": float(
                                updated_quantity
                            ),  # The new stock quantity (e.g., 19)
                            "stock_id": stock_id,
                        }
                    )

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

                # Return order data and stock changes for syncing
                return {
                    "order_id": order_id,
                    "stock_changes": stock_changes,
                }
        except sqlite3.OperationalError as e:
            print(f"Database operational error: {e}")
            return None
        except ValueError as e:
            print(f"Value error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def get_orders_by_status(self, status=None, date=None):
        logging.debug(f"Fetching orders with status: {status}, date: {date}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                SELECT order_number, date, receipt_number, status, total_amount
                FROM orders
                WHERE is_active = 1
                """
                params = []
                if date:
                    query += " AND DATE(date) = ?"  # Use DATE function to compare only the date part
                    params.append(date)
                    logging.debug(f"Added date filter: {date}")
                if status:  # Apply status filter for all non-None statuses
                    query += " AND status = ?"
                    params.append(status)
                    logging.debug(f"Added status filter: {status}")
                logging.debug(f"Executing query: {query} with params: {params}")
                cursor.execute(query, params)
                rows = cursor.fetchall()
                logging.debug(f"Retrieved {len(rows)} rows from database")
                orders = []
                for row in rows:
                    logging.debug(f"Raw row data: {row}")
                    orders.append(
                        {
                            "order_no": row[0],
                            "time": row[
                                1
                            ],  # Use the correct column index for created_at
                            "receipt_no": row[2],
                            "status": row[3],
                            "total_amount": float(row[4]) if row[4] else 0.0,
                        }
                    )
                logging.debug(f"Processed orders: {orders}")
                return orders
        except sqlite3.Error as e:
            logging.error(f"Database error getting orders: {e}")
            return []

    def get_order_for_order_summary(self, order_date):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_number, receipt_number, date, customer_type_id, total_amount, ground_total, status
                    FROM orders WHERE date = ?
                    """,
                    (order_date,),
                )
                order_row = cursor.fetchone()
                if not order_row:
                    return None

                return {
                    "order_number": order_row[0],
                    "receipt_number": order_row[1],
                    "status": order_row[2],
                    "date": order_row[3],
                    "total_amount": float(order_row[4]),
                    "ground_total": float(order_row[5]),
                }
        except sqlite3.Error as e:
            print(f"Database error getting order for sync: {e}")
            return None

    def get_order_for_sync(self, order_id):
        """Fetch order details from local database for syncing to server."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT order_number, receipt_number, date, customer_type_id, total_amount, tip, discount, ground_total
                    FROM orders WHERE id = ?
                    """,
                    (order_id,),
                )
                order_row = cursor.fetchone()
                if not order_row:
                    return None

                cursor.execute(
                    "SELECT customer_id FROM customer_orders WHERE order_id = ?",
                    (order_id,),
                )
                customer_row = cursor.fetchone()
                customer_id = customer_row[0] if customer_row else None

                cursor.execute(
                    "SELECT payment_id FROM order_payments WHERE order_id = ?",
                    (order_id,),
                )
                payment_row = cursor.fetchone()
                payment_id = payment_row[0] if payment_row else None

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
                    "items": items,
                }
        except sqlite3.Error as e:
            print(f"Database error getting order for sync: {e}")
            return None

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

    def save_cart(self, cart_data):
        """
        Save cart data to the database.

        Args:
            cart_data (dict): Dictionary containing cart information with keys:
                - order_number (str)
                - customer_type_id (int)
                - customer_id (int, optional)
                - total_amount (float)
                - date (str)
                - items (list of dicts with item_id, name, unit, quantity, amount)
                - extra_charges (list of dicts with name, amount)

        Returns:
            dict: Success status and message or error details
        """
        try:
            # Basic validation
            required_fields = [
                "order_number",
                "customer_type_id",
                "total_amount",
                "items",
                "date",
            ]
            for field in required_fields:
                if field not in cart_data:
                    raise ValueError(f"Missing required field: {field}")

            if not isinstance(cart_data["items"], list) or not cart_data["items"]:
                raise ValueError("Items must be a non-empty list")

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Begin transaction
                conn.execute("BEGIN TRANSACTION")

                # Check if order_number is unique
                cursor.execute(
                    "SELECT id FROM carts WHERE order_number = ?",
                    (cart_data["order_number"],),
                )
                if cursor.fetchone():
                    raise ValueError(
                        f"Order number {cart_data['order_number']} already exists"
                    )

                # Validate customer_type_id exists
                cursor.execute(
                    "SELECT id FROM customer_types WHERE id = ?",
                    (cart_data["customer_type_id"],),
                )
                if not cursor.fetchone():
                    raise ValueError(
                        f"Customer type ID {cart_data['customer_type_id']} does not exist"
                    )

                # Validate customer_id if provided
                if "customer_id" in cart_data and cart_data["customer_id"]:
                    cursor.execute(
                        "SELECT id FROM customers WHERE id = ?",
                        (cart_data["customer_id"],),
                    )
                    if not cursor.fetchone():
                        raise ValueError(
                            f"Customer ID {cart_data['customer_id']} does not exist"
                        )

                # Insert cart
                cursor.execute(
                    """
                    INSERT INTO carts (order_number, customer_type_id, customer_id, total_amount, date, status)
                    VALUES (?, ?, ?, ?, ?, 'in-cart')
                """,
                    (
                        cart_data["order_number"],
                        cart_data["customer_type_id"],
                        cart_data.get("customer_id"),
                        float(cart_data["total_amount"]),
                        cart_data["date"],
                    ),
                )
                cart_id = cursor.lastrowid

                # Insert cart items
                for item in cart_data["items"]:
                    required_item_fields = ["name", "unit", "quantity", "amount"]
                    for field in required_item_fields:
                        if field not in item:
                            raise ValueError(f"Missing required item field: {field}")

                    # Get item_id if not provided
                    item_id = item.get("item_id")
                    if not item_id:
                        cursor.execute(
                            "SELECT id FROM items WHERE name = ?", (item["name"],)
                        )
                        item_row = cursor.fetchone()
                        if not item_row:
                            raise ValueError(f"Item with name {item['name']} not found")
                        item_id = item_row[0]
                    else:
                        # Validate item_id exists
                        cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
                        if not cursor.fetchone():
                            raise ValueError(f"Item ID {item_id} does not exist")

                    cursor.execute(
                        """
                        INSERT INTO cart_items (cart_id, item_id, name, unit, quantity, amount)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            cart_id,
                            item_id,
                            item["name"],
                            item["unit"],
                            int(item["quantity"]),
                            float(item["amount"]),
                        ),
                    )

                # Insert extra charges if provided
                if "extra_charges" in cart_data and cart_data["extra_charges"]:
                    for charge in cart_data["extra_charges"]:
                        if not all(key in charge for key in ["name", "amount"]):
                            raise ValueError("Extra charges must have name and amount")

                        cursor.execute(
                            """
                            INSERT INTO cart_extra_charges (cart_id, name, amount)
                            VALUES (?, ?, ?)
                        """,
                            (cart_id, charge["name"], float(charge["amount"])),
                        )

                # Commit transaction
                conn.commit()

                return {
                    "success": True,
                    "message": "Cart saved successfully",
                    "cart_id": cart_id,
                }

        except ValueError as e:
            if "conn" in locals():
                conn.rollback()
            print(f"Validation error: {str(e)}")
            return {"success": False, "message": str(e)}
        except sqlite3.Error as e:
            if "conn" in locals():
                conn.rollback()
            print(f"Database error: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        except Exception as e:
            if "conn" in locals():
                conn.rollback()
            print(f"Unexpected error: {str(e)}")
            return {"success": False, "message": f"Unexpected error: {str(e)}"}

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
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # First try barcode lookup
                cursor.execute(
                    """
                    SELECT 
                        i.id,
                        i.name AS item_name,
                        u.name AS item_unit,
                        ip.amount AS item_price,
                        s.stock_quantity
                    FROM items i
                    JOIN item_barcodes ib ON i.id = ib.item_id
                    JOIN barcodes b ON ib.barcode_id = b.id
                    LEFT JOIN item_units iu ON i.id = iu.item_id
                    LEFT JOIN units u ON iu.selling_unit_id = u.id
                    LEFT JOIN item_prices ip ON i.id = ip.item_id
                    LEFT JOIN item_stocks s ON i.id = s.item_id
                    WHERE b.code = ?
                    """,
                    (barcode,),
                )
                item = cursor.fetchone()
                if item:
                    item_dict = {
                        "item_id": item[0],  # Changed from "id" to "item_id"
                        "item_name": item[1],
                        "item_unit": item[2],
                        "item_price": item[3],
                        "stock_quantity": item[4],
                    }
                    print(f"get_item_by_barcode result (barcode): {item_dict}")
                    return item_dict

                # Fallback to item_id if barcode is numeric and no barcode match
                if barcode and barcode.isdigit():
                    cursor.execute(
                        """
                        SELECT 
                            i.id,
                            i.name AS item_name,
                            u.name AS item_unit,
                            ip.amount AS item_price,
                            s.stock_quantity
                        FROM items i
                        LEFT JOIN item_units iu ON i.id = iu.item_id
                        LEFT JOIN units u ON iu.selling_unit_id = u.id
                        LEFT JOIN item_prices ip ON i.id = ip.item_id
                        LEFT JOIN item_stocks s ON i.id = s.item_id
                        WHERE i.id = ?
                        """,
                        (int(barcode),),
                    )
                    item = cursor.fetchone()
                    if item:
                        item_dict = {
                            "item_id": item[0],  # Changed from "id" to "item_id"
                            "item_name": item[1],
                            "item_unit": item[2],
                            "item_price": item[3],
                            "stock_quantity": item[4],
                        }
                        print(
                            f"get_item_by_barcode result (item_id fallback): {item_dict}"
                        )
                        return item_dict

                print(f"No item found for barcode or ID: {barcode}")
                return None
        except sqlite3.Error as e:
            print(f"CRITICAL DATABASE ERROR in get_item_by_barcode: {str(e)}")
            import traceback

            traceback.print_exc()
            return None

    def get_company_details(self):
        """Fetch company details from local database."""
        try:
            with self.get_connection() as conn:
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

    def update_company_details(self, company_data):
        """Update or insert company details into the local database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO companies (
                        id, company_name, address, state, phone, tin_no, vrn_no, 
                        country_id, email, website, post_code, company_logo, 
                        is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        company_data.get("id"),
                        company_data.get("company_name"),
                        company_data.get("address"),
                        company_data.get("state"),
                        company_data.get("phone"),
                        company_data.get("tin_no"),
                        company_data.get("vrn_no"),
                        company_data.get("country_id", 0),  # Default if not provided
                        company_data.get("email", ""),
                        company_data.get("website"),
                        company_data.get("post_code"),
                        company_data.get("company_logo"),
                        company_data.get("is_active", 1),
                        company_data.get(
                            "created_at", time.strftime("%Y-%m-%d %H:%M:%S")
                        ),
                        time.strftime("%Y-%m-%d %H:%M:%S"),  # Updated_at set to now
                    ),
                )
                conn.commit()
                print(f"Updated company details for {company_data.get('company_name')}")
                return True
        except sqlite3.Error as e:
            print(f"Error updating company details: {e}")
            return False

    def get_all_local_companies(self):
        """Fetch all company details from local database for sync purposes."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, company_name, address, state, phone, tin_no, vrn_no, 
                           country_id, email, website, post_code, company_logo, is_active
                    FROM companies
                    """
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
                        "country_id": row[7],
                        "email": row[8],
                        "website": row[9],
                        "post_code": row[10],
                        "company_logo": row[11],
                        "is_active": row[12],
                    }
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            print(f"Error getting all local companies: {e}")
            return []
    def get_item_by_id(self, item_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        i.name AS item_name,
                        u.name AS item_unit,
                        ip.amount AS item_price,
                        s.stock_quantity
                    FROM items i
                    LEFT JOIN item_units iu ON i.id = iu.item_id
                    LEFT JOIN units u ON iu.selling_unit_id = u.id
                    LEFT JOIN item_prices ip ON i.id = ip.item_id AND ip.store_id = 1
                    LEFT JOIN item_stocks s ON i.id = s.item_id
                    WHERE i.id = ?
                    """,
                    (item_id,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "item_name": row[0],
                        "item_unit": row[1] if row[1] else "Unit",  # Default to "Unit" if null
                        "item_price": float(row[2]) if row[2] is not None else 0.0,
                        "stock_quantity": float(row[3]) if row[3] is not None else 0.0
                    }
                print(f"No item found with ID {item_id}")
                return None
        except sqlite3.Error as e:
            print(f"Error fetching item by ID {item_id}: {e}")
            return None
    def get_all_local_items(self):
        """Get all items from local database with barcode and store details"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        i.id,
                        i.name,
                        i.category_id,
                        i.item_type_id,
                        i.item_group_id,
                        i.exprire_date,
                        b.code AS barcode,
                        u_selling.name AS selling_unit_name,
                        u_buying.name AS buying_unit_name,
                        ip.amount AS price,
                        s.stock_quantity,
                        st.min_quantity,
                        st.max_quantity,
                        st.store_id
                    FROM items i
                    LEFT JOIN item_barcodes ib ON i.id = ib.item_id
                    LEFT JOIN barcodes b ON ib.barcode_id = b.id
                    LEFT JOIN item_units iu ON i.id = iu.item_id
                    LEFT JOIN units u_selling ON iu.selling_unit_id = u_selling.id
                    LEFT JOIN units u_buying ON iu.buying_unit_id = u_buying.id
                    LEFT JOIN item_stocks s ON i.id = s.item_id
                    LEFT JOIN stocks st ON s.stock_id = st.id
                    LEFT JOIN item_prices ip ON i.id = ip.item_id
                    WHERE i.status = 'active'
                    """
                )
                rows = cursor.fetchall()
                items_dict = {}
                for row in rows:
                    item_id = row[0]
                    if item_id not in items_dict:
                        items_dict[item_id] = {
                            "id": item_id,
                            "name": row[1],
                            "category_id": row[2],
                            "item_type_id": row[3],
                            "item_group_id": row[4],
                            "exprire_date": row[5],
                            "barcode": row[6],
                            "selling_unit_name": row[7],
                            "buying_unit_name": row[8],
                            "prices": {},
                            "stocks": {},
                        }
                    # Add price and stock per store
                    store_id = (
                        row[13] if row[13] is not None else 0
                    )  # Default store_id if not provided
                    items_dict[item_id]["prices"][store_id] = (
                        float(row[9]) if row[9] else 0.0
                    )
                    items_dict[item_id]["stocks"][store_id] = {
                        "stock_quantity": float(row[10]) if row[10] else 0.0,
                        "min_quantity": float(row[11]) if row[11] else 0.0,
                        "max_quantity": float(row[12]) if row[12] else 0.0,
                    }
                return list(items_dict.values())
        except sqlite3.Error as e:
            print(f"Error getting all local items: {e}")
            return []

    def update_item(
        self,
        item_id,
        name,
        barcode,
        category_id,
        item_type_id,
        item_group_id,
        exprire_date,
        buying_unit_name,
        selling_unit_name,
        price_dict,
        stock_dict,
    ):
        """Update existing item in local database with server-like structure"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Update items table
                cursor.execute(
                    """
                    UPDATE items 
                    SET name = ?, category_id = ?, item_type_id = ?, item_group_id = ?, exprire_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        name,
                        category_id,
                        item_type_id,
                        item_group_id,
                        exprire_date,
                        item_id,
                    ),
                )

                # Update or insert barcode
                cursor.execute("SELECT id FROM barcodes WHERE code = ?", (barcode,))
                barcode_id = cursor.fetchone()
                if not barcode_id:
                    cursor.execute(
                        """
                        INSERT INTO barcodes (code, created_at, updated_at)
                        VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (barcode,),
                    )
                    barcode_id = cursor.lastrowid
                else:
                    barcode_id = barcode_id[0]

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO item_barcodes (item_id, barcode_id, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (item_id, barcode_id),
                )

                # Get or create buying unit
                cursor.execute(
                    "SELECT id FROM units WHERE name = ?", (buying_unit_name,)
                )
                buying_unit_id = cursor.fetchone()
                if not buying_unit_id:
                    cursor.execute(
                        """
                        INSERT INTO units (name, created_at)
                        VALUES (?, CURRENT_TIMESTAMP)
                        """,
                        (buying_unit_name,),
                    )
                    buying_unit_id = cursor.lastrowid
                else:
                    buying_unit_id = buying_unit_id[0]

                # Get or create selling unit
                cursor.execute(
                    "SELECT id FROM units WHERE name = ?", (selling_unit_name,)
                )
                selling_unit_id = cursor.fetchone()
                if not selling_unit_id:
                    cursor.execute(
                        """
                        INSERT INTO units (name, created_at)
                        VALUES (?, CURRENT_TIMESTAMP)
                        """,
                        (selling_unit_name,),
                    )
                    selling_unit_id = cursor.lastrowid
                else:
                    selling_unit_id = selling_unit_id[0]

                # Update item_units
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO item_units (item_id, buying_unit_id, selling_unit_id, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (item_id, buying_unit_id, selling_unit_id),
                )

                # Update prices and stocks per store
                for store_id, price in price_dict.items():
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO item_prices (item_id, store_id, unit_id, amount, created_at, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (item_id, store_id, selling_unit_id, price),
                    )

                for store_id, stock in stock_dict.items():
                    # Insert or update stocks
                    cursor.execute(
                        """
                        INSERT INTO stocks (item_id, store_id, min_quantity, max_quantity, created_at, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT(item_id, store_id) DO UPDATE SET
                            min_quantity = excluded.min_quantity,
                            max_quantity = excluded.max_quantity,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (
                            item_id,
                            store_id,
                            stock["min_quantity"],
                            stock["max_quantity"],
                        ),
                    )
                    cursor.execute(
                        "SELECT id FROM stocks WHERE item_id = ? AND store_id = ?",
                        (item_id, store_id),
                    )
                    stock_id = cursor.fetchone()[0]

                    # Insert or update item_stocks
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO item_stocks (item_id, stock_id, stock_quantity, created_at, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (item_id, stock_id, stock["stock_quantity"]),
                    )

                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error updating item {item_id}: {e}")
            return False

    def insert_payment(self, payment_id, short_code, payment_method, payment_type_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO payments (id, short_code, payment_method, payment_type_id, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (payment_id, short_code, payment_method, payment_type_id),
                )
                conn.commit()
                print(f"Inserted payment {payment_id} ({short_code})")
        except sqlite3.Error as e:
            print(f"Error inserting payment {payment_id}: {e}")

    def update_payment(self, payment_id, short_code, payment_method, payment_type_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE payments 
                    SET short_code = ?, payment_method = ?, payment_type_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (short_code, payment_method, payment_type_id, payment_id),
                )
                conn.commit()
                print(f"Updated payment {payment_id} ({short_code})")
        except sqlite3.Error as e:
            print(f"Error updating payment {payment_id}: {e}")

    # Add methods for customers
    def insert_customer(self, customer_id, customer_name, active=1):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO customers (id, customer_name, active, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (customer_id, customer_name, active),
                )
                conn.commit()
                print(f"Inserted customer {customer_id} ({customer_name})")
        except sqlite3.Error as e:
            print(f"Error inserting customer {customer_id}: {e}")

    def update_customer(self, customer_id, customer_name, active=1):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE customers 
                    SET customer_name = ?, active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (customer_name, active, customer_id),
                )
                conn.commit()
                print(f"Updated customer {customer_id} ({customer_name})")
        except sqlite3.Error as e:
            print(f"Error updating customer {customer_id}: {e}")

    # Add methods for customer types
    def insert_customer_type(self, type_id, name, is_active=1):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO customer_types (id, name, is_active, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (type_id, name, is_active),
                )
                conn.commit()
                print(f"Inserted customer type {type_id} ({name})")
        except sqlite3.Error as e:
            print(f"Error inserting customer type {type_id}: {e}")

    def update_customer_type(self, type_id, name, is_active=1):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE customer_types 
                    SET name = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (name, is_active, type_id),
                )
                conn.commit()
                print(f"Updated customer type {type_id} ({name})")
        except sqlite3.Error as e:
            print(f"Error updating customer type {type_id}: {e}")

    # Add methods to get all local data for sync purposes
    def get_all_local_payments(self):
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
            print(f"Error getting all local payments: {e}")
            return []

    def get_all_local_customers(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, customer_name, active FROM customers")
                return [
                    {"id": row[0], "customer_name": row[1], "active": row[2]}
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            print(f"Error getting all local customers: {e}")
            return []

    def get_all_local_customer_types(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, is_active FROM customer_types")
                return [
                    {"id": row[0], "name": row[1], "is_active": row[2]}
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            print(f"Error getting all local customer types: {e}")
            return []


db = DatabaseManager()

try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()
        print(f"Database connected successfully! SQLite version: {version[0]}")

        # Verify key tables
        tables_to_check = ["users", "stores", "payment_types", "payments"]
        for table in tables_to_check:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table,),
            )
            if cursor.fetchone():
                print(f"Table '{table}' exists.")
            else:
                print(f"Table '{table}' does NOT exist.")
except sqlite3.Error as e:
    print(f"Database connection failed: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

if db.db_path.exists():
    print(f"Database file created at: {db.db_path}")
else:
    print(f"Database file was NOT created at: {db.db_path}")
