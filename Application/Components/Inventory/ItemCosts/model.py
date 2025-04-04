import logging
import sqlite3
from Helper.db_conn import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CostStockViewManager:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_connection(self):
        """Get a database connection using DatabaseManager's context manager"""
        conn = self.db_manager.get_connection()
        conn.row_factory = sqlite3.Row  # Set row_factory to return dict-like rows
        return conn

    def get_cost_stock_data(self, store_id=None):
        """Fetch cost and stock data for all items, optionally filtered by store_id"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT
                        i.id as item_id,
                        i.name as item_name,
                        COALESCE(ist.stock_quantity, 0.00) as stock_quantity,
                        COALESCE(s.min_quantity, 0.00) as min_quantity,
                        COALESCE(s.max_quantity, 0.00) as max_quantity,
                        ic.amount as purchase_rate,
                        ic.unit_id as purchase_unit_id,
                        u1.name as purchase_unit_name,
                        ip.amount as selling_rate,
                        ip.unit_id as selling_unit_id,
                        u2.name as selling_unit_name,
                        t.name as tax_name,
                        t.id as tax_id
                    FROM items i
                    LEFT JOIN item_stocks ist ON i.id = ist.item_id
                    LEFT JOIN stocks s ON ist.stock_id = s.id
                    LEFT JOIN item_stores istores ON i.id = istores.item_id
                    LEFT JOIN item_costs ic ON i.id = ic.item_id AND istores.store_id = ic.store_id
                    LEFT JOIN item_prices ip ON i.id = ip.item_id AND istores.store_id = ip.store_id
                    LEFT JOIN item_taxes it ON i.id = it.item_id AND istores.store_id = it.store_id
                    LEFT JOIN taxes t ON it.tax_id = t.id
                    LEFT JOIN units u1 ON ic.unit_id = u1.id
                    LEFT JOIN units u2 ON ip.unit_id = u2.id
                """
                params = []
                if store_id is not None:
                    query += " WHERE istores.store_id = ?"
                    params.append(store_id)

                cursor.execute(query, params)
                results = cursor.fetchall()
                data = []
                column_names = [description[0] for description in cursor.description]
                for row in results:
                    item = {}
                    for i, value in enumerate(row):
                        item[column_names[i]] = value
                    data.append(item)

                logger.info(
                    f"Fetched cost and stock data for store_id {store_id}: {len(data)} records"
                )
                return {"success": True, "data": data}
        except sqlite3.Error as e:
            logger.error(f"Error fetching cost and stock data: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_stores(self):
        """Fetch all stores from the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM stores")
                stores = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
                logger.info(f"Fetched {len(stores)} stores")
                return {"success": True, "data": stores}
        except sqlite3.Error as e:
            logger.error(f"Error fetching stores: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_units(self):
        """Fetch all units from the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM units")
                units = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
                logger.info(f"Fetched {len(units)} units")
                return {"success": True, "data": units}
        except sqlite3.Error as e:
            logger.error(f"Error fetching units: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_taxes(self):
        """Fetch all taxes from the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM taxes")
                taxes = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
                logger.info(f"Fetched {len(taxes)} taxes")
                return {"success": True, "data": taxes}
        except sqlite3.Error as e:
            logger.error(f"Error fetching taxes: {str(e)}")
            return {"success": False, "message": str(e)}

    def update_cost_stock_data(self, items):
        """Update cost and stock data for multiple items"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for item in items:
                    item_id = item["item_id"]
                    store_id = item["store_id"]

                    # Update stocks table
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO stocks 
                        (item_id, store_id, min_quantity, max_quantity, created_at, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                        (
                            item_id,
                            store_id,
                            item.get("min_quantity", 0.00),
                            item.get("max_quantity", 0.00),
                        ),
                    )

                    # Update item_stocks table
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO item_stocks 
                        (item_id, stock_id, stock_quantity, created_at, updated_at)
                        VALUES (?, (SELECT id FROM stocks WHERE item_id = ? AND store_id = ?), ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                        (item_id, item_id, store_id, item.get("stock_quantity", 0.00)),
                    )

                    # Update item_costs table
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO item_costs 
                        (item_id, store_id, unit_id, amount, created_at, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                        (
                            item_id,
                            store_id,
                            item.get("purchase_unit_id"),
                            item.get("purchase_rate", 0.00),
                        ),
                    )

                    # Update item_prices table
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO item_prices 
                        (item_id, store_id, unit_id, amount, created_at, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                        (
                            item_id,
                            store_id,
                            item.get("selling_unit_id"),
                            item.get("selling_rate", 0.00),
                        ),
                    )

                    # Update item_taxes table if tax_id is provided
                    if item.get("tax_id"):
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO item_taxes 
                            (item_id, store_id, tax_id, created_at, updated_at)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                            (item_id, store_id, item["tax_id"]),
                        )

                conn.commit()
                logger.info(f"Updated cost and stock data for {len(items)} items")
                return {
                    "success": True,
                    "message": f"Updated {len(items)} items successfully",
                }

        except sqlite3.Error as e:
            logger.error(f"Error updating cost and stock data: {str(e)}")
            return {"success": False, "message": str(e)}
