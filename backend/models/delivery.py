class Delivery:
    def __init__(self, db_connection):
        self.conn = db_connection

    def create_delivery_with_products(self, data, products_list):
        """
        data: słownik z polami (user_id, document_id, supplier_id, customer_id, transaction_type)
        products_list: lista słowników [{'product_id': 1, 'qty': 10, 'price': 5.00}, ...]
        """
        try:
            cur = self.conn.cursor()
            
            # 1. Tworzymy Dostawę (Główny rekord)
            query_delivery = """
                INSERT INTO deliveries 
                (user_id, document_id, supplier_id, customer_id, transaction_type, delivery_status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
                RETURNING id;
            """
            cur.execute(query_delivery, (
                data.get('user_id'),
                data.get('document_id'),
                data.get('supplier_id'),
                data.get('customer_id'),
                data.get('transaction_type')
            ))
            delivery_id = cur.fetchone()[0]

            # 2. Dodajemy Produkty (Wiersze)
            # Trigger w bazie sam utworzy potem product_batches
            query_row = """
                INSERT INTO product_rows 
                (delivery_id, product_id, quantity, single_price, total_price)
                VALUES (%s, %s, %s, %s, %s);
            """
            
            for p in products_list:
                qty = int(p['qty'])
                price = float(p['price'])
                total = qty * price
                cur.execute(query_row, (delivery_id, p['product_id'], qty, price, total))

            self.conn.commit()
            cur.close()
            return delivery_id

        except Exception as e:
            self.conn.rollback()
            print(f"BŁĄD TRANSAKCJI DOSTAWY: {e}")
            return None

    def get_all(self):
        # Pobieranie listy dostaw dla podglądu
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT d.id, doc.document_number, d.transaction_type, d.delivery_status, d.created_at
                FROM deliveries d
                LEFT JOIN documents doc ON d.document_id = doc.id
                ORDER BY d.created_at DESC;
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception as e:
            print(f"Error getting deliveries: {e}")
            return []
    
    def get_one(self, id):
        try:
            cur = self.conn.cursor()
            query = """
                SELECT id, delivery_status, transaction_type FROM deliveries WHERE id = %s;
            """
            cur.execute(query, (id, ))
            row = cur.fetchone()
            cur.close()
            
            if row:
                return {
                    'id': row[0],
                    'delivery_status': row[1],
                    'transaction_type': row[2],
                }
            return None
        except Exception as e:
            self.conn.rollback()
            print(f"Error while getting delivery by id: {e}")
            return None
        
    def update(self, id, delivery_status):
        try:
            cur = self.conn.cursor()
            query = """
                UPDATE deliveries 
                SET delivery_status = %s
                WHERE id = %s
                RETURNING id;
            """
            cur.execute(query, (delivery_status, id))
            updated_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return updated_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error while updating delivery by id: {e}")
            return None
