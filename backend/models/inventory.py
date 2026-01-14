class Inventory:
    def __init__(self, db_connection):
        self.conn = db_connection

    def get_stock_levels(self, search_query=None):
        try:
            cur = self.conn.cursor()
            
            # Zakładam, że masz widok v_stock_levels albo pobieramy z produktów
            # Jeśli nie masz widoku, to zapytanie pobierze po prostu produkty
            query = """
                SELECT p.name, p.sku, 0 as current_quantity, p.reorder_level
                FROM products p
            """
            
            params = ()

            if search_query:
                query += " WHERE p.name ILIKE %s OR p.sku ILIKE %s"
                search_term = f"%{search_query}%"
                params = (search_term, search_term)
            
            query += " ORDER BY p.name ASC;"

            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()

            stock = []
            for row in rows:
                stock.append({
                    'product_name': row[0],
                    'sku': row[1],
                    'current_quantity': row[2], # Tu docelowo będzie suma z magazynu
                    'reorder_level': row[3]
                })
            return stock
        except Exception as e:
            print(f"Error getting stock levels: {e}")
            return []