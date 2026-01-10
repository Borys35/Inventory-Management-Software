from flask import Blueprint, request, render_template, flash, redirect, url_for, g
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.delivery import Delivery
from models.product import Product
from models.document import Document
from models.supplier import Supplier
from models.customer import Customer

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
        # --- LOGIKA ZAPISU (BEZ ZMIAN) ---
        data = {
            'user_id': g.user['id'],
            'document_id': request.form.get('document_id'),
            'supplier_id': request.form.get('supplier_id') or None,
            'customer_id': request.form.get('customer_id') or None,
            'transaction_type': request.form.get('transaction_type')
        }
        
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')
        
        products_list = []
        for i in range(len(product_ids)):
            if product_ids[i]:
                products_list.append({
                    'product_id': product_ids[i],
                    'qty': quantities[i],
                    'price': prices[i]
                })

        repo = Delivery(conn)
        new_id = repo.create_delivery_with_products(data, products_list)
        conn.close()

        if new_id:
            flash("Dostawa została pomyślnie utworzona!")
            return redirect(url_for('delivery.list_deliveries'))
        else:
            flash("Błąd podczas tworzenia dostawy.")
            return redirect(url_for('delivery.create_delivery'))

    # --- CZĘŚĆ GET (POPRAWIONA) ---
    print("--- DIAGNOSTYKA FORMULARZA ---")
    
    # 1. Pobieranie Produktów
    try:
        # Sprawdzamy czy metoda nazywa się get_all czy get_all_products
        prod_model = Product(conn)
        if hasattr(prod_model, 'get_all'):
            products = prod_model.get_all()
        elif hasattr(prod_model, 'get_all_products'):
            products = prod_model.get_all_products()
        else:
            print("❌ BŁĄD: Model Product nie ma metody get_all ani get_all_products!")
            products = []
        print(f"✅ Produkty: znalezio {len(products)}")
    except Exception as e:
        print(f"❌ Błąd pobierania produktów: {e}")
        products = []

    # 2. Pobieranie Dokumentów
    try:
        documents = Document(conn).get_all()
        print(f"✅ Dokumenty: znaleziono {len(documents)}")
    except Exception as e:
        print(f"❌ Błąd pobierania dokumentów: {e}")
        documents = []

    # 3. Pobieranie Dostawców
    try:
        # Tu był błąd wcześniej - wywołujemy get_all() a nie get_all_suppliers()
        suppliers = Supplier(conn).get_all() 
        print(f"✅ Dostawcy: znaleziono {len(suppliers)}")
    except Exception as e:
        print(f"❌ Błąd pobierania dostawców: {e}")
        try:
            suppliers = Supplier(conn).get_all_suppliers() # Próba zapasowa
        except:
            suppliers = []

    # 4. Pobieranie Klientów
    try:
        customers = Customer(conn).get_all()
        print(f"✅ Klienci: znaleziono {len(customers)}")
    except Exception as e:
        print(f"❌ Błąd pobierania klientów: {e}")
        customers = []

    conn.close()
    
    return render_template(
        'delivery_create.html', 
        products=products, 
        documents=documents, 
        suppliers=suppliers, 
        customers=customers
    )