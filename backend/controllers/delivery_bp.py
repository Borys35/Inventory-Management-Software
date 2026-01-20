from flask import Blueprint, request, render_template, flash, redirect, url_for, g
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.delivery import Delivery
from models.product import Product
from models.document import Document
from models.supplier import Supplier
from models.customer import Customer
from models.invoice import Invoice

delivery_bp = Blueprint('delivery', __name__)

@delivery_bp.route("/", methods=['GET'])
@login_required
def list_deliveries():
    conn = get_db_connection()
    repo = Delivery(conn)
    deliveries = repo.get_all()
    conn.close()
    return render_template('deliveries_list.html', deliveries=deliveries)

@delivery_bp.route("/<delivery_id>", methods=['GET'])
@login_required
def get_one(delivery_id):
    conn = get_db_connection()
    repo = Delivery(conn)
    [delivery, products] = repo.get_one(delivery_id)
    conn.close()
    return render_template('delivery_single.html', delivery=delivery, products=products)

@delivery_bp.route("/<delivery_id>", methods=['POST'])
@login_required
def update(delivery_id):
    data = request.form
    conn = get_db_connection()
    delivery_model = Delivery(conn)

    delivery_id = delivery_model.update(
        delivery_id,
        data.get('delivery_status')
    )

    conn.close()

    if delivery_id:
        flash(f"Delivery (ID={delivery_id}) updated successfully")
        return redirect(url_for('delivery.get_one', delivery_id=delivery_id))
    else:
        flash("Incorrect data")
        return "Delivery update failed", 400

@delivery_bp.route("/create", methods=['GET', 'POST'])
@login_required
def create_delivery():
    conn = get_db_connection()
    
    if request.method == 'POST':
        doc_id = request.form.get('document_id')
        
        data = {
            'user_id': g.user['id'],
            'document_id': doc_id,
            'supplier_id': request.form.get('supplier_id') or None,
            'customer_id': request.form.get('customer_id') or None,
            'transaction_type': request.form.get('transaction_type')
        }
        
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')
        
        products_list = []
        current_delivery_total = 0.0
        
        for i in range(len(product_ids)):
            if product_ids[i]:
                qty = int(quantities[i])
                price = float(prices[i])
                line_total = qty * price
                current_delivery_total += line_total
                
                products_list.append({
                    'product_id': product_ids[i],
                    'qty': qty,
                    'price': price
                })

        # --- WALIDACJA FINANSOWA (PEŁNA HISTORIA) ---
        if data['transaction_type'] == 'purchase_order' and doc_id:
            doc_model = Document(conn)
            document = doc_model.get_by_id(doc_id) 
            
            if document and document.get('invoice_id'):
                inv_model = Invoice(conn)
                invoice = inv_model.get_by_id(document['invoice_id'])
                
                if invoice:
                    limit = float(invoice['gross_cost'])
                    
                    # 1. Pobieramy sumę WCZEŚNIEJSZYCH dostaw dla tego dokumentu
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT COALESCE(SUM(pr.total_price), 0)
                        FROM product_rows pr
                        JOIN deliveries d ON pr.delivery_id = d.id
                        WHERE d.document_id = %s AND d.delivery_status != 'cancelled'
                    """, (doc_id,))
                    previous_total = float(cur.fetchone()[0])
                    cur.close()

                    # 2. Sumujemy starą historię + nową dostawę
                    total_usage = previous_total + current_delivery_total
                    remaining_limit = limit - previous_total

                    if total_usage > limit + 0.01:
                        conn.close()
                        flash(f"BŁĄD: Przekroczono limit faktury! Faktura: {limit:.2f} PLN. Wykorzystano wcześniej: {previous_total:.2f} PLN. Próbujesz dodać: {current_delivery_total:.2f} PLN. Dostępne tylko: {remaining_limit:.2f} PLN.")
                        return redirect(url_for('delivery.create_delivery'))
                    else:
                        print(f"✅ Walidacja OK. Limit: {limit}, Było: {previous_total}, Teraz: {current_delivery_total}")

        # --- ZAPIS ---
        repo = Delivery(conn)
        new_id = repo.create_delivery_with_products(data, products_list)
        conn.close()

        if new_id:
            flash("Dostawa została pomyślnie utworzona!")
            return redirect(url_for('delivery.list_deliveries'))
        else:
            flash("Błąd podczas tworzenia dostawy.")
            return redirect(url_for('delivery.create_delivery'))

    # --- GET (Bez zmian) ---
    try:
        prod_model = Product(conn)
        if hasattr(prod_model, 'get_all'):
            products = prod_model.get_all()
        elif hasattr(prod_model, 'get_all_products'):
            products = prod_model.get_all_products()
        else:
            products = []
    except Exception:
        products = []

    try:
        documents = Document(conn).get_all()
    except:
        documents = []

    try:
        suppliers = Supplier(conn).get_all() 
    except:
        try:
            suppliers = Supplier(conn).get_all_suppliers()
        except:
            suppliers = []

    try:
        customers = Customer(conn).get_all()
    except:
        customers = []

    conn.close()
    
    return render_template(
        'delivery_create.html', 
        products=products, 
        documents=documents, 
        suppliers=suppliers, 
        customers=customers
    )