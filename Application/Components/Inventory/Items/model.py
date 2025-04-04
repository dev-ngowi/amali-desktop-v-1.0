import logging
import sqlite3
from datetime import datetime
from Helper.db_conn import DatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ItemManager:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_connection(self):
        """Get database connection with thread safety"""
        with self.db_manager.lock:
            conn = sqlite3.connect(self.db_manager.db_path, timeout=30)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row  # Consistent use across all methods
            return conn

    def _commit_and_close(self, conn):
        """Commit changes and close connection"""
        try:
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error committing changes: {str(e)}")
            raise  # Let the caller handle the exception
        finally:
            conn.close()

    def _rollback_and_close(self, conn):
        """Rollback changes and close connection"""
        try:
            conn.rollback()
        except sqlite3.Error as e:
            logger.error(f"Error rolling back changes: {str(e)}")
        finally:
            conn.close()

    def create_item(self, item_data):
        """Create a new item with all related data"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            conn.execute("BEGIN TRANSACTION")

            # Validate required fields
            required_fields = [
                "name",
                "barcode",
                "category_id",
                "item_type_id",
                "buying_unit_id",
                "selling_unit_id",
                "store_data",
            ]
            for field in required_fields:
                if field not in item_data or not item_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Clean nullable values
            brand_id = (
                item_data.get("brand_id")
                if item_data.get("brand_id") != "None"
                else None
            )
            item_group_id = (
                item_data.get("item_group_id")
                if item_data.get("item_group_id") != "None"
                else None
            )
            exprire_date = item_data.get("exprire_date")  # Fixed spelling

            # Insert barcode
            cursor.execute(
                "INSERT INTO barcodes (code) VALUES (?)", (item_data["barcode"],)
            )
            barcode_id = cursor.lastrowid

            # Insert image if provided
            image_id = None
            if "item_image_path" in item_data:
                cursor.execute(
                    "INSERT INTO images (file_path) VALUES (?)",
                    (item_data["item_image_path"],),
                )
                image_id = cursor.lastrowid

            # Insert item
            cursor.execute(
                """
                INSERT INTO items (name, category_id, item_type_id, item_group_id, exprire_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item_data["name"],
                    item_data["category_id"],
                    item_data["item_type_id"],
                    item_group_id,
                    exprire_date,
                ),
            )
            item_id = cursor.lastrowid

            # Insert item barcode relation
            cursor.execute(
                "INSERT INTO item_barcodes (item_id, barcode_id) VALUES (?, ?)",
                (item_id, barcode_id),
            )

            # Insert brand relation if exists
            if brand_id:
                cursor.execute(
                    "INSERT INTO brand_applicable_items (item_id, brand_id) VALUES (?, ?)",
                    (item_id, brand_id),
                )

            # Process store relationships
            for store_info in item_data["store_data"]:
                self._create_store_relations(cursor, item_id, item_data, store_info)

            # Insert image relation if exists
            if image_id:
                cursor.execute(
                    "INSERT INTO item_images (item_id, image_id) VALUES (?, ?)",
                    (item_id, image_id),
                )

            # Insert unit relationships
            cursor.execute(
                "INSERT INTO item_units (item_id, buying_unit_id, selling_unit_id) VALUES (?, ?, ?)",
                (item_id, item_data["buying_unit_id"], item_data["selling_unit_id"]),
            )

            self._commit_and_close(conn)
            logger.info(f"Item created successfully with ID: {item_id}")
            return {
                "success": True,
                "item_id": item_id,
                "message": "Item added successfully",
            }

        except (ValueError, sqlite3.Error) as e:
            self._rollback_and_close(conn)
            logger.error(f"Error creating item: {str(e)}")
            return {"success": False, "message": str(e)}

    def _create_store_relations(self, cursor, item_id, item_data, store_info):
        """Helper method to handle store-related insertions"""
        store_id = store_info["store_id"]

        # Insert store relationship
        cursor.execute(
            "INSERT INTO item_stores (item_id, store_id) VALUES (?, ?)",
            (item_id, store_id),
        )

        # Insert stock record
        cursor.execute(
            "INSERT INTO stocks (item_id, store_id, min_quantity, max_quantity) VALUES (?, ?, ?, ?)",
            (item_id, store_id, store_info["min_quantity"], store_info["max_quantity"]),
        )
        stock_id = cursor.lastrowid

        # Insert item stock relationship
        cursor.execute(
            "INSERT INTO item_stocks (item_id, stock_id, stock_quantity) VALUES (?, ?, ?)",
            (item_id, stock_id, store_info["stock_quantity"]),
        )

        # Insert purchase cost
        cursor.execute(
            "INSERT INTO item_costs (item_id, store_id, unit_id, amount) VALUES (?, ?, ?, ?)",
            (
                item_id,
                store_id,
                item_data["buying_unit_id"],
                store_info["purchase_rate"],
            ),
        )

        # Insert selling price
        cursor.execute(
            "INSERT INTO item_prices (item_id, store_id, unit_id, amount) VALUES (?, ?, ?, ?)",
            (
                item_id,
                store_id,
                item_data["selling_unit_id"],
                store_info["selling_price"],
            ),
        )

        # Insert tax relationship if exists
        if (
            "tax_id" in store_info
            and store_info["tax_id"]
            and store_info["tax_id"] != "None"
        ):
            cursor.execute(
                "INSERT INTO item_taxes (item_id, store_id, tax_id) VALUES (?, ?, ?)",
                (item_id, store_id, store_info["tax_id"]),
            )

    def read_item(self, item_id):
        """Read item details with related data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Fetch basic item data
            cursor.execute(
                """
                SELECT i.*, b.code as barcode
                FROM items i
                LEFT JOIN item_barcodes ib ON i.id = ib.item_id
                LEFT JOIN barcodes b ON ib.barcode_id = b.id
                WHERE i.id = ?
                """,
                (item_id,),
            )
            item = cursor.fetchone()
            if not item:
                return {"success": False, "message": "Item not found"}
            
            item_dict = dict(item)
            
            # Fetch units
            cursor.execute(
                """
                SELECT buying_unit_id, selling_unit_id
                FROM item_units
                WHERE item_id = ?
                """,
                (item_id,)
            )
            units = cursor.fetchone()
            if units:
                item_dict.update(dict(units))

            # Fetch brand
            cursor.execute(
                """
                SELECT brand_id
                FROM brand_applicable_items
                WHERE item_id = ?
                """,
                (item_id,)
            )
            brand = cursor.fetchone()
            if brand:
                item_dict["brand_id"] = brand["brand_id"]

            # Fetch image
            cursor.execute(
                """
                SELECT i.file_path
                FROM item_images ii
                JOIN images i ON ii.image_id = i.id
                WHERE ii.item_id = ?
                """,
                (item_id,)
            )
            image = cursor.fetchone()
            if image:
                item_dict["item_image_path"] = image["file_path"]

            self._commit_and_close(conn)
            return {"success": True, "data": item_dict}
        except sqlite3.Error as e:
            self._rollback_and_close(conn)
            logger.error(f"Error reading item: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        
    def update_item(self, item_id, item_data):
        """Update existing item"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            conn.execute("BEGIN TRANSACTION")
            cursor.execute(
                """
                UPDATE items
                SET name = ?, category_id = ?, item_type_id = ?,
                    item_group_id = ?, exprire_date = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    item_data.get("name"),
                    item_data.get("category_id"),
                    item_data.get("item_type_id"),
                    item_data.get("item_group_id"),
                    item_data.get("exprire_date"),  # Fixed spelling
                    datetime.now().isoformat(),
                    item_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError("Item not found")

            self._commit_and_close(conn)
            return {"success": True, "message": "Item updated successfully"}
        except (ValueError, sqlite3.Error) as e:
            self._rollback_and_close(conn)
            logger.error(f"Error updating item: {str(e)}")
            return {"success": False, "message": str(e)}

    def delete_item(self, item_id):
        """Delete item and all related records"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            conn.execute("BEGIN TRANSACTION")

            # Delete related records from dependent tables
            cursor.execute("DELETE FROM item_barcodes WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_stores WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_units WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_stocks WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_costs WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_prices WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_taxes WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM brand_applicable_items WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_images WHERE item_id = ?", (item_id,))

            # Now delete the item itself
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            if cursor.rowcount == 0:
                raise ValueError("Item not found")

            self._commit_and_close(conn)
            logger.info(f"Item {item_id} and related records deleted successfully")
            return {"success": True, "message": "Item deleted successfully"}
        except (ValueError, sqlite3.Error) as e:
            self._rollback_and_close(conn)
            logger.error(f"Error deleting item: {str(e)}")
            return {"success": False, "message": str(e)}

    def list_items(self):
        """List all items"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT i.*, b.code as barcode
                FROM items i
                LEFT JOIN item_barcodes ib ON i.id = ib.item_id
                LEFT JOIN barcodes b ON ib.barcode_id = b.id
                """
            )
            items = [dict(row) for row in cursor.fetchall()]
            self._commit_and_close(conn)
            return {"success": True, "data": items}
        except sqlite3.Error as e:
            self._rollback_and_close(conn)
            logger.error(f"Error listing items: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}

    # Helper methods (get_units, get_stores, etc.) can remain largely the same but should follow the same pattern
    def get_units(self):
        """Fetch all units from the database"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name FROM units")
            units = [dict(row) for row in cursor.fetchall()]
            self._commit_and_close(conn)
            return {"success": True, "data": units}
        except sqlite3.Error as e:
            self._rollback_and_close(conn)
            logger.error(f"Error fetching units: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}

    def get_stores(self):
        """Fetch all stores from the database"""
        conn = None
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM stores")
            stores = [
                {"id": row["id"], "name": row["name"]} for row in cursor.fetchall()
            ]
            self._commit_and_close(conn)
            return {"success": True, "data": stores}
        except sqlite3.Error as e:
            logger.error(f"Error fetching stores: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            if conn:
                conn.close()

    def get_categories(self):
        """Fetch all categories from the database"""
        conn = None
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM categories WHERE deleted_at IS NULL")
            categories = [
                {"id": row["id"], "name": row["name"]} for row in cursor.fetchall()
            ]
            self._commit_and_close(conn)
            return {"success": True, "data": categories}
        except sqlite3.Error as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            if conn:
                conn.close()

    def get_item_types(self):
        """Fetch all item types from the database"""
        conn = None
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM item_types")
            item_types = [
                {"id": row["id"], "name": row["name"]} for row in cursor.fetchall()
            ]
            self._commit_and_close(conn)
            return {"success": True, "data": item_types}
        except sqlite3.Error as e:
            logger.error(f"Error fetching item types: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            if conn:
                conn.close()

    def get_brands(self):
        """Fetch all brands from the database (assuming a brands table exists)"""
        conn = None
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Note: Assuming you have a brands table; adjust if different
            cursor.execute("SELECT id, name FROM item_brands")
            brands = [
                {"id": row["id"], "name": row["name"]} for row in cursor.fetchall()
            ]
            self._commit_and_close(conn)
            return {"success": True, "data": brands}
        except sqlite3.Error as e:
            logger.error(f"Error fetching brands: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            if conn:
                conn.close()

    def get_taxes(self):
        """Fetch all taxes from the database (assuming a taxes table exists)"""
        conn = None
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Note: Assuming you have a taxes table; adjust if different
            cursor.execute("SELECT id, name FROM taxes")
            taxes = [
                {"id": row["id"], "name": row["name"]} for row in cursor.fetchall()
            ]
            self._commit_and_close(conn)
            return {"success": True, "data": taxes}
        except sqlite3.Error as e:
            logger.error(f"Error fetching taxes: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            if conn:
                conn.close()


# Example usage:
if __name__ == "__main__":
    item_manager = ItemManager()

    # Example item creation
    item_data = {
        "name": "Test Item",
        "barcode": "123456789",
        "category_id": 1,
        "item_type_id": 1,
        "buying_unit_id": 1,
        "selling_unit_id": 1,
        "store_data": [
            {
                "store_id": 1,
                "min_quantity": 10,
                "max_quantity": 100,
                "stock_quantity": 50,
                "purchase_rate": 5.99,
                "selling_price": 9.99,
            }
        ],
        "item_group_id": None,
        "brand_id": None,
        "exprire_date": None,
    }

    result = item_manager.create_item(item_data)
    print(result)