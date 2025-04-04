import json
import requests
from Helper.modal import db
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt


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
        except requests.exceptions.RequestException as e:
            print(f"Error loading image from URL {image_url}: {e}")
            return QPixmap()
    else:
        if not pixmap.load(image_url):
            print(f"Failed to load image from local path: {image_url}")
            return QPixmap()
    return pixmap


def get_item_groups_from_api():
    url = "https://c1.amali.japango.co.tz/api/v1/items/item_group"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        groups_data = data.get("data", [])
        groups = [
            {"id": item["id"], "name": item["name"]}
            for item in groups_data
            if "id" in item and "name" in item
        ]
        print(f"Fetched {len(groups)} item groups: {[g['name'] for g in groups]}")
        return groups
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for item groups: {req_err}")
        return []


def get_categories_for_group(group_name):
    url = "https://c1.amali.japango.co.tz/api/v1/items/item_category"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        categories_data = data.get("data", [])
        categories = [
            {"id": item["category_id"], "name": item["category_name"]}
            for item in categories_data
            if item.get("item_group_name") == group_name
            and "category_id" in item
            and "category_name" in item
        ]
        print(
            f"Fetched {len(categories)} categories for group {group_name}: {categories}"
        )
        return categories
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for categories: {req_err}")
        return []


def get_items_by_category_from_api(category_id):
    """Fetch items for a specific category from the server."""
    url = f"https://c1.amali.japango.co.tz/api/v1/items/sale_items?item_category_id={category_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        items_data = response.json()
        if isinstance(items_data, dict) and "error" in items_data:
            print(f"API error: {items_data['error']}")
            return []
        items = [
            {
                "id": item["id"],
                "name": item["item_name"],
                "barcode": item.get("barcode"),  # Fetch barcode from API
                "item_unit": item.get("item_unit", "Unit"),
                "item_price": float(item.get("item_price", 0.0)),
                "stock_quantity": float(item.get("stock_quantity", 0.0)),
                "image_url": item.get("image_url", ""),
                "category_id": category_id,
            }
            for item in items_data
            if "id" in item and "item_name" in item
        ]
        print(
            f"Fetched {len(items)} items for category {category_id}: {[item['name'] for item in items]}"
        )
        return items
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for items in category {category_id}: {req_err}")
        return []


def get_payments_from_api():
    url = "https://c1.amali.japango.co.tz/api/v1/payments/list"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"Raw payments API response: {data}")  # Debug log
        payments_data = data.get("data", [])
        payments = [
            {
                "id": item["id"],
                "short_code": item["short_code"],
                "payment_method": item.get("payment_method"),  # Allow None
                "payment_type_id": item.get("payment_type_id"),
            }
            for item in payments_data
            if "id" in item and "short_code" in item
        ]
        print(
            f"Fetched {len(payments)} payments: {[p['short_code'] for p in payments]}"
        )
        return payments
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for payments: {req_err}")
        return []


def get_customers_from_api():
    url = "https://c1.amali.japango.co.tz/api/v1/customers/list"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        customers_data = data.get("data", [])
        customers = [
            {
                "id": item["id"],
                "customer_name": item["customer_name"],
                "active": item.get("active", 1),
            }
            for item in customers_data
            if "id" in item and "customer_name" in item
        ]
        print(
            f"Fetched {len(customers)} customers: {[c['customer_name'] for c in customers]}"
        )
        return customers
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for customers: {req_err}")
        return []


def get_customer_types_from_api():
    url = "https://c1.amali.japango.co.tz/api/v1/customers/customer_type"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        customer_types_data = data.get("data", [])
        customer_types = [
            {
                "id": item["id"],
                "name": item["name"],
                "is_active": item.get("is_active", 1),
            }
            for item in customer_types_data
            if "id" in item and "name" in item
        ]
        print(
            f"Fetched {len(customer_types)} customer types: {[ct['name'] for ct in customer_types]}"
        )
        return customer_types
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for customer types: {req_err}")
        return []


def sync_items_by_category(category_id):
    """Synchronize local database with server items for a specific category."""
    try:
        server_items = get_items_by_category_from_api(category_id)
        if not server_items:
            print(f"No items fetched for category {category_id}")
            return False

        local_items = db.get_all_local_items()
        local_items_filtered = [
            item for item in local_items if item["category_id"] == category_id
        ]
        local_item_ids = {item["id"] for item in local_items_filtered}
        server_item_ids = {item["id"] for item in server_items}

        with db.get_connection() as conn:
            cursor = conn.cursor()
            items_to_delete = local_item_ids - server_item_ids
            if items_to_delete:
                cursor.execute(
                    "DELETE FROM items WHERE id IN ({}) AND category_id = ?".format(
                        ",".join("?" * len(items_to_delete))
                    ),
                    tuple(items_to_delete) + (category_id,),
                )
                cursor.execute(
                    "DELETE FROM item_units WHERE item_id IN ({})".format(
                        ",".join("?" * len(items_to_delete))
                    ),
                    tuple(items_to_delete),
                )
                cursor.execute(
                    "DELETE FROM item_prices WHERE item_id IN ({})".format(
                        ",".join("?" * len(items_to_delete))
                    ),
                    tuple(items_to_delete),
                )
                cursor.execute(
                    "DELETE FROM item_stocks WHERE item_id IN ({})".format(
                        ",".join("?" * len(items_to_delete))
                    ),
                    tuple(items_to_delete),
                )
                conn.commit()
                print(
                    f"Deleted {len(items_to_delete)} items for category {category_id}: {items_to_delete}"
                )

        for item in server_items:
            local_item = next(
                (li for li in local_items_filtered if li["id"] == item["id"]), None
            )
            if not local_item:
                db.insert_item(
                    item["id"],
                    item["name"],
                    item["barcode"],
                    item["item_unit"],
                    item["item_price"],
                    item["stock_quantity"],
                    item["category_id"],
                )
                print(
                    f"Inserted item {item['id']} ({item['name']}) for category {category_id}"
                )
            else:
                # Compare fields and update if necessary
                local_unit = local_item.get("selling_unit_name", "Unit")
                local_price = local_item.get("prices", {}).get(1, 0.0)
                local_stock = local_item.get("stocks", {}).get(
                    1, {"stock_quantity": 0.0}
                )["stock_quantity"]
                local_barcode = local_item.get("barcode", "")

                if (
                    local_item["name"] != item["name"]
                    or local_unit != item["item_unit"]
                    or local_price != item["item_price"]
                    or local_stock != item["stock_quantity"]
                    or local_barcode != item["barcode"]
                ):
                    db.update_item(
                        item["id"],
                        item["name"],
                        item["barcode"],
                        item["category_id"],
                        1,  # Default item_type_id
                        None,  # item_group_id not provided
                        None,  # exprire_date not provided
                        item["item_unit"],  # buying_unit_name
                        item["item_unit"],  # selling_unit_name
                        {1: item["item_price"]},  # price_dict
                        {
                            1: {
                                "stock_quantity": item["stock_quantity"],
                                "min_quantity": 0.0,
                                "max_quantity": 0.0,
                            }
                        },  # stock_dict
                    )
                    print(
                        f"Updated item {item['id']} ({item['name']}) for category {category_id}"
                    )

        print(f"Synchronized {len(server_items)} items for category {category_id}")
        return True
    except Exception as e:
        print(f"Sync error for category {category_id}: {e}")
        import traceback

        traceback.print_exc()
        return False


def get_company_details_from_api():
    url = "https://c1.amali.japango.co.tz/api/v1/companies/company_details"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"Raw company details API response: {data}")  # Debug log
        companies_data = data.get("data", [])
        if not isinstance(companies_data, list):
            print("API response 'data' is not a list, adjusting to single object")
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
        print(
            f"Fetched {len(companies)} companies: {[c['company_name'] for c in companies]}"
        )
        return companies
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for company details: {req_err}")
        return []


def post_order_to_server(order_data):
    """Post order data to the server API."""
    url = "https://c1.amali.japango.co.tz/api/v1/orders/store_local_sale"
    headers = {"Content-Type": "application/json"}

    # Prepare payload matching server expectations
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
        # Add extra_charges if your local system supports it; omitted here as not in local schema
    }
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        server_response = response.json()
        print(f"Order posted successfully: {server_response}")
        return server_response
    except requests.exceptions.RequestException as e:
        print(f"Failed to post order to server: {e}")
        if e.response is not None:
            print(f"Server response: {e.response.text}")
        return None


def update_server_stock(stock_changes):
    """Update server-side item_stocks to match the local stock quantity."""
    url = "https://c1.amali.japango.co.tz/api/v1/stocks/update"  # Replace with actual endpoint
    headers = {"Content-Type": "application/json"}

    # Prepare payload to set the exact stock quantity on the server
    payload = {
        "stock_updates": [
            {
                "item_id": change["item_id"],
                "new_quantity": change[
                    "new_quantity"
                ],  # Send the new stock quantity (e.g., 19)
            }
            for change in stock_changes
        ]
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        server_response = response.json()
        print(f"Stock updated on server successfully: {server_response}")
        return server_response
    except requests.exceptions.RequestException as e:
        print(f"Failed to update stock on server: {e}")
        if e.response is not None:
            print(f"Server response: {e.response.text}")
        return None


def save_and_sync_stock(order_data, items, payment_id, customer_id):
    """Save order locally and sync stock changes with server."""
    # Save order locally and get stock changes
    result = db.save_order(order_data, items, payment_id, customer_id)
    if not result:
        print("Failed to save order locally, aborting stock sync")
        return False

    order_id = result["order_id"]
    stock_changes = result["stock_changes"]

    # Sync stock changes with server
    server_response = update_server_stock(stock_changes)
    if server_response and server_response.get(
        "success", True
    ):  # Adjust based on actual response
        print(
            f"Order {order_id} saved locally and stock synced with server successfully"
        )
        return True
    else:
        print(f"Order {order_id} saved locally but failed to sync stock with server")
        return False


def save_and_sync_order(order_data, items, payment_id, customer_id):
    """Save order locally and sync with server."""
    # Save order locally
    saved_order = db.save_order(order_data, items, payment_id, customer_id)
    if not saved_order:
        print("Failed to save order locally, aborting sync")
        return False

    # Post to server
    server_response = post_order_to_server(saved_order)
    if server_response and server_response.get("success"):
        print(f"Order {saved_order['order_id']} synced with server successfully")
        return True
    else:
        print(
            f"Order {saved_order['order_id']} saved locally but failed to sync with server"
        )
        return False


def sync_data_with_server():
    """Synchronize local database with server data, treating server as source of truth."""
    try:
        # Sync Item Groups
        server_groups = get_item_groups_from_api()
        if not server_groups:
            print("No server groups retrieved, aborting sync")
            return False
        local_groups = db.get_local_item_groups()
        group_mapping = {}
        for group in server_groups:
            if not isinstance(group, dict) or "name" not in group or "id" not in group:
                print(f"Invalid group data: {group}, skipping")
                continue
            if group["name"] not in local_groups:
                db.insert_item_group(group["name"])
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name FROM item_groups WHERE name = ?", (group["name"],)
                )
                row = cursor.fetchone()
                if row:
                    group_mapping[row[1]] = row[0]
                else:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO item_groups (name, created_at)
                        VALUES (?, CURRENT_TIMESTAMP)
                        """,
                        (group["name"],),
                    )
                    conn.commit()
                    cursor.execute(
                        "SELECT id, name FROM item_groups WHERE name = ?",
                        (group["name"],),
                    )
                    row = cursor.fetchone()
                    if row:
                        group_mapping[row[1]] = row[0]
        # Sync Categories and Items
        all_server_items = []
        server_category_ids = set()
        for group in server_groups:
            group_name = group["name"]
            group_id = group_mapping.get(group_name)
            if not group_id:
                continue
            server_categories = get_categories_for_group(group_name)
            if not server_categories:
                continue
            server_category_ids.update(cat["id"] for cat in server_categories)
            local_categories = db.get_local_categories_for_group(group_name)
            local_cat_ids = {cat["id"] for cat in local_categories}
            for cat in server_categories:
                if cat["id"] not in local_cat_ids:
                    db.insert_category(cat["id"], cat["name"], group_id)
            for cat in server_categories:
                items = get_items_by_category_from_api(cat["id"])
                if items:
                    all_server_items.extend(items)
        # Handle Item Synchronization
        local_items = db.get_all_local_items()
        local_item_ids = {item["id"] for item in local_items}
        server_item_ids = {item["id"] for item in all_server_items}
        with db.get_connection() as conn:
            cursor = conn.cursor()
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
        items_synced = 0
        for item in all_server_items:
            local_item = next(
                (li for li in local_items if li["id"] == item["id"]), None
            )

            # Map server response to insert_item parameters with error handling
            try:
                server_item_data = {
                    "id": item["id"],
                    "name": item.get("item_name"),
                    "barcode": item.get("barcode", ""),
                    "selling_unit": item.get("selling_unit", "Unit"),
                    "buying_unit": item.get("buying_unit", "Unit"),
                    "item_price": float(item.get("item_price", "0.0")),
                    "item_cost": float(item.get("item_cost", "0.0")),
                    "stock_quantity": float(item.get("stock_quantity", "0.0")),
                    "category_id": item.get("category_id"),
                    "min_quantity": float(item.get("min_quantity", "0.0")),
                    "max_quantity": float(item.get("max_quantity", "0.0")),
                    "store_id": item.get("store_id", 1),
                    "store_name": item.get("store_name", "Default Store"),
                    "expire_date": item.get("expire_date"),
                }
                # Validate required fields
                if not server_item_data["category_id"]:
                    print(f"Skipping item {item['id']} - missing category_id")
                    continue
                if not server_item_data["name"]:
                    print(f"Skipping item {item['id']} - missing name")
                    continue
                if not local_item:
                    db.insert_item(
                        server_item_data["id"],
                        server_item_data["name"],
                        server_item_data["barcode"],
                        server_item_data["selling_unit"],
                        server_item_data["item_price"],
                        server_item_data["item_cost"],
                        server_item_data["stock_quantity"],
                        server_item_data["category_id"],
                        server_item_data["min_quantity"],
                        server_item_data["max_quantity"],
                        server_item_data["store_id"],
                        server_item_data["store_name"],
                        server_item_data["expire_date"],
                        server_item_data["buying_unit"],
                    )
                    items_synced += 1
                elif (
                    local_item["name"] != server_item_data["name"]
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
                    or local_item.get("min_quantity")
                    != server_item_data["min_quantity"]
                    or local_item.get("max_quantity")
                    != server_item_data["max_quantity"]
                    or local_item.get("expire_date") != server_item_data["expire_date"]
                ):
                    # Assuming you have an update_item function that can handle all these details
                    db.update_item(
                        server_item_data["id"],
                        server_item_data["name"],
                        server_item_data["barcode"],
                        server_item_data["category_id"],
                        1,  # item_type_id (assuming a default)
                        None,  # item_group_id
                        server_item_data["expire_date"],
                        server_item_data["buying_unit"],
                        server_item_data["selling_unit"],
                        {server_item_data["store_id"]: server_item_data["item_price"]},
                        {server_item_data["store_id"]: server_item_data["item_cost"]},
                        {
                            server_item_data["store_id"]: {
                                "stock_quantity": server_item_data["stock_quantity"],
                                "min_quantity": server_item_data["min_quantity"],
                                "max_quantity": server_item_data["max_quantity"],
                            }
                        },
                        server_item_data["store_id"],
                        server_item_data["store_name"],
                    )
                    items_synced += 1
            except ValueError as ve:
                print(
                    f"Error processing item {item.get('id', 'unknown')}: Invalid numeric value - {ve}"
                )
                continue
            except KeyError as ke:
                print(
                    f"Error processing item {item.get('id', 'unknown')}: Missing key - {ke}. Item data: {item}"
                )
                continue
        # Sync Payments
        server_payments = get_payments_from_api()
        local_payments = db.get_all_local_payments()
        local_payment_ids = {p["id"] for p in local_payments}
        server_payment_ids = {p["id"] for p in server_payments}
        with db.get_connection() as conn:
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
        for payment in server_payments:
            local_payment = next(
                (lp for lp in local_payments if lp["id"] == payment["id"]), None
            )
            if not local_payment:
                db.insert_payment(
                    payment["id"],
                    payment["short_code"],
                    payment["payment_method"],
                    payment["payment_type_id"],
                )
            elif (
                local_payment["short_code"] != payment["short_code"]
                or local_payment["payment_method"] != payment["payment_method"]
                or local_payment["payment_type_id"] != payment["payment_type_id"]
            ):
                db.update_payment(
                    payment["id"],
                    payment["short_code"],
                    payment["payment_method"],
                    payment["payment_type_id"],
                )
        # Sync Customers
        server_customers = get_customers_from_api()
        local_customers = db.get_all_local_customers()
        local_customer_ids = {c["id"] for c in local_customers}
        server_customer_ids = {c["id"] for c in server_customers}
        with db.get_connection() as conn:
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
        for customer in server_customers:
            local_customer = next(
                (lc for lc in local_customers if lc["id"] == customer["id"]), None
            )
            if not local_customer:
                db.insert_customer(
                    customer["id"],
                    customer["customer_name"],
                    customer["active"],
                )
            elif (
                local_customer["customer_name"] != customer["customer_name"]
                or local_customer["active"] != customer["active"]
            ):
                db.update_customer(
                    customer["id"],
                    customer["customer_name"],
                    customer["active"],
                )
        # Sync Customer Types
        server_customer_types = get_customer_types_from_api()
        local_customer_types = db.get_all_local_customer_types()
        local_customer_type_ids = {ct["id"] for ct in local_customer_types}
        server_customer_type_ids = {ct["id"] for ct in server_customer_types}
        with db.get_connection() as conn:
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
        for customer_type in server_customer_types:
            local_customer_type = next(
                (
                    lct
                    for lct in local_customer_types
                    if lct["id"] == customer_type["id"]
                ),
                None,
            )
            if not local_customer_type:
                db.insert_customer_type(
                    customer_type["id"],
                    customer_type["name"],
                    customer_type["is_active"],
                )
            elif (
                local_customer_type["name"] != customer_type["name"]
                or local_customer_type["is_active"] != customer_type["is_active"]
            ):
                db.update_customer_type(
                    customer_type["id"],
                    customer_type["name"],
                    customer_type["is_active"],
                )
        # Sync Company Details
        server_companies = get_company_details_from_api()
        local_companies = db.get_all_local_companies()
        local_company_ids = {c["id"] for c in local_companies if c["id"] is not None}
        server_company_ids = {c["id"] for c in server_companies if c["id"] is not None}
        with db.get_connection() as conn:
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
        for company in server_companies:
            local_company = next(
                (lc for lc in local_companies if lc["id"] == company["id"]), None
            )
            if not local_company:
                db.update_company_details(company)
                print(f"Inserted company {company['id']} ({company['company_name']})")
            elif (
                local_company["company_name"] != company["company_name"]
                or local_company["address"] != company["address"]
                or local_company["state"] != company["state"]
                or local_company["phone"] != company["phone"]
                or local_company["tin_no"] != company["tin_no"]
                or local_company["vrn_no"] != company["vrn_no"]
                or local_company["country_id"] != company["country_id"]
                or local_company["email"] != company["email"]
                or local_company["website"] != company["website"]
                or local_company["post_code"] != company["post_code"]
                or local_company["company_logo"] != company["company_logo"]
                or local_company["is_active"] != company["is_active"]
            ):
                db.update_company_details(company)
                print(f"Updated company {company['id']} ({company['company_name']})")
        print(
            f"Synchronization completed: {items_synced} items synced along with payments, customers, customer types, and companies"
        )
        return True
    except Exception as e:
        print(f"Sync error: {e}")
        import traceback

        traceback.print_exc()
        return False


def post_new_item_to_api(item_data):
    url = "https://c1.amali.japango.co.tz/api/v1/items/sale_items"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, data=json.dumps(item_data), headers=headers)
        response.raise_for_status()
        print("Item posted successfully:", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to post item: {e}")
        return None


if __name__ == "__main__":
    sync_data_with_server()
