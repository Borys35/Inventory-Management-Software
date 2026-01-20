from flask import Flask, render_template
from controllers.user_bp import user_bp
from controllers.supplier_bp import supplier_bp
from controllers.manufacturer_bp import manufacturer_bp
from controllers.product_bp import product_bp
from lib.db import initialize_db_tables, get_db_connection # <--- Dodano get_db_connection
from controllers.customer_bp import customer_bp
from controllers.document_bp import document_bp
from controllers.invoice_bp import invoice_bp
from controllers.delivery_bp import delivery_bp
from controllers.inventory_bp import inventory_bp

app = Flask(__name__)
app.config.update(
    TESTING=True,
    SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
)

initialize_db_tables()

app.register_blueprint(user_bp)
app.register_blueprint(supplier_bp, url_prefix='/suppliers')
app.register_blueprint(manufacturer_bp, url_prefix='/manufacturers')
app.register_blueprint(product_bp, url_prefix='/products')
app.register_blueprint(customer_bp, url_prefix='/customers')
app.register_blueprint(document_bp, url_prefix='/documents')
app.register_blueprint(invoice_bp, url_prefix='/invoices')
app.register_blueprint(delivery_bp, url_prefix='/deliveries')
app.register_blueprint(inventory_bp, url_prefix='/inventory')

@app.route("/")
def hello_world():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Pobierz łączną wartość magazynu (korzystamy z widoku v_inventory_value)
    cur.execute("SELECT SUM(total_value) FROM v_inventory_value;")
    # Jeśli wynik to None (pusta baza), wstawiamy 0.0
    total_value = cur.fetchone()[0] or 0.0

    # 2. Pobierz liczbę produktów z niskim stanem
    cur.execute("SELECT COUNT(*) FROM v_products_to_reorder;")
    low_stock_count = cur.fetchone()[0] or 0

    # 3. Pobierz ogólną liczbę produktów
    cur.execute("SELECT COUNT(*) FROM products;")
    total_products = cur.fetchone()[0] or 0

    # 4. Pobierz 5 ostatnich transakcji (dla podglądu)
    cur.execute("""
        SELECT d.id, d.transaction_type, d.delivery_status, d.created_at 
        FROM deliveries d 
        ORDER BY d.created_at DESC 
        LIMIT 5;
    """)
    recent_activities = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('index.html', 
                           total_value=round(total_value, 2),
                           low_stock_count=low_stock_count,
                           total_products=total_products,
                           recent_activities=recent_activities)