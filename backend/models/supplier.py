class Supplier:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def create_supplier(self, name, contact_email, phone, address):
        try:
            cur = self.conn.cursor()
            query = """
                INSERT INTO suppliers (name, contact_email, phone, address)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """
            cur.execute(query, (name, contact_email, phone, address))
            new_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error while creating supplier: {e}")
            return None
    
    def get_supplier_by_id(self, id):
        try:
            cur = self.conn.cursor()
            query = """
                SELECT * FROM suppliers WHERE id = %s;
            """
            cur.execute(query, (id, ))
            row = cur.fetchone()
            cur.close()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'contact_email': row[2],
                    'phone': row[3],
                    'address': row[4]
                }
            return None
        except Exception as e:
            self.conn.rollback()
            print(f"Error while getting supplier by id: {e}")
            return None
    
    def get_suppliers(self):
        try:
            cur = self.conn.cursor()
            query = """
                SELECT * FROM suppliers;
            """
            cur.execute(query)
            rows = cur.fetchall()
            cur.close()

            def extract_dict(row):
                return {
                    'id': row[0],
                    'name': row[1],
                    'contact_email': row[2],
                    'phone': row[3],
                    'address': row[4]
                }
            
            if rows:
                return list(map(extract_dict, rows))
            return []
        except Exception as e:
            self.conn.rollback()
            print(f"Error while getting suppliers: {e}")
            return None