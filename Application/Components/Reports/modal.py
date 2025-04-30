# modal.py (in Application/Components/Reports/)
from datetime import datetime, timedelta
import logging
import sqlite3
from Helper.db_conn import DatabaseManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ReportManager:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_connection(self):
        with self.db_manager.lock:
            conn = sqlite3.connect(self.db_manager.db_path, timeout=30)
        return conn

    def _commit_and_close(self, conn):
        try:
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error committing changes: {str(e)}")
        finally:
            conn.close()

    def get_stores_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name FROM stores")
            stores = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(stores)} stores.")
            return stores
        except sqlite3.Error as e:
            logger.error(f"Error retrieving stores data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_company_details(self):
        try:
            with self._get_connection() as conn:
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
            logger.error(f"Database error getting company details: {e}")
            return []

    def get_sales_summary_data(self, start_date, end_date, store_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        sales_data = []
        try:
            query = """
            SELECT DATE(date),
                   SUM(total_amount),
                   SUM(discount),
                   SUM(tip),
                   SUM(ground_total)
            FROM orders
            WHERE DATE(date) BETWEEN ? AND ?
            AND status = 'completed'
            """
            params = (start_date, end_date)

            if store_id is not None:
                query += " AND store_id = ?"
                params += (store_id,)

            query += " GROUP BY DATE(date) ORDER BY DATE(date)"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                sales_data.append(
                    {
                        "date": row[0],
                        "sub_total": float(row[1]) if row[1] is not None else 0.00,
                        "tax_total": 0.00,  # Assuming tax is not separate
                        "discount": float(row[2]) if row[2] is not None else 0.00,
                        "others": 0.00,
                        "tip": float(row[3]) if row[3] is not None else 0.00,
                        "ground_total": float(row[4]) if row[4] is not None else 0.00,
                        "payment_total": float(row[4]) if row[4] is not None else 0.00,
                        "amount_due": 0.00,
                    }
                )
            return sales_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving sales summary data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_sales_detailed_data(self, start_date, end_date, store_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        sales_data = []
        try:
            query = """
            SELECT o.order_number, o.date, o.discount, o.ground_total,
                   i.name AS item_name, oi.quantity, oi.price
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN items i ON oi.item_id = i.id
            WHERE DATE(o.date) BETWEEN ? AND ?
            AND o.status = 'completed'
            """
            params = (start_date, end_date)

            if store_id is not None:
                query += " AND o.store_id = ?"
                params += (store_id,)

            query += " ORDER BY o.date, o.order_number"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            orders_dict = {}
            for row in rows:
                order_number = row[0]
                if order_number not in orders_dict:
                    orders_dict[order_number] = {
                        "order_number": order_number,
                        "date": row[1],
                        "discount": float(row[2]) if row[2] is not None else 0.00,
                        "ground_total": float(row[3]) if row[3] is not None else 0.00,
                        "items": [],
                    }
                if row[4]:  # Check if item_name exists
                    orders_dict[order_number]["items"].append(
                        {
                            "item_name": row[4],
                            "quantity": row[5],
                            "price": float(row[6]),
                            "total": float(row[5] * row[6]),
                        }
                    )

            sales_data = list(orders_dict.values())
            return sales_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving sales detailed data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_top_selling_items_data(self, start_date, end_date, store_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        top_items_data = []
        try:
            query = """
            SELECT i.name AS item_name,
                   SUM(oi.quantity) AS total_quantity,
                   SUM(oi.quantity * oi.price) AS total_revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN items i ON i.id = oi.item_id
            WHERE DATE(o.date) BETWEEN ? AND ?
            AND o.status = 'completed'
            """
            params = (start_date, end_date)

            if store_id is not None:
                query += " AND o.store_id = ?"
                params += (store_id,)

            query += """
            GROUP BY i.id, i.name
            ORDER BY total_quantity DESC
            LIMIT 50
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                total_quantity = row[1]
                total_revenue = float(row[2]) if row[2] is not None else 0.00
                average_price = (
                    total_revenue / total_quantity if total_quantity > 0 else 0.00
                )
                top_items_data.append(
                    {
                        "item_name": row[0],
                        "total_quantity": total_quantity,
                        "total_revenue": total_revenue,
                        "average_price": average_price,
                    }
                )

            logger.info(
                f"Processed {len(top_items_data)} top selling items "
                f"between {start_date} and {end_date}."
            )
            return top_items_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving top selling items data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_stock_ledger_data(self, start_date, end_date, store_id=None, item_id=None):
        """
        Fetch stock ledger data for a given period, store, and optional item.
        Uses good_receive_note_items for inflows and order_items for outflows.
        Returns opening balance and stock movements.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        stock_ledger_data = []
        try:
            # Step 1: Get all relevant items (filtered by item_id if provided)
            items_query = """
            SELECT i.id, i.name
            FROM items i
            """
            items_params = []
            if item_id is not None:
                items_query += " WHERE i.id = ?"
                items_params.append(item_id)

            cursor.execute(items_query, items_params)
            items = cursor.fetchall()

            for item in items:
                item_id = item[0]
                item_name = item[1]

                # Step 2: Calculate opening balance (stock quantity before start_date)
                # Sum inflows from good_receive_note_items before start_date
                inflow_query = """
                SELECT COALESCE(SUM(ri.accepted_quantity), 0)
                FROM good_receive_note_items ri
                JOIN good_receipt_notes grn ON ri.grn_id = grn.id
                WHERE ri.item_id = ?
                AND grn.received_date < ?
                """
                inflow_params = [item_id, start_date]

                if store_id is not None:
                    inflow_query += """
                    AND grn.store_id = ?
                    """
                    inflow_params.append(store_id)

                cursor.execute(inflow_query, inflow_params)
                total_inflow = cursor.fetchone()[0] or 0

                # Sum outflows from order_items (sales) before start_date
                outflow_query = """
                SELECT COALESCE(SUM(oi.quantity), 0)
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE oi.item_id = ?
                AND o.date < ?
                AND o.status = 'completed'
                """
                outflow_params = [item_id, start_date]

                if store_id is not None:
                    outflow_query += """
                    AND o.store_id = ?
                    """
                    outflow_params.append(store_id)

                cursor.execute(outflow_query, outflow_params)
                total_outflow = cursor.fetchone()[0] or 0

                opening_balance = total_inflow - total_outflow  # Outflows reduce stock

                # Step 3: Fetch stock movements within the date range
                # Inflows from good_receive_note_items
                inflow_movements_query = """
                SELECT grn.received_date AS movement_date,
                       'receipt' AS movement_type,
                       ri.accepted_quantity AS quantity,
                       grn.grn_number AS reference
                FROM good_receive_note_items ri
                JOIN good_receipt_notes grn ON ri.grn_id = grn.id
                WHERE ri.item_id = ?
                AND grn.received_date BETWEEN ? AND ?
                """
                inflow_movements_params = [item_id, start_date, end_date]

                if store_id is not None:
                    inflow_movements_query += """
                    AND grn.store_id = ?
                    """
                    inflow_movements_params.append(store_id)

                cursor.execute(inflow_movements_query, inflow_movements_params)
                inflow_movements = cursor.fetchall()

                # Outflows from order_items (sales)
                outflow_movements_query = """
                SELECT o.date AS movement_date,
                       'sale' AS movement_type,
                       oi.quantity AS quantity,
                       o.order_number AS reference
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE oi.item_id = ?
                AND o.date BETWEEN ? AND ?
                AND o.status = 'completed'
                """
                outflow_movements_params = [item_id, start_date, end_date]

                if store_id is not None:
                    outflow_movements_query += """
                    AND o.store_id = ?
                    """
                    outflow_movements_params.append(store_id)

                cursor.execute(outflow_movements_query, outflow_movements_params)
                outflow_movements = cursor.fetchall()

                # Combine and sort movements by date
                all_movements = []
                for movement in inflow_movements:
                    all_movements.append(
                        {
                            "movement_date": movement[0],
                            "movement_type": movement[1],
                            "quantity": movement[2],
                            "reference": movement[3],
                        }
                    )
                for movement in outflow_movements:
                    all_movements.append(
                        {
                            "movement_date": movement[0],
                            "movement_type": movement[1],
                            "quantity": -movement[2],  # Negative for outflows
                            "reference": movement[3],
                        }
                    )

                all_movements.sort(key=lambda x: x["movement_date"])

                # Step 4: Build the ledger entries
                current_balance = opening_balance
                ledger_entries = []

                # Add opening balance as the first entry
                ledger_entries.append(
                    {
                        "item_id": item_id,
                        "item_name": item_name,
                        "date": start_date,
                        "reference": "Opening Balance",
                        "inflow": 0,
                        "outflow": 0,
                        "balance": current_balance,
                    }
                )

                # Process each movement
                for movement in all_movements:
                    movement_date = movement["movement_date"]
                    movement_type = movement["movement_type"]
                    quantity = movement["quantity"]
                    reference = movement["reference"] or "Unknown"

                    inflow = quantity if quantity > 0 else 0
                    outflow = -quantity if quantity < 0 else 0
                    current_balance += quantity

                    ledger_entries.append(
                        {
                            "item_id": item_id,
                            "item_name": item_name,
                            "date": movement_date,
                            "reference": reference,
                            "inflow": inflow,
                            "outflow": outflow,
                            "balance": current_balance,
                        }
                    )

                stock_ledger_data.extend(ledger_entries)

            logger.info(
                f"Processed stock ledger data for {len(items)} items "
                f"between {start_date} and {end_date}."
            )
            return stock_ledger_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving stock ledger data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    def get_stock_level_data(self, store_id=None, item_id=None):
        """
        Fetch current stock levels for items, optionally filtered by store and item.
        Returns a list of stock levels with item name, store name, stock quantity,
        minimum quantity, maximum quantity, and status.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        stock_level_data = []
        try:
            query = """
            SELECT i.id, i.name AS item_name,
                   s.id AS store_id, s.name AS store_name,
                   ist.stock_quantity,
                   st.min_quantity, st.max_quantity
            FROM item_stocks ist
            JOIN items i ON ist.item_id = i.id
            JOIN stocks st ON ist.stock_id = st.id
            JOIN stores s ON st.store_id = s.id
            WHERE 1=1
            """
            params = []

            if store_id is not None:
                query += " AND s.id = ?"
                params.append(store_id)

            if item_id is not None:
                query += " AND i.id = ?"
                params.append(item_id)

            query += " ORDER BY i.name, s.name"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                item_id = row[0]
                item_name = row[1]
                store_id = row[2]
                store_name = row[3]
                stock_quantity = row[4] or 0
                min_quantity = row[5] or 0
                max_quantity = row[6] or 0

                # Determine stock status
                if stock_quantity < min_quantity:
                    status = "Low"
                elif stock_quantity > max_quantity:
                    status = "High"
                else:
                    status = "Normal"

                stock_level_data.append(
                    {
                        "item_id": item_id,
                        "item_name": item_name,
                        "store_id": store_id,
                        "store_name": store_name,
                        "stock_quantity": stock_quantity,
                        "min_quantity": min_quantity,
                        "max_quantity": max_quantity,
                        "status": status,
                    }
                )

            logger.info(
                f"Processed stock level data for {len(stock_level_data)} items."
            )
            return stock_level_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving stock level data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)

    # In modal.py, add this method to the ReportManager class

    def get_dead_stock_data(self, days_threshold=90, store_id=None):
        """
        Fetch dead stock data: items with no sales in the last 'days_threshold' days.
        Returns a list of items with their current stock levels and last sale date (if any).
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        dead_stock_data = []
        try:
            # Calculate the cutoff date
            from datetime import datetime, timedelta

            cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime(
                "%Y-%m-%d"
            )

            query = """
            SELECT 
                i.id AS item_id,
                i.name AS item_name,
                s.id AS store_id,
                s.name AS store_name,
                ist.stock_quantity,
                st.min_quantity,
                st.max_quantity,
                (SELECT MAX(o.date) 
                FROM order_items oi 
                JOIN orders o ON oi.order_id = o.id 
                WHERE oi.item_id = i.id 
                AND o.status = 'completed'
                AND o.store_id = s.id) AS last_sale_date
            FROM item_stocks ist
            JOIN items i ON ist.item_id = i.id
            JOIN stocks st ON ist.stock_id = st.id
            JOIN stores s ON st.store_id = s.id
            WHERE 1=1
            """
            params = []

            if store_id is not None:
                query += " AND s.id = ?"
                params.append(store_id)

            # Only include items with stock > 0
            query += " AND ist.stock_quantity > 0"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                item_id = row[0]
                item_name = row[1]
                store_id = row[2]
                store_name = row[3]
                stock_quantity = row[4] or 0
                min_quantity = row[5] or 0
                max_quantity = row[6] or 0
                last_sale_date = row[7]  # Could be None if no sales

                # Consider it dead stock if no sales ever or last sale is before cutoff
                is_dead = last_sale_date is None or last_sale_date < cutoff_date

                if is_dead:
                    dead_stock_data.append(
                        {
                            "item_id": item_id,
                            "item_name": item_name,
                            "store_id": store_id,
                            "store_name": store_name,
                            "stock_quantity": stock_quantity,
                            "min_quantity": min_quantity,
                            "max_quantity": max_quantity,
                            "last_sale_date": (
                                last_sale_date if last_sale_date else "Never Sold"
                            ),
                        }
                    )

            logger.info(
                f"Processed dead stock data for {len(dead_stock_data)} items with threshold {days_threshold} days."
            )
            return dead_stock_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving dead stock data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)
    def get_expenses_data(self, start_date=None, end_date=None, expense_type=None, store_id=None):
        """
        Fetch expense data from the expenses table, optionally filtered by date range, expense type, and store.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        expenses_data = []
        try:
            query = """
            SELECT 
                e.expense_date,
                e.expense_type,
                e.amount,
                e.description,
                e.reference_number,
                u.fullname AS user_name,
                i.name AS linked_item_name,
                s.name AS store_name
            FROM expenses e
            LEFT JOIN users u ON e.user_id = u.id
            LEFT JOIN items i ON e.linked_shop_item_id = i.id
            LEFT JOIN stocks st ON i.id = st.item_id
            LEFT JOIN stores s ON st.store_id = s.id
            WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND e.expense_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND e.expense_date <= ?"
                params.append(end_date)
            if expense_type:
                query += " AND e.expense_type = ?"
                params.append(expense_type)
            if store_id:
                query += " AND s.id = ?"
                params.append(store_id)

            query += " ORDER BY e.expense_date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                expenses_data.append({
                    "expense_date": row[0],
                    "expense_type": row[1],
                    "amount": float(row[2]) if row[2] is not None else 0.0,
                    "description": row[3] or "No description",
                    "reference_number": row[4] or "N/A",
                    "user_name": row[5] or "Unknown",
                    "linked_item_name": row[6] or "N/A",
                    "store_name": row[7] or "N/A",
                })

            logger.info(f"Retrieved {len(expenses_data)} expense records.")
            return expenses_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving expenses data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)
            
    def get_expenses_detailed_data(self, start_date=None, end_date=None, expense_type=None, store_id=None):
        """
        Fetch detailed expense data, including associated items, optionally filtered by date range, expense type, and store.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        expenses_data = []
        try:
            query = """
            SELECT 
                e.id AS expense_id,
                e.expense_date,
                e.expense_type,
                e.amount AS total_amount,
                e.description,
                e.reference_number,
                u.fullname AS user_name,
                i.id AS item_id,
                i.name AS item_name,
                s.name AS store_name
            FROM expenses e
            LEFT JOIN users u ON e.user_id = u.id
            LEFT JOIN expense_items ei ON e.id = ei.expense_id
            LEFT JOIN items i ON ei.item_id = i.id
            LEFT JOIN stocks st ON i.id = st.item_id
            LEFT JOIN stores s ON st.store_id = s.id
            WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND e.expense_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND e.expense_date <= ?"
                params.append(end_date)
            if expense_type:
                query += " AND e.expense_type = ?"
                params.append(expense_type)
            if store_id:
                query += " AND s.id = ?"
                params.append(store_id)

            query += " ORDER BY e.expense_date DESC, e.id"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Group data by expense_id to handle multiple items per expense
            expense_dict = {}
            for row in rows:
                expense_id = row[0]
                if expense_id not in expense_dict:
                    expense_dict[expense_id] = {
                        "expense_date": row[1],
                        "expense_type": row[2],
                        "total_amount": float(row[3]) if row[3] is not None else 0.0,
                        "description": row[4] or "No description",
                        "reference_number": row[5] or "N/A",
                        "user_name": row[6] or "Unknown",
                        "store_name": row[9] or "N/A",
                        "items": []
                    }
                if row[7]:  # If item_id exists
                    expense_dict[expense_id]["items"].append({
                        "item_id": row[7],
                        "item_name": row[8] or "N/A"
                    })

            # Convert to list format for the report
            for expense_id, data in expense_dict.items():
                if not data["items"]:  # Handle expenses with no linked items
                    expenses_data.append({
                        "expense_id": expense_id,
                        "expense_date": data["expense_date"],
                        "expense_type": data["expense_type"],
                        "total_amount": data["total_amount"],
                        "description": data["description"],
                        "reference_number": data["reference_number"],
                        "user_name": data["user_name"],
                        "store_name": data["store_name"],
                        "item_name": "N/A"
                    })
                else:
                    for item in data["items"]:
                        expenses_data.append({
                            "expense_id": expense_id,
                            "expense_date": data["expense_date"],
                            "expense_type": data["expense_type"],
                            "total_amount": data["total_amount"],
                            "description": data["description"],
                            "reference_number": data["reference_number"],
                            "user_name": data["user_name"],
                            "store_name": data["store_name"],
                            "item_name": item["item_name"]
                        })

            logger.info(f"Retrieved {len(expenses_data)} detailed expense records.")
            return expenses_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving detailed expenses data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)
    
    def get_daily_financials_data(self, start_date=None, end_date=None):
        """
        Fetch daily financial data, optionally filtered by date range.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        financials_data = []
        try:
            query = """
            SELECT 
                date,
                total_orders,
                total_expenses,
                after_expenses
            FROM daily_financials
            WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                financials_data.append({
                    "date": row[0],
                    "total_orders": float(row[1]) if row[1] is not None else 0.0,
                    "total_expenses": float(row[2]) if row[2] is not None else 0.0,
                    "after_expenses": float(row[3]) if row[3] is not None else 0.0,
                })

            logger.info(f"Retrieved {len(financials_data)} daily financial records.")
            return financials_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving daily financials data: {str(e)}")
            return []
        finally:
            self._commit_and_close(conn)
    


    def get_business_health_data(self, store_id=None):
        """
        Fetch aggregated transaction data for day, week, month, and year periods.
        Includes current balance, profit (item_price - item_cost * sold_quantity), and loss.
        Optionally filter by store_id.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        health_data = {}
        try:
            # Use dynamic dates
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday() + 1)  # Last Sunday
            month_start = today.replace(day=1)  # First of current month
            year_start = today.replace(month=1, day=1)  # First of current year

            periods = {
                "Day": (today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
                "Week": (week_start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
                "Month": (month_start.strftime('%Y-%m-%m-%d'), today.strftime('%Y-%m-%d')),
                "Year": (year_start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
            }

            # Calculate current balance (cumulative up to today)
            total_profit_query = """
                SELECT SUM((ip.amount - COALESCE(ic.amount, 0)) * oi.quantity)
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                JOIN item_prices ip ON oi.item_id = ip.item_id AND ip.store_id = o.store_id
                LEFT JOIN item_costs ic ON oi.item_id = ic.item_id AND ic.store_id = o.store_id
                WHERE o.status IN ('completed', 'settled')
                AND o.date <= ?
            """
            total_expenses_query = """
                SELECT SUM(amount)
                FROM expenses
                WHERE expense_date <= ?
            """
            # Initialize params separately for each query to avoid overlap
            profit_params = [today.strftime('%Y-%m-%d')]
            expenses_params = [today.strftime('%Y-%m-%d')]

            if store_id:
                total_profit_query += " AND o.store_id = ?"
                profit_params.append(store_id)
                
                total_expenses_query += """
                    AND EXISTS (
                        SELECT 1 FROM expense_items ei
                        JOIN items i ON ei.item_id = i.id
                        JOIN stocks st ON i.id = st.item_id
                        WHERE ei.expense_id = expenses.id AND st.store_id = ?
                    )
                """
                expenses_params.append(store_id)

            cursor.execute(total_profit_query, profit_params)
            total_profit = cursor.fetchone()[0] or 0.0
            cursor.execute(total_expenses_query, expenses_params)
            total_expenses = cursor.fetchone()[0] or 0.0
            current_balance = total_profit - total_expenses

            for period_name, (start_date, end_date) in periods.items():
                # Total Sales (Revenue from orders)
                sales_query = """
                    SELECT SUM(o.ground_total)
                    FROM orders o
                    WHERE o.date BETWEEN ? AND ?
                    AND o.status IN ('completed', 'settled')
                """
                params = [start_date, end_date]
                if store_id:
                    sales_query += " AND o.store_id = ?"
                    params.append(store_id)
                cursor.execute(sales_query, params)
                total_sales = cursor.fetchone()[0] or 0.0

                # Profit: (item_price - item_cost) * sold_quantity
                profit_query = """
                    SELECT SUM((ip.amount - COALESCE(ic.amount, 0)) * oi.quantity)
                    FROM order_items oi
                    JOIN orders o ON oi.order_id = o.id
                    JOIN item_prices ip ON oi.item_id = ip.item_id AND ip.store_id = o.store_id
                    LEFT JOIN item_costs ic ON oi.item_id = ic.item_id AND ic.store_id = o.store_id
                    WHERE o.date BETWEEN ? AND ?
                    AND o.status IN ('completed', 'settled')
                """
                params = [start_date, end_date]
                if store_id:
                    profit_query += " AND o.store_id = ?"
                    params.append(store_id)
                cursor.execute(profit_query, params)
                profit = cursor.fetchone()[0] or 0.0

                # Loss: Where item_cost > item_price for sold items
                loss_query = """
                    SELECT SUM((ic.amount - ip.amount) * oi.quantity)
                    FROM order_items oi
                    JOIN orders o ON oi.order_id = o.id
                    JOIN item_prices ip ON oi.item_id = ip.item_id AND ip.store_id = o.store_id
                    JOIN item_costs ic ON oi.item_id = ic.item_id AND ic.store_id = o.store_id
                    WHERE o.date BETWEEN ? AND ?
                    AND o.status IN ('completed', 'settled')
                    AND ic.amount > ip.amount
                """
                params = [start_date, end_date]
                if store_id:
                    loss_query += " AND o.store_id = ?"
                    params.append(store_id)
                cursor.execute(loss_query, params)
                loss = cursor.fetchone()[0] or 0.0

                # Expenses
                expenses_query = """
                    SELECT SUM(amount)
                    FROM expenses
                    WHERE expense_date BETWEEN ? AND ?
                """
                params = [start_date, end_date]
                if store_id:
                    expenses_query += """
                        AND EXISTS (
                            SELECT 1 FROM expense_items ei
                            JOIN items i ON ei.item_id = i.id
                            JOIN stocks st ON i.id = st.item_id
                            WHERE ei.expense_id = expenses.id AND st.store_id = ?
                        )
                    """
                    params.append(store_id)
                cursor.execute(expenses_query, params)
                total_expenses = cursor.fetchone()[0] or 0.0

                health_data[period_name] = {
                    "total_sales": float(total_sales),
                    "total_expenses": float(total_expenses),
                    "profit": float(profit),
                    "loss": float(loss),
                    "current_balance": float(current_balance),
                }

            logger.info(f"Retrieved business health data for periods: {list(health_data.keys())}")
            return health_data
        except sqlite3.Error as e:
            logger.error(f"Error retrieving business health data: {str(e)}")
            return {}
        finally:
            self._commit_and_close(conn)