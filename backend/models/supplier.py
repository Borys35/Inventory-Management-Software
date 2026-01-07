class Supplier:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    # --- Funkcje od Borysa ---
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
        
    def update_supplier(self, id, name, contact_email, phone, address):
        try:
            cur = self.conn.cursor()
            query = """
                UPDATE suppliers
                SET name = %s, contact_email = %s, phone = %s, address = %s
                WHERE id = %s
                RETURNING id;
            """
            cur.execute(query, (name, contact_email, phone, address, id))
            updated_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return updated_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error while updating supplier: {e}")
            return None
        
    def delete_supplier(self, id):
        try:
            cur = self.conn.cursor()
            query = """
                DELETE FROM suppliers
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
            print(f"Error while deleting supplier: {e}")
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

    # --- TA FUNKCJA JEST KLUCZOWA ---
    def get_all(self):
        return self.get_suppliers()