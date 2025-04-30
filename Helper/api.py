import json
import requests
from Helper.modal import db
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt
import sqlite3
from concurrent.futures import ThreadPoolExecutor


def load_icon(icon_path):
    """Loads an icon from the given path."""
    return QIcon(QPixmap(icon_path))


def load_image(image_url):
    """Loads a QPixmap image from a file path or URL."""
    pixmap = QPixmap()
    if image_url.startswith(("http://", "https://")):
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            image = QImage()
            image.loadFromData(response.content)
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
            else:
                print(
                    f"Failed to load image from URL: {image_url} - Invalid image data"
                )
        except requests.RequestException as e:
            print(f"Error loading image from URL {image_url}: {e}")
            return QPixmap()
    else:
        if not pixmap.load(image_url):
            print(f"Failed to load image from local path: {image_url}")
            return QPixmap()
    return pixmap


def get_item_groups_from_api():
    """Fetch all item groups from the API."""
    url = "https://c1.amali.japango.co.tz/api/v1/items/item_group"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        groups = [
            {"id": item["id"], "name": item["name"]}
            for item in data.get("data", [])
            if "id" in item and "name" in item
        ]
        print(f"Fetched {len(groups)} item groups")
        return groups
    except requests.RequestException as e:
        print(f"API request failed for item groups: {e}")
        return []


def get_all_categories_from_api():
    """Fetch all categories from the API in one call."""
    url = "https://c1.amali.japango.co.tz/api/v1/items/item_category"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        categories = [
            {
                "id": item["category_id"],
                "name": item["category_name"],
                "group_name": item.get("item_group_name"),
            }
            for item in data.get("data", [])
            if "category_id" in item and "category_name" in item
        ]
        print(f"Fetched {len(categories)} categories")
        return categories
    except requests.RequestException as e:
        print(f"API request failed for categories: {e}")
        return []


def fetch_items_for_category(category_id):
    """Fetch items for a specific category with error handling."""
    url = f"https://c1.amali.japango.co.tz/api/v1/items/sale_items?item_category_id={category_id}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        items_data = response.json()
        if not isinstance(items_data, list):
            print(f"Unexpected response for category {category_id}: {items_data}")
            return []
        items = [
            {
                "id": item["id"],
                "name": item.get("item_name", f"Unnamed Item {item['id']}"),
                "barcode": item.get("barcode", ""),
                "selling_unit": item.get("selling_unit", "Unit"),
                "buying_unit": item.get("buying_unit", "Unit"),
                "selling_unit_id": item.get("selling_unit_id", 23),
                "buying_unit_id": item.get("buying_unit_id", 23),
                "item_price": float(item.get("item_price", "0.0")),
                "item_cost": float(item.get("item_cost", "0.0")),
                "stock_quantity": float(item.get("stock_quantity", "0.0")),
                "category_id": category_id,
                "min_quantity": float(item.get("min_quantity", "0.0")),
                "max_quantity": float(item.get("max_quantity", "0.0")),
                "store_id": item.get("store_id", 1),
                "store_name": item.get("store_name", "Default Store"),
                "expire_date": item.get("expire_date"),
            }
            for item in items_data
            if "id" in item
        ]
        print(f"Fetched {len(items)} items for category {category_id}")
        return items
    except requests.RequestException as e:
        print(f"Failed to fetch items for category {category_id}: {e}")
        return []


def get_payments_from_api():
    """Fetch payment methods from the API."""
    url = "https://c1.amali.japango.co.tz/api/v1/payments/list"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        payments = [
            {
                "id": item["id"],
                "short_code": item["short_code"],
                "payment_method": item.get("payment_method"),
                "payment_type_id": item.get("payment_type_id"),
            }
            for item in data.get("data", [])
            if "id" in item and "short_code" in item
        ]
        print(f"Fetched {len(payments)} payments")
        return payments
    except requests.RequestException as e:
        print(f"API request failed for payments: {e}")
        return []


def get_customers_from_api():
    """Fetch customers from the API."""
    url = "https://c1.amali.japango.co.tz/api/v1/customers/list"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        customers = [
            {
                "id": item["id"],
                "customer_name": item["customer_name"],
                "active": item.get("active", 1),
            }
            for item in data.get("data", [])
            if "id" in item and "customer_name" in item
        ]
        print(f"Fetched {len(customers)} customers")
        return customers
    except requests.RequestException as e:
        print(f"API request failed for customers: {e}")
        return []


def get_customer_types_from_api():
    """Fetch customer types from the API."""
    url = "https://c1.amali.japango.co.tz/api/v1/customers/customer_type"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        customer_types = [
            {
                "id": item["id"],
                "name": item["name"],
                "is_active": item.get("is_active", 1),
            }
            for item in data.get("data", [])
            if "id" in item and "name" in item
        ]
        print(f"Fetched {len(customer_types)} customer types")
        return customer_types
    except requests.RequestException as e:
        print(f"API request failed for customer types: {e}")
        return []


def get_company_details_from_api():
    """Fetch company details from the API."""
    url = "https://c1.amali.japango.co.tz/api/v1/companies/company_details"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        companies_data = data.get("data", [])
        if not isinstance(companies_data, list):
            companies_data = [companies_data] if companies_data else []
        companies = [
            {
                "id": item.get("id"),
                "company_name": item.get("company_name"),
                "address": item.get("address"),
                "state": item.get("state"),
                "phone": item.get("phone"),
                "tin_no": item.get("tin_no"),
                "vrn_no": item.get("vrn_no"),
                "country_id": item.get("country_id"),
                "email": item.get("email"),
                "website": item.get("website"),
                "post_code": item.get("post_code"),
                "company_logo": item.get("company_logo"),
                "is_active": item.get("is_active", 1),
            }
            for item in companies_data
            if item.get("id") and item.get("company_name")
        ]
        print(f"Fetched {len(companies)} companies")
        return companies
    except requests.RequestException as e:
        print(f"API request failed for company details: {e}")
        return []


def get_units_from_api():
    """Fetch units from the API."""
    url = "https://c1.amali.japango.co.tz/api/v1/items/units"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        units = [
            {"id": item["id"], "name": item["name"]}
            for item in data.get("data", [])
            if "id" in item and "name" in item
        ]
        print(f"Fetched {len(units)} units")
        return units
    except requests.RequestException as e:
        print(f"API request failed for units: {e}")
        return []


def get_stores_from_api():
    """Fetch stores from the API."""
    url = (
        "https://c1.amali.japango.co.tz/api/v1/stores/list"  # Adjust this URL as needed
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        stores = [
            {"id": item["id"], "name": item["name"]}
            for item in data.get("data", [])
            if "id" in item and "name" in item
        ]
        print(f"Fetched {len(stores)} stores")
        return stores
    except requests.RequestException as e:
        print(f"API request failed for stores: {e}")
        return []


def sync_data_with_server():
    """Optimized synchronization of local database with server data."""
    try:
        # Step 0: Sync Units
        server_units = get_units_from_api()
        if not server_units:
            print("No units retrieved, inserting default unit")
            with db.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO units (id, name) VALUES (?, ?)",
                    (23, "Piece (PCS)"),
                )
                conn.commit()
        else:
            with db.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT OR IGNORE INTO units (id, name) VALUES (?, ?)",
                    [(u["id"], u["name"]) for u in server_units],
                )
                conn.commit()
                print(f"Synced {len(server_units)} units")

        # Step 1: Sync Stores
        server_stores = get_stores_from_api()
        if not server_stores:
            print("No stores retrieved, inserting default store")
            with db.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO stores (id, name, location, manager_id) VALUES (?, ?, ?, ?)",
                    (1, "MOHALAL SHOP", "Unknown", 1),  # Assuming manager_id 1 exists
                )
                conn.commit()
        else:
            with db.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT OR IGNORE INTO stores (id, name, location, manager_id) VALUES (?, ?, ?, ?)",
                    [
                        (s["id"], s["name"], "Unknown", 1) for s in server_stores
                    ],  # Default location and manager_id
                )
                conn.commit()
                print(f"Synced {len(server_stores)} stores")

        # Step 2: Sync Item Groups
        server_groups = get_item_groups_from_api()
        if not server_groups:
            print("No item groups retrieved, aborting sync")
            return False
        with db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO item_groups (id, name, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                [(g["id"], g["name"]) for g in server_groups],
            )
            conn.commit()
            cursor.execute("SELECT id, name FROM item_groups")
            group_mapping = {row["name"]: row["id"] for row in cursor.fetchall()}
            print(f"Synced {len(server_groups)} item groups")

        # Step 3: Sync All Categories
        server_categories = get_all_categories_from_api()
        if not server_categories:
            print("No categories retrieved, continuing with items sync")
        else:
            with db.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO categories (id, name, item_group_id, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    [
                        (c["id"], c["name"], group_mapping.get(c["group_name"]))
                        for c in server_categories
                    ],
                )
                conn.commit()
                print(f"Synced {len(server_categories)} categories")

        # Step 4: Fetch All Items Concurrently
        category_ids = [c["id"] for c in server_categories]
        all_server_items = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_category = {
                executor.submit(fetch_items_for_category, cid): cid
                for cid in category_ids
            }
            for future in future_to_category:
                items = future.result()
                all_server_items.extend(items)
        print(f"Fetched {len(all_server_items)} items from all categories")

        # Step 5: Sync Items Efficiently
        local_items = db.get_all_local_items()
        local_item_ids = {item["id"] for item in local_items}
        server_item_ids = {item["id"] for item in all_server_items}

        with db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Delete items not on server
            items_to_delete = local_item_ids - server_item_ids
            if items_to_delete:
                cursor.execute(
                    "DELETE FROM items WHERE id IN ({})".format(
                        ",".join("?" * len(items_to_delete))
                    ),
                    tuple(items_to_delete),
                )
                conn.commit()
                print(f"Deleted {len(items_to_delete)} local items not on server")

            # Prepare bulk insert/update
            items_to_insert = []
            items_to_update = []
            barcodes_to_insert = []
            item_barcodes_to_insert = []
            local_items_dict = {item["id"]: item for item in local_items}

            # Fetch existing stores, units, and barcodes for validation
            cursor.execute("SELECT id FROM stores")
            existing_stores = set(row["id"] for row in cursor.fetchall())
            cursor.execute("SELECT id FROM units")
            existing_units = set(row["id"] for row in cursor.fetchall())
            cursor.execute("SELECT code FROM barcodes")
            existing_barcodes = set(row["code"] for row in cursor.fetchall())

            for item in all_server_items:
                # Validate store_id and unit_ids
                if item["store_id"] not in existing_stores:
                    print(
                        f"Warning: Store ID {item['store_id']} not found, inserting default"
                    )
                    cursor.execute(
                        "INSERT OR IGNORE INTO stores (id, name, location, manager_id) VALUES (?, ?, ?, ?)",
                        (
                            item["store_id"],
                            item["store_name"] or f"Store {item['store_id']}",
                            "Unknown",
                            1,
                        ),
                    )
                    existing_stores.add(item["store_id"])
                if item["selling_unit_id"] not in existing_units:
                    print(
                        f"Warning: Selling Unit ID {item['selling_unit_id']} not found, inserting default"
                    )
                    cursor.execute(
                        "INSERT OR IGNORE INTO units (id, name) VALUES (?, ?)",
                        (
                            item["selling_unit_id"],
                            item["selling_unit"] or f"Unit {item['selling_unit_id']}",
                        ),
                    )
                    existing_units.add(item["selling_unit_id"])
                if item["buying_unit_id"] not in existing_units:
                    print(
                        f"Warning: Buying Unit ID {item['buying_unit_id']} not found, inserting default"
                    )
                    cursor.execute(
                        "INSERT OR IGNORE INTO units (id, name) VALUES (?, ?)",
                        (
                            item["buying_unit_id"],
                            item["buying_unit"] or f"Unit {item['buying_unit_id']}",
                        ),
                    )
                    existing_units.add(item["buying_unit_id"])

                # Handle barcode
                barcode = item.get("barcode", "").strip()
                if barcode and barcode not in existing_barcodes:
                    barcodes_to_insert.append((barcode,))
                    existing_barcodes.add(barcode)
                if barcode:
                    item_barcodes_to_insert.append((item["id"], barcode))

                local_item = local_items_dict.get(item["id"])
                server_item_data = {
                    "id": item["id"],
                    "name": item["name"],
                    "barcode": barcode,
                    "selling_unit": item["selling_unit"],
                    "buying_unit": item["buying_unit"],
                    "selling_unit_id": item["selling_unit_id"],
                    "buying_unit_id": item["buying_unit_id"],
                    "item_price": item["item_price"],
                    "item_cost": item["item_cost"],
                    "stock_quantity": item["stock_quantity"],
                    "category_id": item["category_id"],
                    "min_quantity": item["min_quantity"],
                    "max_quantity": item["max_quantity"],
                    "store_id": item["store_id"],
                    "store_name": item["store_name"],
                    "expire_date": item["expire_date"],
                }

                if not local_item:
                    items_to_insert.append(server_item_data)
                elif (
                    local_item["name"] != server_item_data["name"]
                    or local_item.get("barcode") != server_item_data["barcode"]
                    or local_item.get("selling_unit_name", "Unit")
                    != server_item_data["selling_unit"]
                    or local_item.get("buying_unit_name", "Unit")
                    != server_item_data["buying_unit"]
                    or local_item.get("prices", {}).get(
                        server_item_data["store_id"], 0.0
                    )
                    != server_item_data["item_price"]
                    or local_item.get("costs", {}).get(
                        server_item_data["store_id"], 0.0
                    )
                    != server_item_data["item_cost"]
                    or local_item.get("stocks", {}).get(
                        server_item_data["store_id"], {"stock_quantity": 0.0}
                    )["stock_quantity"]
                    != server_item_data["stock_quantity"]
                    or local_item.get("min_quantity", 0.0)
                    != server_item_data["min_quantity"]
                    or local_item.get("max_quantity", 0.0)
                    != server_item_data["max_quantity"]
                    or local_item.get("expire_date") != server_item_data["expire_date"]
                ):
                    items_to_update.append(server_item_data)

            # Bulk Insert Barcodes FIRST
            if barcodes_to_insert:
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO barcodes (code, created_at, updated_at)
                    VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    barcodes_to_insert,
                )
                print(f"Inserted {len(barcodes_to_insert)} new barcodes")

            # Bulk Insert Items SECOND
            if items_to_insert:
                cursor.executemany(
                    """
                    INSERT INTO items (id, name, category_id, item_type_id, expire_date, created_at, updated_at)
                    VALUES (?, ?, ?, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    [
                        (i["id"], i["name"], i["category_id"], i["expire_date"])
                        for i in items_to_insert
                    ],
                )
                cursor.executemany(
                    "INSERT INTO item_units (item_id, buying_unit_id, selling_unit_id) VALUES (?, ?, ?)",
                    [
                        (i["id"], i["buying_unit_id"], i["selling_unit_id"])
                        for i in items_to_insert
                    ],
                )
                cursor.executemany(
                    "INSERT INTO item_prices (item_id, store_id, unit_id, amount, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    [
                        (i["id"], i["store_id"], i["selling_unit_id"], i["item_price"])
                        for i in items_to_insert
                    ],
                )
                cursor.executemany(
                    "INSERT INTO item_costs (item_id, store_id, unit_id, amount, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    [
                        (i["id"], i["store_id"], i["buying_unit_id"], i["item_cost"])
                        for i in items_to_insert
                    ],
                )
                cursor.executemany(
                    "INSERT INTO stocks (item_id, store_id, min_quantity, max_quantity, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    [
                        (i["id"], i["store_id"], i["min_quantity"], i["max_quantity"])
                        for i in items_to_insert
                    ],
                )
                cursor.executemany(
                    """
                    INSERT INTO item_stocks (item_id, stock_id, stock_quantity, created_at, updated_at)
                    VALUES (?, (SELECT id FROM stocks WHERE item_id=? AND store_id=?), ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    [
                        (i["id"], i["id"], i["store_id"], i["stock_quantity"])
                        for i in items_to_insert
                    ],
                )
                print(f"Inserted {len(items_to_insert)} new items")

            # Bulk Insert Item-Barcodes THIRD
            if item_barcodes_to_insert:
                cursor.execute("SELECT code, id FROM barcodes")
                barcode_id_map = {row["code"]: row["id"] for row in cursor.fetchall()}
                item_barcodes_data = [
                    (item_id, barcode_id_map[barcode])
                    for item_id, barcode in item_barcodes_to_insert
                    if barcode in barcode_id_map and item_id in server_item_ids
                ]
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO item_barcodes (item_id, barcode_id, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    item_barcodes_data,
                )
                print(f"Linked {len(item_barcodes_data)} items to barcodes")

            # Bulk Update Items
            if items_to_update:
                cursor.executemany(
                    """
                    UPDATE items SET name=?, category_id=?, expire_date=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    [
                        (i["name"], i["category_id"], i["expire_date"], i["id"])
                        for i in items_to_update
                    ],
                )
                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO item_prices (item_id, store_id, unit_id, amount, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    [
                        (i["id"], i["store_id"], i["selling_unit_id"], i["item_price"])
                        for i in items_to_update
                    ],
                )
                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO item_costs (item_id, store_id, unit_id, amount, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    [
                        (i["id"], i["store_id"], i["buying_unit_id"], i["item_cost"])
                        for i in items_to_update
                    ],
                )
                cursor.executemany(
                    """
                    UPDATE stocks SET min_quantity=?, max_quantity=?, updated_at=CURRENT_TIMESTAMP
                    WHERE item_id=? AND store_id=?
                    """,
                    [
                        (i["min_quantity"], i["max_quantity"], i["id"], i["store_id"])
                        for i in items_to_update
                    ],
                )
                cursor.executemany(
                    """
                    UPDATE item_stocks SET stock_quantity=?, updated_at=CURRENT_TIMESTAMP
                    WHERE item_id=? AND stock_id=(SELECT id FROM stocks WHERE item_id=? AND store_id=?)
                    """,
                    [
                        (i["stock_quantity"], i["id"], i["id"], i["store_id"])
                        for i in items_to_update
                    ],
                )
                print(f"Updated {len(items_to_update)} existing items")

            conn.commit()

        # Sync Payments
        server_payments = get_payments_from_api()
        local_payments = db.get_all_local_payments()
        local_payment_ids = {p["id"] for p in local_payments}
        server_payment_ids = {p["id"] for p in server_payments}

        with db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            payments_to_delete = local_payment_ids - server_payment_ids
            if payments_to_delete:
                cursor.execute(
                    "DELETE FROM payments WHERE id IN ({})".format(
                        ",".join("?" * len(payments_to_delete))
                    ),
                    tuple(payments_to_delete),
                )
                conn.commit()
                print(f"Deleted {len(payments_to_delete)} local payments not on server")

            payments_to_insert = [
                p for p in server_payments if p["id"] not in local_payment_ids
            ]
            if payments_to_insert:
                cursor.executemany(
                    "INSERT INTO payments (id, short_code, payment_method, payment_type_id) VALUES (?, ?, ?, ?)",
                    [
                        (
                            p["id"],
                            p["short_code"],
                            p["payment_method"],
                            p["payment_type_id"],
                        )
                        for p in payments_to_insert
                    ],
                )
                conn.commit()
                print(f"Inserted {len(payments_to_insert)} new payments")

        # Sync Customers
        server_customers = get_customers_from_api()
        local_customers = db.get_all_local_customers()
        local_customer_ids = {c["id"] for c in local_customers}
        server_customer_ids = {c["id"] for c in server_customers}

        with db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            customers_to_delete = local_customer_ids - server_customer_ids
            if customers_to_delete:
                cursor.execute(
                    "DELETE FROM customers WHERE id IN ({})".format(
                        ",".join("?" * len(customers_to_delete))
                    ),
                    tuple(customers_to_delete),
                )
                conn.commit()
                print(
                    f"Deleted {len(customers_to_delete)} local customers not on server"
                )

            customers_to_insert = [
                c for c in server_customers if c["id"] not in local_customer_ids
            ]
            if customers_to_insert:
                cursor.executemany(
                    "INSERT INTO customers (id, customer_name, active) VALUES (?, ?, ?)",
                    [
                        (c["id"], c["customer_name"], c["active"])
                        for c in customers_to_insert
                    ],
                )
                conn.commit()
                print(f"Inserted {len(customers_to_insert)} new customers")

        # Sync Customer Types
        server_customer_types = get_customer_types_from_api()
        local_customer_types = db.get_all_local_customer_types()
        local_customer_type_ids = {ct["id"] for ct in local_customer_types}
        server_customer_type_ids = {ct["id"] for ct in server_customer_types}

        with db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            customer_types_to_delete = (
                local_customer_type_ids - server_customer_type_ids
            )
            if customer_types_to_delete:
                cursor.execute(
                    "DELETE FROM customer_types WHERE id IN ({})".format(
                        ",".join("?" * len(customer_types_to_delete))
                    ),
                    tuple(customer_types_to_delete),
                )
                conn.commit()
                print(
                    f"Deleted {len(customer_types_to_delete)} local customer types not on server"
                )

            customer_types_to_insert = [
                ct
                for ct in server_customer_types
                if ct["id"] not in local_customer_type_ids
            ]
            if customer_types_to_insert:
                cursor.executemany(
                    "INSERT INTO customer_types (id, name, is_active) VALUES (?, ?, ?)",
                    [
                        (ct["id"], ct["name"], ct["is_active"])
                        for ct in customer_types_to_insert
                    ],
                )
                conn.commit()
                print(f"Inserted {len(customer_types_to_insert)} new customer types")

        # Sync Company Details
        server_companies = get_company_details_from_api()
        local_companies = db.get_all_local_companies()
        local_company_ids = {c["id"] for c in local_companies if c["id"] is not None}
        server_company_ids = {c["id"] for c in server_companies if c["id"] is not None}

        with db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            companies_to_delete = local_company_ids - server_company_ids
            if companies_to_delete:
                cursor.execute(
                    "DELETE FROM companies WHERE id IN ({})".format(
                        ",".join("?" * len(companies_to_delete))
                    ),
                    tuple(companies_to_delete),
                )
                conn.commit()
                print(
                    f"Deleted {len(companies_to_delete)} local companies not on server"
                )

            companies_to_insert = [
                c for c in server_companies if c["id"] not in local_company_ids
            ]
            if companies_to_insert:
                cursor.executemany(
                    """
                    INSERT INTO companies (id, company_name, address, state, phone, tin_no, vrn_no, country_id, email, website, post_code, company_logo, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            c["id"],
                            c["company_name"],
                            c["address"],
                            c["state"],
                            c["phone"],
                            c["tin_no"],
                            c["vrn_no"],
                            c["country_id"],
                            c["email"],
                            c["website"],
                            c["post_code"],
                            c["company_logo"],
                            c["is_active"],
                        )
                        for c in companies_to_insert
                    ],
                )
                conn.commit()
                print(f"Inserted {len(companies_to_insert)} new companies")

        print(
            f"Synchronization completed: {len(all_server_items)} items synced along with payments, customers, customer types, and companies"
        )
        return True
    except Exception as e:
        print(f"Sync error: {e}")
        import traceback

        traceback.print_exc()
        return False


# def sync_data_with_server(force_full_sync=True):
#     """Optimized synchronization of local database with server data.

#     Args:
#         force_full_sync (bool): If True, perform full sync including deletions.
#                                If False, only insert/update, preserving local changes.
#     """
#     try:
#         # Step 0: Sync Units
#         server_units = get_units_from_api()
#         if not server_units:
#             print("No units retrieved, inserting default unit")
#             with db.get_connection() as conn:
#                 conn.row_factory = sqlite3.Row
#                 cursor = conn.cursor()
#                 cursor.execute(
#                     "INSERT OR IGNORE INTO units (id, name) VALUES (?, ?)",
#                     (23, "Piece (PCS)"),
#                 )
#                 conn.commit()
#         else:
#             with db.get_connection() as conn:
#                 conn.row_factory = sqlite3.Row
#                 cursor = conn.cursor()
#                 cursor.executemany(
#                     "INSERT OR IGNORE INTO units (id, name) VALUES (?, ?)",
#                     [(u["id"], u["name"]) for u in server_units],
#                 )
#                 conn.commit()
#                 print(f"Synced {len(server_units)} units")

#         # Step 1: Sync Stores
#         server_stores = get_stores_from_api()
#         if not server_stores:
#             print("No stores retrieved, inserting default store")
#             with db.get_connection() as conn:
#                 conn.row_factory = sqlite3.Row
#                 cursor = conn.cursor()
#                 cursor.execute(
#                     "INSERT OR IGNORE INTO stores (id, name, location, manager_id) VALUES (?, ?, ?, ?)",
#                     (1, "MOHALAL SHOP", "Unknown", 1),
#                 )
#                 conn.commit()
#         else:
#             with db.get_connection() as conn:
#                 conn.row_factory = sqlite3.Row
#                 cursor = conn.cursor()
#                 cursor.executemany(
#                     "INSERT OR IGNORE INTO stores (id, name, location, manager_id) VALUES (?, ?, ?, ?)",
#                     [(s["id"], s["name"], "Unknown", 1) for s in server_stores],
#                 )
#                 conn.commit()
#                 print(f"Synced {len(server_stores)} stores")

#         # Step 2: Sync Item Groups
#         server_groups = get_item_groups_from_api()
#         if not server_groups:
#             print("No item groups retrieved, aborting sync")
#             return False
#         with db.get_connection() as conn:
#             conn.row_factory = sqlite3.Row
#             cursor = conn.cursor()
#             cursor.executemany(
#                 "INSERT OR IGNORE INTO item_groups (id, name, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
#                 [(g["id"], g["name"]) for g in server_groups],
#             )
#             conn.commit()
#             cursor.execute("SELECT id, name FROM item_groups")
#             group_mapping = {row["name"]: row["id"] for row in cursor.fetchall()}
#             print(f"Synced {len(server_groups)} item groups")

#         # Step 3: Sync All Categories
#         server_categories = get_all_categories_from_api()
#         if not server_categories:
#             print("No categories retrieved, continuing with items sync")
#         else:
#             with db.get_connection() as conn:
#                 conn.row_factory = sqlite3.Row
#                 cursor = conn.cursor()
#                 cursor.executemany(
#                     """
#                     INSERT OR IGNORE INTO categories (id, name, item_group_id, created_at)
#                     VALUES (?, ?, ?, CURRENT_TIMESTAMP)
#                     """,
#                     [
#                         (c["id"], c["name"], group_mapping.get(c["group_name"]))
#                         for c in server_categories
#                     ],
#                 )
#                 conn.commit()
#                 print(f"Synced {len(server_categories)} categories")

#         # Step 4: Fetch All Items Concurrently
#         category_ids = [c["id"] for c in server_categories]
#         all_server_items = []
#         with ThreadPoolExecutor(max_workers=10) as executor:
#             future_to_category = {
#                 executor.submit(fetch_items_for_category, cid): cid
#                 for cid in category_ids
#             }
#             for future in future_to_category:
#                 items = future.result()
#                 all_server_items.extend(items)
#         print(f"Fetched {len(all_server_items)} items from all categories")

#         # Step 5: Sync Items Efficiently
#         local_items = db.get_all_local_items()
#         local_item_ids = {item["id"] for item in local_items}
#         server_item_ids = {item["id"] for item in all_server_items}

#         with db.get_connection() as conn:
#             conn.row_factory = sqlite3.Row
#             cursor = conn.cursor()

#             # Only delete local items not on server if force_full_sync is True
#             if force_full_sync:
#                 items_to_delete = local_item_ids - server_item_ids
#                 if items_to_delete:
#                     cursor.execute(
#                         "DELETE FROM items WHERE id IN ({})".format(
#                             ",".join("?" * len(items_to_delete))
#                         ),
#                         tuple(items_to_delete),
#                     )
#                     conn.commit()
#                     print(f"Deleted {len(items_to_delete)} local items not on server")
#             else:
#                 print(
#                     "Sync toggle OFF: Skipping deletion of local items to preserve changes"
#                 )

#             # Prepare bulk insert/update
#             items_to_insert = []
#             items_to_update = []
#             barcodes_to_insert = []
#             item_barcodes_to_insert = []
#             local_items_dict = {item["id"]: item for item in local_items}

#             # Fetch existing stores, units, and barcodes for validation
#             cursor.execute("SELECT id FROM stores")
#             existing_stores = set(row["id"] for row in cursor.fetchall())
#             cursor.execute("SELECT id FROM units")
#             existing_units = set(row["id"] for row in cursor.fetchall())
#             cursor.execute("SELECT code FROM barcodes")
#             existing_barcodes = set(row["code"] for row in cursor.fetchall())

#             for item in all_server_items:
#                 # Validate store_id and unit_ids
#                 if item["store_id"] not in existing_stores:
#                     print(
#                         f"Warning: Store ID {item['store_id']} not found, inserting default"
#                     )
#                     cursor.execute(
#                         "INSERT OR IGNORE INTO stores (id, name, location, manager_id) VALUES (?, ?, ?, ?)",
#                         (
#                             item["store_id"],
#                             item["store_name"] or f"Store {item['store_id']}",
#                             "Unknown",
#                             1,
#                         ),
#                     )
#                     existing_stores.add(item["store_id"])
#                 if item["selling_unit_id"] not in existing_units:
#                     print(
#                         f"Warning: Selling Unit ID {item['selling_unit_id']} not found, inserting default"
#                     )
#                     cursor.execute(
#                         "INSERT OR IGNORE INTO units (id, name) VALUES (?, ?)",
#                         (
#                             item["selling_unit_id"],
#                             item["selling_unit"] or f"Unit {item['selling_unit_id']}",
#                         ),
#                     )
#                     existing_units.add(item["selling_unit_id"])
#                 if item["buying_unit_id"] not in existing_units:
#                     print(
#                         f"Warning: Buying Unit ID {item['buying_unit_id']} not found, inserting default"
#                     )
#                     cursor.execute(
#                         "INSERT OR IGNORE INTO units (id, name) VALUES (?, ?)",
#                         (
#                             item["buying_unit_id"],
#                             item["buying_unit"] or f"Unit {item['buying_unit_id']}",
#                         ),
#                     )
#                     existing_units.add(item["buying_unit_id"])

#                 # Handle barcode
#                 barcode = item.get("barcode", "").strip()
#                 if barcode and barcode not in existing_barcodes:
#                     barcodes_to_insert.append((barcode,))
#                     existing_barcodes.add(barcode)
#                 if barcode:
#                     item_barcodes_to_insert.append((item["id"], barcode))

#                 local_item = local_items_dict.get(item["id"])
#                 server_item_data = {
#                     "id": item["id"],
#                     "name": item["name"],
#                     "barcode": barcode,
#                     "selling_unit": item["selling_unit"],
#                     "buying_unit": item["buying_unit"],
#                     "selling_unit_id": item["selling_unit_id"],
#                     "buying_unit_id": item["buying_unit_id"],
#                     "item_price": item["item_price"],
#                     "item_cost": item["item_cost"],
#                     "stock_quantity": item["stock_quantity"],
#                     "category_id": item["category_id"],
#                     "min_quantity": item["min_quantity"],
#                     "max_quantity": item["max_quantity"],
#                     "store_id": item["store_id"],
#                     "store_name": item["store_name"],
#                     "expire_date": item["expire_date"],
#                 }

#                 if not local_item:
#                     items_to_insert.append(server_item_data)
#                 elif (
#                     local_item["name"] != server_item_data["name"]
#                     or local_item.get("barcode") != server_item_data["barcode"]
#                     or local_item.get("selling_unit_name", "Unit")
#                     != server_item_data["selling_unit"]
#                     or local_item.get("buying_unit_name", "Unit")
#                     != server_item_data["buying_unit"]
#                     or local_item.get("prices", {}).get(
#                         server_item_data["store_id"], 0.0
#                     )
#                     != server_item_data["item_price"]
#                     or local_item.get("costs", {}).get(
#                         server_item_data["store_id"], 0.0
#                     )
#                     != server_item_data["item_cost"]
#                     or local_item.get("stocks", {}).get(
#                         server_item_data["store_id"], {"stock_quantity": 0.0}
#                     )["stock_quantity"]
#                     != server_item_data["stock_quantity"]
#                     or local_item.get("min_quantity", 0.0)
#                     != server_item_data["min_quantity"]
#                     or local_item.get("max_quantity", 0.0)
#                     != server_item_data["max_quantity"]
#                     or local_item.get("expire_date") != server_item_data["expire_date"]
#                 ):
#                     items_to_update.append(server_item_data)

#             # Bulk Insert Barcodes FIRST
#             if barcodes_to_insert:
#                 cursor.executemany(
#                     """
#                     INSERT OR IGNORE INTO barcodes (code, created_at, updated_at)
#                     VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#                     """,
#                     barcodes_to_insert,
#                 )
#                 print(f"Inserted {len(barcodes_to_insert)} new barcodes")

#             # Bulk Insert Items SECOND
#             if items_to_insert:
#                 cursor.executemany(
#                     """
#                     INSERT INTO items (id, name, category_id, item_type_id, expire_date, created_at, updated_at)
#                     VALUES (?, ?, ?, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#                     """,
#                     [
#                         (i["id"], i["name"], i["category_id"], i["expire_date"])
#                         for i in items_to_insert
#                     ],
#                 )
#                 cursor.executemany(
#                     "INSERT INTO item_units (item_id, buying_unit_id, selling_unit_id) VALUES (?, ?, ?)",
#                     [
#                         (i["id"], i["buying_unit_id"], i["selling_unit_id"])
#                         for i in items_to_insert
#                     ],
#                 )
#                 cursor.executemany(
#                     "INSERT INTO item_prices (item_id, store_id, unit_id, amount, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
#                     [
#                         (i["id"], i["store_id"], i["selling_unit_id"], i["item_price"])
#                         for i in items_to_insert
#                     ],
#                 )
#                 cursor.executemany(
#                     "INSERT INTO item_costs (item_id, store_id, unit_id, amount, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
#                     [
#                         (i["id"], i["store_id"], i["buying_unit_id"], i["item_cost"])
#                         for i in items_to_insert
#                     ],
#                 )
#                 cursor.executemany(
#                     "INSERT INTO stocks (item_id, store_id, min_quantity, max_quantity, created_at, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
#                     [
#                         (i["id"], i["store_id"], i["min_quantity"], i["max_quantity"])
#                         for i in items_to_insert
#                     ],
#                 )
#                 cursor.executemany(
#                     """
#                     INSERT INTO item_stocks (item_id, stock_id, stock_quantity, created_at, updated_at)
#                     VALUES (?, (SELECT id FROM stocks WHERE item_id=? AND store_id=?), ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#                     """,
#                     [
#                         (i["id"], i["id"], i["store_id"], i["stock_quantity"])
#                         for i in items_to_insert
#                     ],
#                 )
#                 print(f"Inserted {len(items_to_insert)} new items")

#             # Bulk Insert Item-Barcodes THIRD
#             if item_barcodes_to_insert:
#                 cursor.execute("SELECT code, id FROM barcodes")
#                 barcode_id_map = {row["code"]: row["id"] for row in cursor.fetchall()}
#                 item_barcodes_data = [
#                     (item_id, barcode_id_map[barcode])
#                     for item_id, barcode in item_barcodes_to_insert
#                     if barcode in barcode_id_map and item_id in server_item_ids
#                 ]
#                 cursor.executemany(
#                     """
#                     INSERT OR IGNORE INTO item_barcodes (item_id, barcode_id, created_at, updated_at)
#                     VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#                     """,
#                     item_barcodes_data,
#                 )
#                 print(f"Linked {len(item_barcodes_data)} items to barcodes")

#             # Bulk Update Items
#             if items_to_update:
#                 cursor.executemany(
#                     """
#                     UPDATE items SET name=?, category_id=?, expire_date=?, updated_at=CURRENT_TIMESTAMP
#                     WHERE id=?
#                     """,
#                     [
#                         (i["name"], i["category_id"], i["expire_date"], i["id"])
#                         for i in items_to_update
#                     ],
#                 )
#                 cursor.executemany(
#                     """
#                     INSERT OR REPLACE INTO item_prices (item_id, store_id, unit_id, amount, created_at, updated_at)
#                     VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
#                     """,
#                     [
#                         (i["id"], i["store_id"], i["selling_unit_id"], i["item_price"])
#                         for i in items_to_update
#                     ],
#                 )
#                 cursor.executemany(
#                     """
#                     INSERT OR REPLACE INTO item_costs (item_id, store_id, unit_id, amount, created_at)
#                     VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
#                     """,
#                     [
#                         (i["id"], i["store_id"], i["buying_unit_id"], i["item_cost"])
#                         for i in items_to_update
#                     ],
#                 )
#                 cursor.executemany(
#                     """
#                     UPDATE stocks SET min_quantity=?, max_quantity=?, updated_at=CURRENT_TIMESTAMP
#                     WHERE item_id=? AND store_id=?
#                     """,
#                     [
#                         (i["min_quantity"], i["max_quantity"], i["id"], i["store_id"])
#                         for i in items_to_update
#                     ],
#                 )
#                 cursor.executemany(
#                     """
#                     UPDATE item_stocks SET stock_quantity=?, updated_at=CURRENT_TIMESTAMP
#                     WHERE item_id=? AND stock_id=(SELECT id FROM stocks WHERE item_id=? AND store_id=?)
#                     """,
#                     [
#                         (i["stock_quantity"], i["id"], i["id"], i["store_id"])
#                         for i in items_to_update
#                     ],
#                 )
#                 print(f"Updated {len(items_to_update)} existing items")

#             conn.commit()

#         # Sync Payments (skip deletion if not force_full_sync)
#         server_payments = get_payments_from_api()
#         local_payments = db.get_all_local_payments()
#         local_payment_ids = {p["id"] for p in local_payments}
#         server_payment_ids = {p["id"] for p in server_payments}

#         with db.get_connection() as conn:
#             conn.row_factory = sqlite3.Row
#             cursor = conn.cursor()
#             if force_full_sync:
#                 payments_to_delete = local_payment_ids - server_payment_ids
#                 if payments_to_delete:
#                     cursor.execute(
#                         "DELETE FROM payments WHERE id IN ({})".format(
#                             ",".join("?" * len(payments_to_delete))
#                         ),
#                         tuple(payments_to_delete),
#                     )
#                     conn.commit()
#                     print(
#                         f"Deleted {len(payments_to_delete)} local payments not on server"
#                     )
#             else:
#                 print("Sync toggle OFF: Skipping deletion of local payments")

#             payments_to_insert = [
#                 p for p in server_payments if p["id"] not in local_payment_ids
#             ]
#             if payments_to_insert:
#                 cursor.executemany(
#                     "INSERT INTO payments (id, short_code, payment_method, payment_type_id) VALUES (?, ?, ?, ?)",
#                     [
#                         (
#                             p["id"],
#                             p["short_code"],
#                             p["payment_method"],
#                             p["payment_type_id"],
#                         )
#                         for p in payments_to_insert
#                     ],
#                 )
#                 conn.commit()
#                 print(f"Inserted {len(payments_to_insert)} new payments")

#         # Sync Customers (skip deletion if not force_full_sync)
#         server_customers = get_customers_from_api()
#         local_customers = db.get_all_local_customers()
#         local_customer_ids = {c["id"] for c in local_customers}
#         server_customer_ids = {c["id"] for c in server_customers}

#         with db.get_connection() as conn:
#             conn.row_factory = sqlite3.Row
#             cursor = conn.cursor()
#             if force_full_sync:
#                 customers_to_delete = local_customer_ids - server_customer_ids
#                 if customers_to_delete:
#                     cursor.execute(
#                         "DELETE FROM customers WHERE id IN ({})".format(
#                             ",".join("?" * len(customers_to_delete))
#                         ),
#                         tuple(customers_to_delete),
#                     )
#                     conn.commit()
#                     print(
#                         f"Deleted {len(customers_to_delete)} local customers not on server"
#                     )
#             else:
#                 print("Sync toggle OFF: Skipping deletion of local customers")

#             customers_to_insert = [
#                 c for c in server_customers if c["id"] not in local_customer_ids
#             ]
#             if customers_to_insert:
#                 cursor.executemany(
#                     "INSERT INTO customers (id, customer_name, active) VALUES (?, ?, ?)",
#                     [
#                         (c["id"], c["customer_name"], c["active"])
#                         for c in customers_to_insert
#                     ],
#                 )
#                 conn.commit()
#                 print(f"Inserted {len(customers_to_insert)} new customers")

#         # Sync Customer Types (skip deletion if not force_full_sync)
#         server_customer_types = get_customer_types_from_api()
#         local_customer_types = db.get_all_local_customer_types()
#         local_customer_type_ids = {ct["id"] for ct in local_customer_types}
#         server_customer_type_ids = {ct["id"] for ct in server_customer_types}

#         with db.get_connection() as conn:
#             conn.row_factory = sqlite3.Row
#             cursor = conn.cursor()
#             if force_full_sync:
#                 customer_types_to_delete = (
#                     local_customer_type_ids - server_customer_type_ids
#                 )
#                 if customer_types_to_delete:
#                     cursor.execute(
#                         "DELETE FROM customer_types WHERE id IN ({})".format(
#                             ",".join("?" * len(customer_types_to_delete))
#                         ),
#                         tuple(customer_types_to_delete),
#                     )
#                     conn.commit()
#                     print(
#                         f"Deleted {len(customer_types_to_delete)} local customer types not on server"
#                     )
#             else:
#                 print("Sync toggle OFF: Skipping deletion of local customer types")

#             customer_types_to_insert = [
#                 ct
#                 for ct in server_customer_types
#                 if ct["id"] not in local_customer_type_ids
#             ]
#             if customer_types_to_insert:
#                 cursor.executemany(
#                     "INSERT INTO customer_types (id, name, is_active) VALUES (?, ?, ?)",
#                     [
#                         (ct["id"], ct["name"], ct["is_active"])
#                         for ct in customer_types_to_insert
#                     ],
#                 )
#                 conn.commit()
#                 print(f"Inserted {len(customer_types_to_insert)} new customer types")

#         # Sync Company Details (skip deletion if not force_full_sync)
#         server_companies = get_company_details_from_api()
#         local_companies = db.get_all_local_companies()
#         local_company_ids = {c["id"] for c in local_companies if c["id"] is not None}
#         server_company_ids = {c["id"] for c in server_companies if c["id"] is not None}

#         with db.get_connection() as conn:
#             conn.row_factory = sqlite3.Row
#             cursor = conn.cursor()
#             if force_full_sync:
#                 companies_to_delete = local_company_ids - server_company_ids
#                 if companies_to_delete:
#                     cursor.execute(
#                         "DELETE FROM companies WHERE id IN ({})".format(
#                             ",".join("?" * len(companies_to_delete))
#                         ),
#                         tuple(companies_to_delete),
#                     )
#                     conn.commit()
#                     print(
#                         f"Deleted {len(companies_to_delete)} local companies not on server"
#                     )
#             else:
#                 print("Sync toggle OFF: Skipping deletion of local companies")

#             companies_to_insert = [
#                 c for c in server_companies if c["id"] not in local_company_ids
#             ]
#             if companies_to_insert:
#                 cursor.executemany(
#                     """
#                     INSERT INTO companies (id, company_name, address, state, phone, tin_no, vrn_no, country_id, email, website, post_code, company_logo, is_active)
#                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                     """,
#                     [
#                         (
#                             c["id"],
#                             c["company_name"],
#                             c["address"],
#                             c["state"],
#                             c["phone"],
#                             c["tin_no"],
#                             c["vrn_no"],
#                             c["country_id"],
#                             c["email"],
#                             c["website"],
#                             c["post_code"],
#                             c["company_logo"],
#                             c["is_active"],
#                         )
#                         for c in companies_to_insert
#                     ],
#                 )
#                 conn.commit()
#                 print(f"Inserted {len(companies_to_insert)} new companies")

#         print(
#             f"Synchronization completed: {len(all_server_items)} items synced along with payments, customers, customer types, and companies"
#             f"{' (Full Sync)' if force_full_sync else ' (Partial Sync - Local Preserved)'}"
#         )
#         return True
#     except Exception as e:
#         print(f"Sync error: {e}")
#         import traceback

#         traceback.print_exc()
#         return False


def post_order_to_server(order_data):
    """Post order data to the server API."""
    url = "https://c1.amali.japango.co.tz/api/v1/orders/store_local_sale"
    headers = {"Content-Type": "application/json"}
    payload = {
        "customer_type_id": order_data["customer_type_id"],
        "customer_id": order_data["customer_id"],
        "payment_id": order_data["payment_id"],
        "total_amount": order_data["total_amount"],
        "tip": order_data["tip"],
        "discount": order_data["discount"],
        "items": [
            {
                "item_id": item["item_id"],
                "quantity": item["quantity"],
                "price": item["price"],
            }
            for item in order_data["items"]
        ],
    }
    try:
        response = requests.post(
            url, data=json.dumps(payload), headers=headers, timeout=10
        )
        response.raise_for_status()
        server_response = response.json()
        print(f"Order posted successfully: {server_response}")
        return server_response
    except requests.RequestException as e:
        print(f"Failed to post order to server: {e}")
        return None


def update_server_stock(stock_changes):
    """Update server-side item stocks."""
    url = "https://c1.amali.japango.co.tz/api/v1/stocks/update"
    headers = {"Content-Type": "application/json"}
    payload = {
        "stock_updates": [
            {"item_id": change["item_id"], "new_quantity": change["new_quantity"]}
            for change in stock_changes
        ]
    }
    try:
        response = requests.post(
            url, data=json.dumps(payload), headers=headers, timeout=10
        )
        response.raise_for_status()
        server_response = response.json()
        print(f"Stock updated on server: {server_response}")
        return server_response
    except requests.RequestException as e:
        print(f"Failed to update stock on server: {e}")
        return None


def save_and_sync_stock(order_data, items, payment_id, customer_id):
    """Save order locally and sync stock changes with server."""
    result = db.save_order(order_data, items, payment_id, customer_id)
    if not result:
        print("Failed to save order locally, aborting stock sync")
        return False

    order_id = result["order_id"]
    stock_changes = result["stock_changes"]
    server_response = update_server_stock(stock_changes)
    if server_response and server_response.get("success", True):
        print(f"Order {order_id} saved locally and stock synced with server")
        return True
    print(f"Order {order_id} saved locally but failed to sync stock")
    return False


def save_and_sync_order(order_data, items, payment_id, customer_id):
    """Save order locally and sync with server."""
    saved_order = db.save_order(order_data, items, payment_id, customer_id)
    if not saved_order:
        print("Failed to save order locally, aborting sync")
        return False

    server_response = post_order_to_server(saved_order)
    if server_response and server_response.get("success"):
        print(f"Order {saved_order['order_id']} synced with server")
        return True
    print(f"Order {saved_order['order_id']} saved locally but failed to sync")
    return False


def post_new_item_to_api(item_data):
    """Post a new item to the API."""
    url = "https://c1.amali.japango.co.tz/api/v1/items/sale_items"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            url, data=json.dumps(item_data), headers=headers, timeout=10
        )
        response.raise_for_status()
        print("Item posted successfully:", response.json())
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to post item: {e}")
        return None


if __name__ == "__main__":
    sync_data_with_server()
