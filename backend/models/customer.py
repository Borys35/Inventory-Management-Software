class Customer:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def get_all(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM customers ORDER BY id DESC;")
            rows = cur.fetchall()
            cur.close()
            customers = []
            for row in rows:
                customers.append({
                    'id': row[0],
                    'name': row[1],
                    'nip': row[2],
                    'contact_email': row[3],
                    'address': row[4]
                })
            return customers
        except Exception as e:
            print(f"Error getting customers: {e}")
            return []

    def create(self, name, nip, contact_email, address):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO customers (name, nip, contact_email, address)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (name, nip, contact_email, address))
            new_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating customer: {e}")
            return None