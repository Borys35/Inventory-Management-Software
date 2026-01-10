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

    def create(self, sku, name, description, manufacturer_id, reorder_level):
        # Ta funkcja mogła już tu być, zostawiamy ją dla porządku
        try:
            cur = self.conn.cursor()
            query = """
                INSERT INTO products (sku, name, description, manufacturer_id, reorder_level)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """
            cur.execute(query, (sku, name, description, manufacturer_id, reorder_level))
            new_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating product: {e}")
            return None
    
    # def create_product(self, sku, name, description, supplier_id, manufacturer_id, reorder_level):
    #     try:
    #         cur = self.conn.cursor()
    #         query = """
    #             INSERT INTO products (sku, name, description, supplier_id, manufacturer_id, reorder_level)
    #             VALUES (%s, %s, %s, %s, %s, %s)
    #             RETURNING id;
    #         """
    #         cur.execute(query, (sku, name, description, supplier_id, manufacturer_id, reorder_level))
            
    #         new_id = cur.fetchone()[0]
    #         self.conn.commit()
    #         cur.close()
    #         return new_id
    #     except Exception as e:
    #         self.conn.rollback()
    #         print(f"Error while creating product: {e}")
    #         return None
        
    def update_product(self, id, sku, name, description, manufacturer_id, reorder_level):
        try:
            cur = self.conn.cursor()
            query = """
                UPDATE products
                SET 
                    sku = %s,
                    name = %s, 
                    description = %s, 
                    manufacturer_id = %s,
                    reorder_level = %s
                WHERE 
                    id = %s
                RETURNING id;
            """
            cur.execute(query, (sku, name, description, manufacturer_id, reorder_level, id))
            updated_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return updated_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error while updating product: {e}")
            return None

    def delete_product(self, id):
        try:
            cur = self.conn.cursor()
            query = """
                DELETE FROM products
                WHERE id = %s
                RETURNING id;
            """
            cur.execute(query, (id, ))
            deleted_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return deleted_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error while deleting product: {e}")
            return None
    
    def get_product_by_id(self, id):
        try:
            cur = self.conn.cursor()
            query = """
                SELECT * FROM products WHERE id = %s;
            """
            cur.execute(query, (id, ))
            row = cur.fetchone()
            cur.close()
            print(row)
            
            if row:
                return {
                    'id': row[0],
                    'sku': row[1],
                    'name': row[2],
                    # 'quantity': row[3],
                    'description': row[3],
                    'specifications': row[4],
                    # 'supplier_id': row[6],
                    'manufacturer_id': row[5],
                    'reorder_level': row[6],
                    'created_at': row[7]
                }
            return None
        except Exception as e:
            self.conn.rollback()
            print(f"Error while getting product by id: {e}")
            return None
    
    # def get_products(self):
    #     try:
    #         cur = self.conn.cursor()
    #         query = """
    #             SELECT * FROM products;
    #         """
    #         cur.execute(query)
    #         rows = cur.fetchall()
    #         cur.close()

    #         def extract_dict(row):
    #             return {
    #                 'id': row[0],
    #                 'sku': row[1],
    #                 'name': row[2],
    #                 'quantity': row[3],
    #                 'description': row[4],
    #                 'specifications': row[5],
    #                 'supplier_id': row[6],
    #                 'manufacturer_id': row[7],
    #                 'reorder_level': row[8],
    #                 'created_at': row[9]
    #             }
            
    #         if rows:
    #             return list(map(extract_dict, rows))
    #         return []
    #     except Exception as e:
    #         self.conn.rollback()
    #         print(f"Error while getting products: {e}")
    #         return None