class Document:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def get_all(self):
        try:
            cur = self.conn.cursor()
            # Pobieramy dokumenty wraz z numerem faktury (LEFT JOIN)
            query = """
                SELECT d.id, d.document_number, d.document_date, d.created_at, d.document_type, i.invoice_number
                FROM documents d
                LEFT JOIN invoices i ON d.invoice_id = i.id
                ORDER BY d.created_at DESC;
            """
            cur.execute(query)
            rows = cur.fetchall()
            cur.close()
            documents = []
            for row in rows:
                documents.append({
                    'id': row[0],
                    'document_number': row[1],
                    # row[2] to data dokumentu
                    'document_date': row[2],
                    'created_at': row[3],
                    'document_type': row[4],
                    'invoice_number': row[5]  # Nowe pole z JOINa
                })
            return documents
        except Exception as e:
            print(f"Error getting documents: {e}")
            return []

    def create(self, document_number, document_type, document_date, invoice_id=None):
        try:
            cur = self.conn.cursor()
            query = """
                INSERT INTO documents (document_number, document_type, document_date, invoice_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """
            cur.execute(query, (document_number, document_type, document_date, invoice_id))
            new_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating document: {e}")
            return None
    
    def get_by_id(self, id):
        # Pomocnicza funkcja do pobierania jednego dokumentu (przyda się przy walidacji)
        try:
            cur = self.conn.cursor()
            query = "SELECT * FROM documents WHERE id = %s"
            cur.execute(query, (id,))
            row = cur.fetchone()
            cur.close()
            if row:
                return {'id': row[0], 'invoice_id': row[2]} # index 2 to invoice_id w bazie
            return None
        except Exception:
            return None