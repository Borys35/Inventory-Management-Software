class Manufacturer:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def create_manufacturer(self, name, contact_email, phone, address):
        try:
            cur = self.conn.cursor()
            query = """
                INSERT INTO manufacturers (name, contact_email, phone, address)
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
            print(f"Error while creating manufacturer: {e}")
            return None
        
    def update_manufacturer(self, id, name, contact_email, phone, address):
        try:
            cur = self.conn.cursor()
            query = """
                UPDATE manufacturers
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
            print(f"Error while updating manufacturer: {e}")
            return None
        
    def delete_manufacturer(self, id):
        try:
            cur = self.conn.cursor()
            query = """
                DELETE FROM manufacturers
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
            print(f"Error while deleting manufacturer: {e}")
            return None
    
    def get_manufacturer_by_id(self, id):
        try:
            cur = self.conn.cursor()
            query = """
                SELECT * FROM manufacturers WHERE id = %s;
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
            print(f"Error while getting manufacturer by id: {e}")
            return None
    
    def get_manufacturers(self):
        try:
            cur = self.conn.cursor()
            query = """
                SELECT * FROM manufacturers;
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
            print(f"Error while getting manufacturers: {e}")
            return None