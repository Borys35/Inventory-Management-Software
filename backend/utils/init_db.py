def init_tables(cur):
    print("Initializing database schema...")

    # Enums
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
            CREATE TYPE ledger_status AS ENUM (
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

    # Independent tables
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS manufacturers (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            contact_email VARCHAR,
            phone VARCHAR,
            address TEXT
        );
    """)

    # Dependent tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            sku VARCHAR UNIQUE NOT NULL,
            name VARCHAR NOT NULL,
            quantity INTEGER DEFAULT 0,
            description TEXT,
            specifications JSONB,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
            manufacturer_id INTEGER REFERENCES manufacturers(id) ON DELETE SET NULL,
            reorder_level INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory_batches (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
            cost_price DECIMAL(10, 2) NOT NULL,
            original_quantity INTEGER NOT NULL,
            remaining_quantity INTEGER NOT NULL,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory_ledger (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            batch_id INTEGER REFERENCES inventory_batches(id) ON DELETE SET NULL,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            quantity_change INTEGER NOT NULL,
            transaction_type transaction_type NOT NULL,
            status ledger_status DEFAULT 'pending',
            unit_cost DECIMAL(10, 2) NOT NULL,
            unit_price DECIMAL(10, 2) DEFAULT 0,
            transaction_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    print("Tables created successfully.")