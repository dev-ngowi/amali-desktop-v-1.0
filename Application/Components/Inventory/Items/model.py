import logging
import sqlite3
from datetime import datetime
from Helper.db_conn import DatabaseManager

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
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
            conn.row_factory = sqlite3.Row
            return conn

    def _commit_and_close(self, conn):
        """Commit changes and close connection"""
        if conn:
            try:
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Error committing changes: {str(e)}")
                raise
            finally:
                conn.close()

    def _rollback_and_close(self, conn):
        """Rollback changes and close connection"""
        if conn:
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
                "category_id",
                "item_type_id",
                "buying_unit_id",
                "selling_unit_id",
            ]
            for field in required_fields:
                if field not in item_data or item_data[field] is None:
                    raise ValueError(f"Missing required field: {field}")

            # Handle store_data
            store_data = item_data.get("store_data")
            if not store_data or not isinstance(store_data, list):
                raise ValueError("Store data is required and must be a list")

            # Clean nullable values
            barcode = item_data.get("barcode")
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
            expire_date = item_data.get("expire_date")
            image_path = item_data.get("item_image_path")
            current_time = datetime.now().isoformat()

            # Insert barcode if provided
            barcode_id = None
            if barcode:
                cursor.execute(
                    "INSERT INTO barcodes (code, created_at, updated_at) VALUES (?, ?, ?)",
                    (barcode, current_time, current_time),
                )
                barcode_id = cursor.lastrowid

            # Insert image if provided
            image_id = None
            if image_path:
                cursor.execute(
                    "INSERT INTO images (file_path, created_at, updated_at) VALUES (?, ?, ?)",
                    (image_path, current_time, current_time),
                )
                image_id = cursor.lastrowid

            # Insert item
            cursor.execute(
                """
                INSERT INTO items (name, category_id, item_type_id, item_group_id, expire_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_data["name"],
                    item_data["category_id"],
                    item_data["item_type_id"],
                    item_group_id,
                    expire_date,
                    current_time,
                    current_time,
                ),
            )
            item_id = cursor.lastrowid
            logger.debug(f"Inserted item: id={item_id}, name={item_data['name']}")

            # Insert item barcode relation
            if barcode_id:
                cursor.execute(
                    "INSERT INTO item_barcodes (item_id, barcode_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (item_id, barcode_id, current_time, current_time),
                )

            # Insert brand relation if exists
            if brand_id:
                cursor.execute(
                    "INSERT INTO brand_applicable_items (item_id, brand_id) VALUES (?, ?)",
                    (item_id, brand_id),
                )

            # Process store relationships
            for store_info in store_data:
                self._create_store_relations(
                    cursor, item_id, item_data, store_info, current_time
                )

            # Insert image relation if exists
            if image_id:
                cursor.execute(
                    "INSERT INTO item_images (item_id, image_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (item_id, image_id, current_time, current_time),
                )

            # Insert unit relationships
            cursor.execute(
                "INSERT INTO item_units (item_id, buying_unit_id, selling_unit_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (
                    item_id,
                    item_data["buying_unit_id"],
                    item_data["selling_unit_id"],
                    current_time,
                    current_time,
                ),
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

    def _create_store_relations(
        self, cursor, item_id, item_data, store_info, current_time
    ):
        """Helper method to handle store-related insertions"""
        try:
            store_id = store_info.get("store_id")
            if not store_id or store_id == -1:
                raise ValueError(f"Valid Store ID is required for item {item_id}")

            # Insert stock record
            min_qty = float(store_info.get("min_quantity", 0) or 0)
            max_qty = float(store_info.get("max_quantity", 0) or 0)
            cursor.execute(
                """
                INSERT INTO stocks (item_id, store_id, min_quantity, max_quantity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (item_id, store_id, min_qty, max_qty, current_time, current_time),
            )
            stock_id = cursor.lastrowid
            logger.debug(
                f"Inserted stocks: item_id={item_id}, store_id={store_id}, min={min_qty}, max={max_qty}"
            )

            # Insert item stock relationship
            stock_qty = float(store_info.get("stock_quantity", 0) or 0)
            cursor.execute(
                """
                INSERT INTO item_stocks (item_id, stock_id, stock_quantity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item_id, stock_id, stock_qty, current_time, current_time),
            )
            logger.debug(
                f"Inserted item_stocks: item_id={item_id}, stock_id={stock_id}, qty={stock_qty}"
            )

            # Insert purchase cost
            purchase_rate = float(store_info.get("purchase_rate", 0) or 0)
            cursor.execute(
                """
                INSERT INTO item_costs (item_id, store_id, unit_id, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    store_id,
                    item_data["buying_unit_id"],
                    purchase_rate,
                    current_time,
                ),
            )
            logger.debug(
                f"Inserted item_costs: item_id={item_id}, store_id={store_id}, amount={purchase_rate}"
            )

            # Insert selling price
            selling_price = float(store_info.get("selling_price", 0) or 0)
            cursor.execute(
                """
                INSERT INTO item_prices (item_id, store_id, unit_id, amount, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    store_id,
                    item_data["selling_unit_id"],
                    selling_price,
                    current_time,
                    current_time,
                ),
            )
            logger.debug(
                f"Inserted item_prices: item_id={item_id}, store_id={store_id}, amount={selling_price}"
            )

            # Insert tax relationship if exists
            tax_id = store_info.get("tax_id")
            if tax_id and tax_id != "None" and tax_id != -1:
                cursor.execute(
                    "INSERT INTO item_taxes (item_id, store_id, tax_id) VALUES (?, ?, ?)",
                    (item_id, store_id, tax_id),
                )
                logger.debug(
                    f"Inserted item_taxes: item_id={item_id}, store_id={store_id}, tax_id={tax_id}"
                )

        except Exception as e:
            logger.error(f"Error in store relations for item_id={item_id}: {str(e)}")
            raise

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
                (item_id,),
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
                (item_id,),
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
                (item_id,),
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
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            conn.execute("BEGIN TRANSACTION")
            current_time = datetime.now().isoformat()

            # Update items table (only columns that exist)
            cursor.execute(
                """
                UPDATE items
                SET name = ?, category_id = ?, item_type_id = ?, item_group_id = ?, 
                    expire_date = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    item_data["name"],
                    item_data["category_id"],
                    item_data["item_type_id"],
                    item_data.get("item_group_id"),
                    item_data.get("expire_date"),
                    current_time,
                    item_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError("Item not found")

            # Handle barcode
            barcode = item_data.get("barcode")
            if barcode:
                cursor.execute("SELECT id FROM barcodes WHERE code = ?", (barcode,))
                barcode_row = cursor.fetchone()
                if barcode_row:
                    barcode_id = barcode_row["id"]
                else:
                    cursor.execute(
                        """
                        INSERT INTO barcodes (code, created_at, updated_at)
                        VALUES (?, ?, ?)
                        """,
                        (barcode, current_time, current_time),
                    )
                    barcode_id = cursor.lastrowid

                # Update or insert item_barcodes
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO item_barcodes (item_id, barcode_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (item_id, barcode_id, current_time, current_time),
                )
            else:
                # Remove barcode if it exists and is set to None/empty
                cursor.execute("DELETE FROM item_barcodes WHERE item_id = ?", (item_id,))

            # Update item_units
            cursor.execute(
                """
                INSERT OR REPLACE INTO item_units (item_id, buying_unit_id, selling_unit_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    item_data["buying_unit_id"],
                    item_data["selling_unit_id"],
                    current_time,
                    current_time,
                ),
            )

            # Handle brand
            brand_id = item_data.get("brand_id")
            cursor.execute(
                "DELETE FROM brand_applicable_items WHERE item_id = ?", (item_id,)
            )
            if brand_id and brand_id != "None" and brand_id != -1:
                cursor.execute(
                    """
                    INSERT INTO brand_applicable_items (item_id, brand_id)
                    VALUES (?, ?)
                    """,
                    (item_id, brand_id),
                )

            # Handle image
            image_path = item_data.get("item_image_path")
            cursor.execute("DELETE FROM item_images WHERE item_id = ?", (item_id,))
            if image_path:
                cursor.execute(
                    """
                    INSERT INTO images (file_path, created_at)
                    VALUES (?, ?)
                    """,
                    (image_path, current_time),
                )
                image_id = cursor.lastrowid
                cursor.execute(
                    """
                    INSERT INTO item_images (item_id, image_id, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (item_id, image_id, current_time),
                )

            # Delete existing store-related data
            cursor.execute("DELETE FROM stocks WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_stocks WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_costs WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_prices WHERE item_id = ?", (item_id,))
            cursor.execute("DELETE FROM item_taxes WHERE item_id = ?", (item_id,))

            # Insert new store-related data
            for store in item_data["store_data"]:
                # Insert stocks
                cursor.execute(
                    """
                    INSERT INTO stocks (item_id, store_id, min_quantity, max_quantity, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        store["store_id"],
                        store["min_quantity"],
                        store["max_quantity"],
                        current_time,
                        current_time,
                    ),
                )
                stock_id = cursor.lastrowid

                # Insert item_stocks
                cursor.execute(
                    """
                    INSERT INTO item_stocks (item_id, stock_id, stock_quantity, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        stock_id,
                        store["stock_quantity"],
                        current_time,
                        current_time,
                    ),
                )

                # Insert item_costs
                cursor.execute(
                    """
                    INSERT INTO item_costs (item_id, store_id, unit_id, amount, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        store["store_id"],
                        item_data["buying_unit_id"],
                        store["purchase_rate"],
                        current_time,
                        current_time,
                    ),
                )

                # Insert item_prices
                cursor.execute(
                    """
                    INSERT INTO item_prices (item_id, store_id, unit_id, amount, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        store["store_id"],
                        item_data["selling_unit_id"],
                        store["selling_price"],
                        current_time,
                        current_time,
                    ),
                )

                # Insert item_taxes if tax_id exists
                if store.get("tax_id") and store["tax_id"] != "None" and store["tax_id"] != -1:
                    cursor.execute(
                        """
                        INSERT INTO item_taxes (item_id, store_id, tax_id)
                        VALUES (?, ?, ?)
                        """,
                        (item_id, store["store_id"], store["tax_id"]),
                    )

            self._commit_and_close(conn)
            logger.info(f"Item {item_id} updated successfully")
            return {"success": True, "message": "Item updated successfully"}
        except Exception as e:
            self._rollback_and_close(conn)
            logger.error(f"Error updating item {item_id}: {str(e)}")
            return {"success": False, "message": f"Failed to update item: {str(e)}"}
        
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
            cursor.execute(
                "DELETE FROM brand_applicable_items WHERE item_id = ?", (item_id,)
            )
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
