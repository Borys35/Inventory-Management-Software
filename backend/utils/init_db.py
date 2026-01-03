import psycopg2

def init_tables(cur):
    print("Initializing database schema...")

    # ---------------------------------------------------------
    # 1. Tworzenie Typów Enum (Słowniki)
    # ---------------------------------------------------------
    enum_queries = [
        """
        DO $$ BEGIN
            CREATE TYPE transaction_type AS ENUM (
                'purchase_order', 'sales_order', 'transfer', 'adjustment', 'return'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE document_type AS ENUM (
                'PZ', 'WZ', 'PW', 'RW'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE delivery_status AS ENUM (
                'pending', 'in_progress', 'completed', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM (
                'admin', 'manager', 'warehouse_staff'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    ]

    for query in enum_queries:
        cur.execute(query)

    # ---------------------------------------------------------
    # 2. Tabele Niezależne (Słowniki i Podmioty)
    # ---------------------------------------------------------
    
    # Users (Zmiana nazwy na liczbę mnogą dla uniknięcia konfliktu ze słowem 'user')
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR UNIQUE NOT NULL,
            email VARCHAR UNIQUE NOT NULL,
            password_hash VARCHAR NOT NULL,
            role user_role DEFAULT 'warehouse_staff',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            contact_email VARCHAR,
            phone VARCHAR,
            address TEXT
        );
    """)

    # NOWA TABELA: Customers
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            nip VARCHAR,
            contact_email VARCHAR,
            address TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS manufacturers (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            contact_email VARCHAR,
            phone VARCHAR,
            address TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            invoice_number VARCHAR,
            net_cost DECIMAL(10, 2),
            gross_cost DECIMAL(10, 2)
        );
    """)

    # ---------------------------------------------------------
    # 3. Tabele Zależne (Produkty i Dokumenty)
    # ---------------------------------------------------------

    # Products (Zależy od manufacturers)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            sku VARCHAR UNIQUE NOT NULL,
            name VARCHAR NOT NULL,
            description TEXT,
            specifications JSONB,
            manufacturer_id INTEGER REFERENCES manufacturers(id) ON DELETE SET NULL,
            reorder_level INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Documents (Zależy od invoices)
    # document_id to np. string 'PZ/01/2025'
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            document_number VARCHAR, 
            invoice_id INTEGER REFERENCES invoices(id) ON DELETE SET NULL,
            document_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            document_type document_type
        );
    """)

    # ---------------------------------------------------------
    # 4. Tabele Transakcyjne (Dostawy i Ruchy Magazynowe)
    # ---------------------------------------------------------

    # Deliveries (Główna tabela operacyjna)
    # Łączy Users, Documents, Suppliers, Customers
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deliveries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
            customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
            delivery_status delivery_status DEFAULT 'pending',
            transaction_type transaction_type,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Product Rows (Historia transakcji - Ledger)
    # Immutable (raczej nie edytujemy po fakcie)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_rows (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            delivery_id INTEGER REFERENCES deliveries(id) ON DELETE CASCADE,
            single_price DECIMAL(10, 2),
            quantity INTEGER,
            total_price DECIMAL(10, 2),
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Product Batches (Aktualny stan magazynowy per partia - dla FIFO)
    # Mutable (zmniejszamy quantity przy wydawaniu)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_batches (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            delivery_id INTEGER REFERENCES deliveries(id) ON DELETE CASCADE,
            quantity INTEGER DEFAULT 1,
            single_price DECIMAL(10, 2),
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)


    # Implement TRIGGER, VIEW, PROCEDURE, FUNCTION, TRANSACTION
    
    print("Tables created successfully.")