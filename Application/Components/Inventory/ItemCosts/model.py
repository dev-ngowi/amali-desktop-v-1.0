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

    def get_cost_stock_data(self):
        """Fetch cost and stock data for all items, aggregated across all stores"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT
                        i.id as item_id,
                        i.name as item_name,
                        MAX(COALESCE(ist.stock_quantity, 0.00)) as stock_quantity,
                        MAX(COALESCE(s.min_quantity, 0.00)) as min_quantity,
                        MAX(COALESCE(s.max_quantity, 0.00)) as max_quantity,
                        AVG(COALESCE(ic.amount, 0.00)) as purchase_rate,
                        MAX(ic.unit_id) as purchase_unit_id,
                        (SELECT u1.name
                         FROM units u1
                         WHERE u1.id = (
                             SELECT ic2.unit_id
                             FROM item_costs ic2
                             WHERE ic2.item_id = i.id
                             ORDER BY ic2.id DESC
                             LIMIT 1
                         )) as purchase_unit_name,
                        AVG(COALESCE(ip.amount, 0.00)) as selling_rate,
                        MAX(ip.unit_id) as selling_unit_id,
                        (SELECT u2.name
                         FROM units u2
                         WHERE u2.id = (
                             SELECT ip2.unit_id
                             FROM item_prices ip2
                             WHERE ip2.item_id = i.id
                             ORDER BY ip2.id DESC
                             LIMIT 1
                         )) as selling_unit_name,
                        (SELECT t.name
                         FROM taxes t
                         JOIN item_taxes it ON t.id = it.tax_id
                         WHERE it.item_id = i.id
                         ORDER BY t.id DESC
                         LIMIT 1) as tax_name,
                        (SELECT t.id
                         FROM taxes t
                         JOIN item_taxes it ON t.id = it.tax_id
                         WHERE it.item_id = i.id
                         ORDER BY t.id DESC
                         LIMIT 1) as tax_id
                    FROM items i
                    LEFT JOIN item_stocks ist ON i.id = ist.item_id
                    LEFT JOIN stocks s ON ist.stock_id = s.id
                    LEFT JOIN item_costs ic ON i.id = ic.item_id
                    LEFT JOIN item_prices ip ON i.id = ip.item_id
                    LEFT JOIN item_taxes it ON i.id = it.item_id
                    LEFT JOIN taxes t ON it.tax_id = t.id
                    LEFT JOIN units u1 ON ic.unit_id = u1.id
                    LEFT JOIN units u2 ON ip.unit_id = u2.id
                    GROUP BY i.id, i.name
                """
                cursor.execute(query)
                data = [dict(row) for row in cursor.fetchall()]
                logger.info(f"Fetched {len(data)} unique items")
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
        """Update cost and stock data for multiple items without store association"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for item in items:
                    item_id = item["item_id"]

                    # Update stocks table (without store_id)
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO stocks
                        (item_id, min_quantity, max_quantity, created_at, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (
                            item_id,
                            item.get("min_quantity", 0.00),
                            item.get("max_quantity", 0.00),
                        ),
                    )

                    # Update item_stocks table (using the latest stock entry)
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO item_stocks
                        (item_id, stock_id, stock_quantity, created_at, updated_at)
                        VALUES (?, (SELECT id FROM stocks WHERE item_id = ? ORDER BY updated_at DESC LIMIT 1), ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (item_id, item_id, item.get("stock_quantity", 0.00)),
                    )

                    # Update item_costs table (without store_id)
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO item_costs
                        (item_id, unit_id, amount, created_at, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (
                            item_id,
                            item.get("purchase_unit_id"),
                            item.get("purchase_rate", 0.00),
                        ),
                    )

                    # Update item_prices table (without store_id)
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO item_prices
                        (item_id, unit_id, amount, created_at, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (
                            item_id,
                            item.get("selling_unit_id"),
                            item.get("selling_rate", 0.00),
                        ),
                    )

                    # Update item_taxes table if tax_id is provided (without store_id)
                    if item.get("tax_id"):
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO item_taxes
                            (item_id, tax_id, created_at, updated_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """,
                            (item_id, item["tax_id"]),
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

