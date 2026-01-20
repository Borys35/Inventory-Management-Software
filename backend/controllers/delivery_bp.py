from flask import Blueprint, request, render_template, flash, redirect, url_for, g
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.delivery import Delivery
from models.product import Product
from models.document import Document
from models.supplier import Supplier
from models.customer import Customer
from models.invoice import Invoice  # <--- WAŻNY IMPORT

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
        # --- 1. POBIERANIE DANYCH ---
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
        
        # --- 2. PRZYGOTOWANIE PRODUKTÓW I SUMOWANIE WARTOŚCI ---
        products_list = []
        current_delivery_total = 0.0
        
        for i in range(len(product_ids)):
            if product_ids[i]:
                qty = int(quantities[i])
                price = float(prices[i])
                
                # Liczymy wartość tej pozycji i dodajemy do sumy całkowitej
                line_total = qty * price
                current_delivery_total += line_total
                
                products_list.append({
                    'product_id': product_ids[i],
                    'qty': qty,
                    'price': price
                })

        # --- 3. [START] WALIDACJA FINANSOWA (Business Logic) ---
        # Sprawdzamy tylko dla zakupów (purchase_order), bo wtedy faktura jest limitem kosztów
        if data['transaction_type'] == 'purchase_order' and doc_id:
            # A. Pobierz dokument
            doc_model = Document(conn)
            # Używamy metody get_by_id, którą dodaliśmy do modelu Document
            document = doc_model.get_by_id(doc_id) 
            
            # B. Sprawdź czy dokument ma przypisaną fakturę (invoice_id)
            if document and document.get('invoice_id'):
                inv_model = Invoice(conn)
                invoice = inv_model.get_by_id(document['invoice_id'])
                
                if invoice:
                    limit = float(invoice['gross_cost'])
                    
                    # C. Porównanie (z małym marginesem błędu 0.01 grosza)
                    if current_delivery_total > limit + 0.01:
                        conn.close()
                        flash(f"BŁĄD KRYTYCZNY: Wartość dostawy ({current_delivery_total:.2f} PLN) przekracza kwotę faktury {invoice['invoice_number']} ({limit:.2f} PLN)!")
                        return redirect(url_for('delivery.create_delivery'))
                    else:
                        print(f"✅ Walidacja finansowa OK. Dostawa: {current_delivery_total}, Faktura: {limit}")
        # --- [KONIEC] WALIDACJA FINANSOWA ---

        # --- 4. ZAPIS DO BAZY ---
        repo = Delivery(conn)
        new_id = repo.create_delivery_with_products(data, products_list)
        conn.close()

        if new_id:
            flash("Dostawa została pomyślnie utworzona!")
            return redirect(url_for('delivery.list_deliveries'))
        else:
            flash("Błąd podczas tworzenia dostawy.")
            return redirect(url_for('delivery.create_delivery'))

    # --- CZĘŚĆ GET (BEZ ZMIAN - DIAGNOSTYKA) ---
    print("--- DIAGNOSTYKA FORMULARZA ---")
    
    # 1. Pobieranie Produktów
    try:
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
        suppliers = Supplier(conn).get_all() 
        print(f"✅ Dostawcy: znaleziono {len(suppliers)}")
    except Exception as e:
        print(f"❌ Błąd pobierania dostawców: {e}")
        try:
            suppliers = Supplier(conn).get_all_suppliers()
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