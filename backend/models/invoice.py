class Invoice:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def get_all(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM invoices ORDER BY id DESC;")
            rows = cur.fetchall()
            cur.close()
            invoices = []
            for row in rows:
                invoices.append({
                    'id': row[0],
                    'invoice_number': row[1],
                    'net_cost': row[2],
                    'gross_cost': row[3]
                })
            return invoices
        except Exception as e:
            print(f"Error getting invoices: {e}")
            return []

    def create(self, invoice_number, net_cost, gross_cost):
        try:
            cur = self.conn.cursor()
            query = """
                INSERT INTO invoices (invoice_number, net_cost, gross_cost)
                VALUES (%s, %s, %s)
                RETURNING id;
            """
            cur.execute(query, (invoice_number, net_cost, gross_cost))
            new_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating invoice: {e}")
            return None