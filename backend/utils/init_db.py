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


    # Implementacja TRIGGER, VIEW, PROCEDURE, FUNCTION, TRANSACTION

    # FUNCTION i TRIGGER
    # KROK 1: Funkcja obsługująca logikę (Wersja Full: Przyjęcia + Wydania FIFO)
    cur.execute("""
        CREATE OR REPLACE FUNCTION create_batch_on_completion_func()
        RETURNS TRIGGER AS $$
        DECLARE
            v_row RECORD;          -- Zmienna do iteracji po produktach w zamówieniu
            v_batch RECORD;        -- Zmienna do iteracji po partiach magazynowych
            v_remaining_qty INT;   -- Ile jeszcze musimy 'zdjąć' z magazynu
            v_deduct_qty INT;      -- Ile zdejmujemy z konkretnej partii
        BEGIN
            -- Uruchamiamy tylko gdy status zmienił się na 'completed'
            IF NEW.delivery_status = 'completed' AND (OLD.delivery_status IS DISTINCT FROM 'completed') THEN
                
                -- ====================================================
                -- SCENARIUSZ 1: PRZYJĘCIA (INBOUND) -> Tworzymy nowe partie
                -- ====================================================
                IF (NEW.transaction_type = 'purchase_order') OR 
                   (NEW.transaction_type = 'return' AND NEW.customer_id IS NOT NULL) OR
                   (NEW.transaction_type = 'adjustment' AND NEW.transaction_type != 'sales_order') THEN -- Uproszczenie dla adjustment
                   
                    INSERT INTO product_batches (product_id, delivery_id, quantity, single_price, transaction_date)
                    SELECT 
                        product_id, 
                        delivery_id, 
                        quantity, 
                        single_price,
                        CURRENT_TIMESTAMP
                    FROM product_rows
                    WHERE delivery_id = NEW.id;

                -- ====================================================
                -- SCENARIUSZ 2: ROZCHODY (OUTBOUND) -> Zdejmujemy ze stanu (FIFO)
                -- ====================================================
                ELSIF (NEW.transaction_type = 'sales_order') OR 
                      (NEW.transaction_type = 'transfer') OR 
                      (NEW.transaction_type = 'return' AND NEW.supplier_id IS NOT NULL) THEN
                    
                    -- Pętla po wszystkich produktach w tym zamówieniu
                    FOR v_row IN SELECT * FROM product_rows WHERE delivery_id = NEW.id LOOP
                        v_remaining_qty := v_row.quantity;

                        -- Szukamy dostępnych partii dla produktu (sortujemy od najstarszej - FIFO)
                        -- FOR UPDATE blokuje rekordy, aby nikt inny ich nie wykupił w trakcie tej transakcji
                        FOR v_batch IN 
                            SELECT * FROM product_batches 
                            WHERE product_id = v_row.product_id AND quantity > 0 
                            ORDER BY transaction_date ASC, id ASC
                            FOR UPDATE 
                        LOOP
                            -- Jeśli zaspokoiliśmy potrzebę, przerywamy pętlę partii
                            IF v_remaining_qty <= 0 THEN
                                EXIT;
                            END IF;

                            IF v_batch.quantity >= v_remaining_qty THEN
                                -- Przypadek A: Partia ma wystarczająco dużo towaru
                                UPDATE product_batches 
                                SET quantity = quantity - v_remaining_qty 
                                WHERE id = v_batch.id;
                                
                                v_remaining_qty := 0; -- Wszystko wydano
                            ELSE
                                -- Przypadek B: Partia ma za mało, bierzemy wszystko co jest i szukamy dalej
                                v_deduct_qty := v_batch.quantity;
                                
                                UPDATE product_batches 
                                SET quantity = 0 
                                WHERE id = v_batch.id;
                                
                                v_remaining_qty := v_remaining_qty - v_deduct_qty;
                            END IF;
                        END LOOP;

                        -- WALIDACJA: Jeśli po sprawdzeniu wszystkich partii nadal brakuje towaru
                        IF v_remaining_qty > 0 THEN
                            RAISE EXCEPTION 'Błąd magazynowy: Brak wystarczającej ilości towaru dla produktu ID: % (Brakuje: %)', v_row.product_id, v_remaining_qty;
                        END IF;

                    END LOOP;
                END IF;
                
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # KROK 2: Przypisanie Triggera do tabeli deliveries
    # Trigger uruchamia się PO (AFTER) aktualizacji (UPDATE) rekordu.
    cur.execute("""
        DROP TRIGGER IF EXISTS trg_create_batch_on_completion ON deliveries;
        
        CREATE TRIGGER trg_create_batch_on_completion
        AFTER UPDATE ON deliveries
        FOR EACH ROW
        EXECUTE FUNCTION create_batch_on_completion_func();
    """)

    # VIEW
    cur.execute("DROP VIEW IF EXISTS v_stock_levels CASCADE;")
    cur.execute("""
        CREATE OR REPLACE VIEW v_stock_levels AS
        SELECT 
            p.id AS product_id,
            p.sku AS sku,
            p.name AS product_name,
            COALESCE(SUM(pb.quantity), 0) AS total_quantity, -- COALESCE zamienia NULL na 0
            COALESCE(SUM(pb.quantity * pb.single_price), 0) AS total_value,
            p.reorder_level AS reorder_level,
            m.name AS manufacturer_name
        FROM products p
        LEFT JOIN product_batches pb ON p.id = pb.product_id
        LEFT JOIN manufacturers m ON p.manufacturer_id = m.id
        GROUP BY p.id, p.sku, p.name, p.reorder_level, m.name;
    """)
    
    cur.execute("DROP VIEW IF EXISTS v_delivery_details CASCADE;")
    cur.execute("""
        CREATE OR REPLACE VIEW v_delivery_details AS
        SELECT
            d.id AS delivery_id,
                
            pr.id AS row_id,
            pr.quantity,
            pr.single_price,
            pr.total_price,
            
            -- Product Details (Joined from products table)
            p.name AS product_name,
            p.sku AS product_sku,
            p.description AS product_description

        FROM 
            product_rows pr
        JOIN 
            deliveries d ON pr.delivery_id = d.id
        JOIN 
            products p ON pr.product_id = p.id;
    """)

    cur.execute("""
        CREATE OR REPLACE VIEW v_products_to_reorder AS
        SELECT *
        FROM v_stock_levels
        WHERE total_quantity <= reorder_level;
    """)

    cur.execute("""
        CREATE OR REPLACE VIEW v_inventory_value AS
        SELECT 
            p.name AS product_name,
            SUM(pb.quantity) AS quantity,
            -- Średnia ważona cena (opcjonalnie)
            ROUND(SUM(pb.quantity * pb.single_price) / NULLIF(SUM(pb.quantity), 0), 2) AS avg_price,
            -- Łączna wartość towaru
            SUM(pb.quantity * pb.single_price) AS total_value
        FROM product_batches pb
        JOIN products p ON pb.product_id = p.id
        GROUP BY p.id, p.name;
    """)

    # PROCEDURE
    cur.execute("""
        CREATE OR REPLACE PROCEDURE cancel_completed_delivery(p_delivery_id INT)
        LANGUAGE plpgsql
        AS $$
        BEGIN
            -- 1. Sprawdź czy dostawa istnieje i jest zakończona
            IF NOT EXISTS (SELECT 1 FROM deliveries WHERE id = p_delivery_id AND delivery_status = 'completed') THEN
                RAISE EXCEPTION 'Dostawa nie istnieje lub nie jest zakończona.';
            END IF;

            -- 2. Cofnij skutki magazynowe (Usuń partie towaru powstałe z tej dostawy)
            -- UWAGA: To zadziała tylko dla przyjęć (purchase_order). 
            -- Cofanie wydań (sales) jest trudniejsze, bo towar już mógł wyjść.
            DELETE FROM product_batches 
            WHERE delivery_id = p_delivery_id;

            -- 3. Zmień status dostawy na 'cancelled' (zamiast usuwać rekord)
            UPDATE deliveries 
            SET delivery_status = 'cancelled' 
            WHERE id = p_delivery_id;

            COMMIT;
            RAISE NOTICE 'Dostawa % została anulowana, a stany magazynowe cofnięte.', p_delivery_id;
        END;
        $$;
    """)


#     -- 1. Start Transakcji
# BEGIN TRANSACTION;

# -- Używamy konstrukcji WITH, aby przechować ID nowej dostawy
# WITH new_delivery_insert AS (
#     -- 2. Tworzymy nagłówek i zwracamy wygenerowane ID (RETURNING id)
#     INSERT INTO deliveries (user_id, delivery_status)
#     VALUES (1, 'pending') -- Tu wpisz ID użytkownika (zamiast %s)
#     RETURNING id
# )
# -- 3. Wstawiamy wiersze (odpowiednik pętli w Pythonie)
# INSERT INTO product_rows (delivery_id, product_id, quantity)
# SELECT id, product_id, quantity
# FROM new_delivery_insert, 
#      (VALUES 
#         -- Tutaj wypisujesz listę produktów (odpowiednik listy 'items')
#         (10, 50),  -- (product_id=10, quantity=50)
#         (12, 100), -- (product_id=12, quantity=100)
#         (15, 5)    -- (product_id=15, quantity=5)
#      ) AS items(product_id, quantity);

# -- 4. Zatwierdź (jeśli nie było błędów)
# COMMIT;

# -- 5. Jeśli wystąpi błąd w trakcie, SQL automatycznie zrobi ROLLBACK
# -- (W skrypcie SQL nie piszemy jawnie ROLLBACK w bloku IF, silnik bazy danych zrobi to sam przy błędzie)
        
    print("Tables created successfully.")

