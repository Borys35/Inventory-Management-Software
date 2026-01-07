class Product:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def get_all(self):
        try:
            cur = self.conn.cursor()
            # Pobieramy produkty
            cur.execute("SELECT * FROM products ORDER BY id DESC;")
            rows = cur.fetchall()
            cur.close()
            
            products = []
            for row in rows:
                products.append({
                    'id': row[0],
                    'sku': row[1],
                    'name': row[2],
                    'description': row[3],
                    # row[4] to specifications (json), pomijamy
                    'manufacturer_id': row[5],
                    'reorder_level': row[6]
                })
            return products
        except Exception as e:
            print(f"Błąd pobierania produktów: {e}")
            return []

    def create(self, sku, name, description, manufacturer_id):
        # Ta funkcja mogła już tu być, zostawiamy ją dla porządku
        try:
            cur = self.conn.cursor()
            query = """
                INSERT INTO products (sku, name, description, manufacturer_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """
            cur.execute(query, (sku, name, description, manufacturer_id))
            new_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating product: {e}")
            return None