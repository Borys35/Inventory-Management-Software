class Inventory:
    def __init__(self, db_connection):
        self.conn = db_connection

    def get_stock_levels(self, search_query=None, restock_query=None):
        try:
            cur = self.conn.cursor()
            
            query = """
                SELECT *
                FROM v_stock_levels
            """
            
            conditions = []
            params = []

            if search_query:
                conditions.append("(product_name ILIKE %s OR sku ILIKE %s)")
                search_term = f"%{search_query}%"
                params.extend([search_term, search_term])
            
            if restock_query:
                conditions.append("total_quantity <= reorder_level")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY product_name ASC;"

            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            cur.close()

            stock = []
            for row in rows:
                stock.append({
                    'product_name': row[2],
                    'sku': row[1],
                    'current_quantity': row[3],
                    'total_price': row[4],
                    'reorder_level': row[5],
                    'manufacturer': row[6]
                })
            return stock
        except Exception as e:
            print(f"Error getting stock levels: {e}")
            return []