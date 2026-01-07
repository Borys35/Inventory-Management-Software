class Document:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def get_all(self):
        try:
            cur = self.conn.cursor()
            # Pobieramy dokumenty od najnowszego
            cur.execute("SELECT * FROM documents ORDER BY created_at DESC;")
            rows = cur.fetchall()
            cur.close()
            documents = []
            for row in rows:
                documents.append({
                    'id': row[0],
                    'document_number': row[1],
                    # row[2] to invoice_id, na razie pomijamy
                    'document_date': row[3],
                    'created_at': row[4],
                    'document_type': row[5]
                })
            return documents
        except Exception as e:
            print(f"Error getting documents: {e}")
            return []

    def create(self, document_number, document_type, document_date):
        try:
            cur = self.conn.cursor()
            query = """
                INSERT INTO documents (document_number, document_type, document_date)
                VALUES (%s, %s, %s)
                RETURNING id;
            """
            cur.execute(query, (document_number, document_type, document_date))
            new_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating document: {e}")
            return None