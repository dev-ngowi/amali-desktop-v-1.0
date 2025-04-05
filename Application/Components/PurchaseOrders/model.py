import logging
import sqlite3
from datetime import datetime
from Helper.db_conn import DatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PurchaseOrderManager:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_connection(self):
        with self.db_manager.lock:
            conn = sqlite3.connect(self.db_manager.db_path, timeout=30)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            return conn

    def _commit_and_close(self, conn):
        try:
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error committing changes: {str(e)}")
            raise
        finally:
            conn.close()

    def _rollback_and_close(self, conn):
        try:
            conn.rollback()
        except sqlite3.Error as e:
            logger.error(f"Error rolling back changes: {str(e)}")
        finally:
            conn.close()

    def create_purchase_order(
        self,
        order_number,
        supplier_id,
        order_date,
        items,
        expected_delivery_date=None,
        status="Pending",
        currency="USD",
        notes=None,
    ):
        conn = self._get_connection()
        try:
            current_time = datetime.now().isoformat()
            total_amount = sum(item["total_price"] for item in items)

            query = """
                INSERT INTO purchase_orders (
                    order_number, supplier_id, order_date, expected_delivery_date, status,
                    total_amount, currency, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
                order_number,
                supplier_id,
                order_date,
                expected_delivery_date,
                status,
                total_amount,
                currency,
                notes,
                current_time,
                current_time,
            )
            cursor = conn.execute(query, values)
            po_id = cursor.lastrowid

            for item in items:
                item_query = """
                    INSERT INTO purchase_order_items (
                        purchase_order_id, item_id, unit_id, quantity, discount, unit_price,
                        tax_id, total_price, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                item_values = (
                    po_id,
                    item["item_id"],
                    item["unit_id"],
                    item["quantity"],
                    item.get("discount", 0.0),
                    item["unit_price"],
                    item.get("tax_id"),
                    item["total_price"],
                    current_time,
                    current_time,
                )
                conn.execute(item_query, item_values)

            self._commit_and_close(conn)
            logger.info(f"Created purchase order with ID: {po_id}")
            return po_id
        except sqlite3.Error as e:
            logger.error(f"Error creating purchase order: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def get_purchase_order(self, po_id):
        conn = self._get_connection()
        try:
            query = """
                SELECT po.*, v.name as supplier_name
                FROM purchase_orders po
                JOIN vendors v ON po.supplier_id = v.id
                WHERE po.id = ?
            """
            cursor = conn.execute(query, (po_id,))
            po = cursor.fetchone()

            if po:
                items_query = """
                    SELECT poi.*, i.name as item_name, u.name as unit_name
                    FROM purchase_order_items poi
                    JOIN items i ON poi.item_id = i.id
                    JOIN units u ON poi.unit_id = u.id
                    WHERE poi.purchase_order_id = ?
                """
                cursor = conn.execute(items_query, (po_id,))
                items = [dict(row) for row in cursor.fetchall()]
                result = dict(po)
                result["items"] = items
                conn.close()
                return result
            conn.close()
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving purchase order: {str(e)}")
            conn.close()
            raise

    def list_purchase_orders(self, status=None):
        conn = self._get_connection()
        try:
            query = """
                SELECT po.*, v.name as supplier_name
                FROM purchase_orders po
                JOIN vendors v ON po.supplier_id = v.id
            """
            params = []
            if status:
                query += " WHERE po.status = ?"
                params.append(status)

            cursor = conn.execute(query, params)
            pos = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return pos
        except sqlite3.Error as e:
            logger.error(f"Error listing purchase orders: {str(e)}")
            conn.close()
            raise

    def update_purchase_order(self, po_id, items=None, **kwargs):
        conn = self._get_connection()
        try:
            allowed_fields = {
                "order_number",
                "supplier_id",
                "order_date",
                "expected_delivery_date",
                "status",
                "currency",
                "notes",
                "total_amount",
            }
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            success = False

            # Update main PO fields if any
            if update_fields:
                update_fields["updated_at"] = datetime.now().isoformat()
                set_clause = ", ".join(f"{k} = ?" for k in update_fields.keys())
                values = list(update_fields.values()) + [po_id]
                query = f"UPDATE purchase_orders SET {set_clause} WHERE id = ?"
                cursor = conn.execute(query, values)
                if cursor.rowcount > 0:
                    success = True

            # Update PO items if provided
            if items is not None:
                # First, get existing items to determine what to update/delete
                existing_items_query = (
                    "SELECT id FROM purchase_order_items WHERE purchase_order_id = ?"
                )
                cursor = conn.execute(existing_items_query, (po_id,))
                existing_item_ids = set(row["id"] for row in cursor.fetchall())
                new_item_ids = set(item.get("id") for item in items if item.get("id"))

                # Delete items that are no longer in the list
                items_to_delete = existing_item_ids - new_item_ids
                if items_to_delete:
                    delete_query = (
                        "DELETE FROM purchase_order_items WHERE id IN ({})".format(
                            ",".join("?" for _ in items_to_delete)
                        )
                    )
                    conn.execute(delete_query, list(items_to_delete))

                # Update or insert items
                current_time = datetime.now().isoformat()
                for item in items:
                    if "id" in item and item["id"] in existing_item_ids:
                        # Update existing item
                        update_item_query = """
                            UPDATE purchase_order_items 
                            SET item_id = ?, unit_id = ?, quantity = ?, discount = ?, 
                                unit_price = ?, total_price = ?, updated_at = ?
                            WHERE id = ?
                        """
                        conn.execute(
                            update_item_query,
                            (
                                item["item_id"],
                                item["unit_id"],
                                item["quantity"],
                                item["discount"],
                                item["unit_price"],
                                item["total_price"],
                                current_time,
                                item["id"],
                            ),
                        )
                    else:
                        # Insert new item
                        insert_item_query = """
                            INSERT INTO purchase_order_items (
                                purchase_order_id, item_id, unit_id, quantity, discount, 
                                unit_price, total_price, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        conn.execute(
                            insert_item_query,
                            (
                                po_id,
                                item["item_id"],
                                item["unit_id"],
                                item["quantity"],
                                item["discount"],
                                item["unit_price"],
                                item["total_price"],
                                current_time,
                                current_time,
                            ),
                        )
                    success = True

            if success:
                self._commit_and_close(conn)
                logger.info(f"Updated purchase order with ID: {po_id}")
                return True
            self._rollback_and_close(conn)
            return False
        except sqlite3.Error as e:
            logger.error(f"Error updating purchase order: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def delete_purchase_order(self, po_id):
        conn = self._get_connection()
        try:
            query = "UPDATE purchase_orders SET status = 'Cancelled', updated_at = ? WHERE id = ?"
            current_time = datetime.now().isoformat()
            cursor = conn.execute(query, (current_time, po_id))

            if cursor.rowcount > 0:
                self._commit_and_close(conn)
                logger.info(f"Cancelled purchase order with ID: {po_id}")
                return True
            self._rollback_and_close(conn)
            return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting purchase order: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def get_suppliers(self):
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, name FROM vendors WHERE status = 'active'"
            )
            suppliers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return suppliers
        except sqlite3.Error as e:
            logger.error(f"Error retrieving suppliers: {str(e)}")
            conn.close()
            raise

    def get_items(self):
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT id, name FROM items WHERE status = 'active'")
            items = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return items
        except sqlite3.Error as e:
            logger.error(f"Error retrieving items: {str(e)}")
            conn.close()
            raise

    def get_units(self):
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT id, name FROM units")
            units = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return units
        except sqlite3.Error as e:
            logger.error(f"Error retrieving units: {str(e)}")
            conn.close()
            raise

    def get_company_info(self):
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM companies WHERE is_active = 1 LIMIT 1")
            company = cursor.fetchone()
            conn.close()
            return (
                dict(company)
                if company
                else {"company_name": "Unknown", "email": "N/A"}
            )
        except sqlite3.Error as e:
            logger.error(f"Error retrieving company info: {str(e)}")
            conn.close()
            raise

    # New GRN-related methods
    def create_grn(
        self,
        purchase_order_id,
        supplier_id,
        received_by,
        received_date,
        delivery_note_number=None,
        status="Pending",
        remarks=None,
        items=None,
    ):
        """
        Create a new Goods Received Note (GRN) and its items
        """
        conn = self._get_connection()
        try:
            current_time = datetime.now().isoformat()
            grn_number = (
                f"GRN-{purchase_order_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )

            # Insert into good_receipt_notes
            query = """
                INSERT INTO good_receipt_notes (
                    grn_number, purchase_order_id, supplier_id, received_by,
                    received_date, delivery_note_number, status, remarks,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
                grn_number,
                purchase_order_id,
                supplier_id,
                received_by,
                received_date,
                delivery_note_number,
                status,
                remarks,
                current_time,
                current_time,
            )
            cursor = conn.execute(query, values)
            grn_id = cursor.lastrowid

            # Insert GRN items if provided
            if items:
                for item in items:
                    item_query = """
                        INSERT INTO good_receive_note_items (
                            grn_id, purchase_order_item_id, item_id, ordered_quantity,
                            received_quantity, accepted_quantity, rejected_quantity,
                            unit_price, received_condition, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    item_values = (
                        grn_id,
                        item.get("purchase_order_item_id"),
                        item["item_id"],
                        item["ordered_quantity"],
                        item["received_quantity"],
                        item["accepted_quantity"],
                        item["rejected_quantity"],
                        item["unit_price"],
                        item.get("received_condition", "Good"),
                        current_time,
                        current_time,
                    )
                    conn.execute(item_query, item_values)

            self._commit_and_close(conn)
            logger.info(f"Created GRN with ID: {grn_id}, Number: {grn_number}")
            return {"id": grn_id, "grn_number": grn_number}
        except sqlite3.Error as e:
            logger.error(f"Error creating GRN: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def get_grn(self, grn_id):
        """
        Retrieve a specific GRN with its items
        """
        conn = self._get_connection()
        try:
            query = """
                SELECT grn.*, v.name as supplier_name, u.username as received_by_name
                FROM good_receipt_notes grn
                JOIN vendors v ON grn.supplier_id = v.id
                JOIN users u ON grn.received_by = u.id
                WHERE grn.id = ?
            """
            cursor = conn.execute(query, (grn_id,))
            grn = cursor.fetchone()

            if grn:
                items_query = """
                    SELECT grni.*, i.name as item_name
                    FROM good_receive_note_items grni
                    JOIN items i ON grni.item_id = i.id
                    WHERE grni.grn_id = ?
                """
                cursor = conn.execute(items_query, (grn_id,))
                items = [dict(row) for row in cursor.fetchall()]
                result = dict(grn)
                result["items"] = items
                conn.close()
                return result
            conn.close()
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving GRN: {str(e)}")
            conn.close()
            raise

    def list_grns(self, purchase_order_id=None, status=None):
        """
        List all GRNs with optional filters
        """
        conn = self._get_connection()
        try:
            query = """
                SELECT grn.*, v.name as supplier_name, u.username as received_by_name
                FROM good_receipt_notes grn
                JOIN vendors v ON grn.supplier_id = v.id
                JOIN users u ON grn.received_by = u.id
            """
            params = []
            conditions = []

            if purchase_order_id:
                conditions.append("grn.purchase_order_id = ?")
                params.append(purchase_order_id)
            if status:
                conditions.append("grn.status = ?")
                params.append(status)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor = conn.execute(query, params)
            grns = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return grns
        except sqlite3.Error as e:
            logger.error(f"Error listing GRNs: {str(e)}")
            conn.close()
            raise

    def update_grn(self, grn_id, **kwargs):
        """
        Update an existing GRN
        """
        conn = self._get_connection()
        try:
            allowed_fields = {
                "grn_number",
                "purchase_order_id",
                "supplier_id",
                "received_by",
                "received_date",
                "delivery_note_number",
                "status",
                "remarks",
            }
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not update_fields:
                conn.close()
                return False

            update_fields["updated_at"] = datetime.now().isoformat()
            set_clause = ", ".join(f"{k} = ?" for k in update_fields.keys())
            values = list(update_fields.values()) + [grn_id]

            query = f"UPDATE good_receipt_notes SET {set_clause} WHERE id = ?"
            cursor = conn.execute(query, values)

            if cursor.rowcount > 0:
                self._commit_and_close(conn)
                logger.info(f"Updated GRN with ID: {grn_id}")
                return True
            self._rollback_and_close(conn)
            return False
        except sqlite3.Error as e:
            logger.error(f"Error updating GRN: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def update_stock_from_grn(self, grn_id, stock_id=None):
        """
        Update stock levels in item_stocks based on accepted quantities in GRN.
        Requires a stock_id to determine the stock location.
        """
        if stock_id is None:
            raise ValueError("stock_id must be provided to update stock from GRN")

        conn = self._get_connection()
        try:
            # Get accepted items from GRN
            items_query = """
                SELECT item_id, accepted_quantity
                FROM good_receive_note_items
                WHERE grn_id = ?
            """
            cursor = conn.execute(items_query, (grn_id,))
            items = cursor.fetchall()

            for item in items:
                # Check if the item exists in item_stocks for the given stock_id
                check_query = """
                    SELECT id, stock_quantity 
                    FROM item_stocks 
                    WHERE item_id = ? AND stock_id = ?
                """
                cursor = conn.execute(check_query, (item["item_id"], stock_id))
                existing_stock = cursor.fetchone()

                if existing_stock:
                    # Update existing stock
                    update_query = """
                        UPDATE item_stocks
                        SET stock_quantity = stock_quantity + ?,
                            updated_at = ?
                        WHERE id = ?
                    """
                    conn.execute(
                        update_query,
                        (
                            item["accepted_quantity"],
                            datetime.now().isoformat(),
                            existing_stock["id"],
                        ),
                    )
                else:
                    # Insert new stock record if it doesn't exist
                    insert_query = """
                        INSERT INTO item_stocks (item_id, stock_id, stock_quantity, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    """
                    conn.execute(
                        insert_query,
                        (
                            item["item_id"],
                            stock_id,
                            item["accepted_quantity"],
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                        ),
                    )

            self._commit_and_close(conn)
            logger.info(f"Updated stock from GRN ID: {grn_id} for stock_id: {stock_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating stock from GRN: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def get_stock_id(self, item_id, store_id):
        """
        Get or create a stock_id for the given item_id and store_id combination
        """
        conn = self._get_connection()
        try:
            # Check if stock record exists
            query = """
                SELECT id FROM stocks
                WHERE item_id = ? AND store_id = ?
            """
            cursor = conn.execute(query, (item_id, store_id))
            stock = cursor.fetchone()

            if stock:
                return stock["id"]
            else:
                # Create new stock record if it doesn't exist
                insert_query = """
                    INSERT INTO stocks (item_id, store_id, min_quantity, max_quantity, created_at, updated_at)
                    VALUES (?, ?, 0, NULL, ?, ?)
                """
                current_time = datetime.now().isoformat()
                cursor = conn.execute(
                    insert_query, (item_id, store_id, current_time, current_time)
                )
                stock_id = cursor.lastrowid
                self._commit_and_close(conn)
                logger.info(
                    f"Created new stock record with ID: {stock_id} for item_id: {item_id}, store_id: {store_id}"
                )
                return stock_id
        except sqlite3.Error as e:
            logger.error(f"Error getting/creating stock_id: {str(e)}")
            self._rollback_and_close(conn)
            raise

    def get_stores(self):
        """
        Retrieve all available stores
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT id, name FROM stores")
            stores = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return stores
        except sqlite3.Error as e:
            logger.error(f"Error retrieving stores: {str(e)}")
            conn.close()
            raise
