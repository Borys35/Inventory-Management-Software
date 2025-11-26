from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def get_user_by_email(self, email):
        try:
            cur = self.conn.cursor()
            query = """
                SELECT id, username, email, password_hash, role
                FROM users
                WHERE email = %s;
            """
            cur.execute(query, (email, ))
            row = cur.fetchone()
            cur.close()

            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'password_hash': row[3],
                    'role': row[4]
                }
            return None
        except Exception as e:
            self.conn.rollback()
            print(f"Error while getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        try:
            cur = self.conn.cursor()
            query = """
                SELECT id, username, email, password_hash, role
                FROM users
                WHERE id = %s;
            """
            cur.execute(query, (user_id, ))
            row = cur.fetchone()
            cur.close()

            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'password_hash': row[3],
                    'role': row[4]
                }
            return None
        except Exception as e:
            self.conn.rollback()
            print(f"Error while getting user by user id: {e}")
            return None

    def create_user(self, username, email, password, role='warehouse_staff'):
        try:
            cur = self.conn.cursor()
            query = """
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """
            password_hash = generate_password_hash(password)
            cur.execute(query, (username, email, password_hash, role))
            new_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return new_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error while creating user: {e}")
            return None
    
    def verify_login(self, email, password):
        user = self.get_user_by_email(email)

        if not user:
            return None
        
        if check_password_hash(user['password_hash'], password):
            return user
        
        return None