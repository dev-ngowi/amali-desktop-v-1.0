import json
import requests
from Helper.modal import db
from PyQt5.QtGui import QIcon, QPixmap, QImage  # Import QPixmap and QImage
from PyQt5.QtCore import Qt  # Import Qt for image scaling


def load_icon(icon_path):
    """Loads an icon from the given path."""
    return QIcon(QPixmap(icon_path))


def load_image(image_url):
    """Loads a QPixmap image from a file path or URL.

    Handles both local file paths and URLs, though URL loading is basic
    and might need more robust error handling and network operations for
    production use (e.g., caching, asynchronous loading).
    """
    pixmap = QPixmap()
    if image_url.startswith(("http://", "https://")):
        # Basic URL handling - consider more robust approach for URLs in real app
        try:
            response = requests.get(image_url, stream=True, timeout=10)  # Add timeout
            response.raise_for_status()  # Raise error for bad status codes
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
            return QPixmap()  # Return null pixmap on failure
    else:
        # Assume it's a local file path
        if not pixmap.load(image_url):  # Load from local path
            print(f"Failed to load image from local path: {image_url}")
            return QPixmap()  # Return null pixmap on failure
    return pixmap


def get_item_groups_from_api():
    url = "http://127.0.0.1:8000/api/v1/items/item_group"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"Item groups API response: {data}")
        groups_data = data.get("data", [])
        groups = [item["name"] for item in groups_data if "name" in item]
        print(f"Fetched {len(groups)} item groups: {groups}")
        return groups
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for item groups: {req_err}")
        return []

def get_categories_for_group(group_id):
    url = "http://127.0.0.1:8000/api/v1/items/item_category"
    categories = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"Categories API response for group_id {group_id}: {data}")
        categories_data = data.get("data", [])
        # Flexible key check: try 'item_group_id' or 'group_id'
        categories = [
            {"name": item["name"], "id": item["id"]}
            for item in categories_data
            if ("item_group_id" in item and item["item_group_id"] == group_id) or
               ("group_id" in item and item["group_id"] == group_id)
            if "name" in item and "id" in item
        ]
        print(f"Fetched {len(categories)} categories for group_id {group_id}: {categories}")
        return categories
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for categories: {req_err}")
        return []

def get_items_for_category(category_id):
    url = f"http://127.0.0.1:8000/api/v1/items/sale_items?item_category_id={category_id}"
    items = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"Server response for item_category_id {category_id}: {data}")
        items_data = data.get("data", []) if isinstance(data, dict) else data
        items = [
            {
                "id": item["id"],
                "name": item["name"],
                "item_unit": item.get("item_unit", "unit"),
                "item_price": item.get("item_price", 0.0),
                "stock_quantity": item.get("stock_quantity", 0.0),
                "image_url": item.get("image_url", ""),
                "category_id": item.get("item_category_id", category_id),
            }
            for item in items_data
            if "id" in item and "name" in item
        ]
        print(f"Parsed {len(items)} items for item_category_id {category_id}")
        return items
    except requests.exceptions.RequestException as req_err:
        print(f"API request failed for items: {req_err}")
        return []

def sync_data_with_server():
    try:
        server_groups = get_item_groups_from_api()
        if not server_groups:
            print("No item groups received from server")
            return False

        local_groups = db.get_local_item_groups()
        group_mapping = {}
        
        for group in server_groups:
            if group not in local_groups:
                db.insert_item_group(group)
                
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM item_groups")
            group_mapping = {row[1]: row[0] for row in cursor.fetchall()}
            print(f"Group mapping: {group_mapping}")

        all_server_items = []
        for group_name in server_groups:
            group_id = group_mapping.get(group_name)
            if not group_id:
                print(f"No group_id found for {group_name}")
                continue
                
            server_categories = get_categories_for_group(group_id)
            if not server_categories:
                print(f"No categories for group {group_name}")
                continue
                
            local_categories = db.get_local_categories_for_group(group_name)
            local_cat_ids = {cat["id"] for cat in local_categories}
            print(f"Local categories for {group_name}: {local_categories}")
            
            for cat in server_categories:
                if cat["id"] not in local_cat_ids:
                    db.insert_category(cat["id"], cat["name"], group_id)
                    print(f"Inserted category {cat['id']} for group {group_name}")
                    
            for cat in server_categories:
                items = get_items_for_category(cat["id"])
                if items:
                    all_server_items.extend(items)
                    print(f"Fetched {len(items)} items for item_category_id {cat['id']}")
                else:
                    print(f"No items fetched for item_category_id {cat['id']}")
        
        print(f"Total server items fetched: {len(all_server_items)}")
        for item in all_server_items:
            db.insert_item(
                item["id"],
                item["name"],
                item["item_unit"],
                item["item_price"],
                item["stock_quantity"],
                item["category_id"]
            )
            print(f"Inserted item {item['id']} into database")

        print("Database synchronization completed successfully")
        return True
    except Exception as e:
        print(f"Error during synchronization: {e}")
        return False

def post_new_item_to_api(item_data):
    url = "http://127.0.0.1:8000/api/v1/items/sale_items"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, data=json.dumps(item_data), headers=headers)
        response.raise_for_status()
        print("Item posted successfully:", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to post item: {e}")
        return None
