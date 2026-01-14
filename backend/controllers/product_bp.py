from flask import Blueprint, render_template, request, redirect, url_for, flash
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.product import Product
from models.manufacturer import Manufacturer
# from models.supplier import Supplier  # Odkomentuj jeśli będziesz używać dostawców

product_bp = Blueprint('product', __name__, url_prefix='/products')

@product_bp.route('/', methods=['GET'])
@login_required
def get_all():
    # 1. Pobieramy frazę z paska wyszukiwania (jeśli istnieje)
    search_query = request.args.get('search', '')
    
    conn = get_db_connection()
    product_model = Product(conn)
    manufacturer_model = Manufacturer(conn)
    # supplier_model = Supplier(conn)
    
    # 2. Pobieramy produkty (z filtrowaniem lub bez)
    products = product_model.get_all(search_query)
    
    # 3. Pobieramy producentów (potrzebne do listy rozwijanej w formularzu dodawania)
    manufacturers = manufacturer_model.get_manufacturers()
    # suppliers = supplier_model.get_suppliers()
    
    conn.close()
    
    # 4. Przekazujemy wszystko do szablonu HTML
    return render_template('products.html', 
                           products=products, 
                           manufacturers=manufacturers,
                           # suppliers=suppliers,
                           search_query=search_query)

@product_bp.route('/create', methods=['POST'])
@login_required
def create():
    data = request.form
    
    # --- WALIDACJA ---
    name = data.get('name')
    sku = data.get('sku')
    reorder_level = data.get('reorder_level')

    # 1. Pola obowiązkowe
    if not name or not sku:
        flash("Validation Error: Name and SKU are required fields!")
        return redirect(url_for('product.get_all'))
    
    # 2. Długość nazwy
    if len(name) < 3:
        flash("Validation Error: Product name is too short (min. 3 characters)!")
        return redirect(url_for('product.get_all'))

    # 3. Liczba dodatnia
    try:
        r_level = int(reorder_level)
        if r_level < 0:
            flash("Validation Error: Reorder level cannot be negative!")
            return redirect(url_for('product.get_all'))
    except (ValueError, TypeError):
        flash("Validation Error: Reorder level must be a valid number!")
        return redirect(url_for('product.get_all'))
    # --- KONIEC WALIDACJI ---

    conn = get_db_connection()
    product_model = Product(conn)

    product_id = product_model.create(
        sku,
        name,
        data.get('description'),
        data.get('manufacturer_id'),
        r_level
    )

    conn.close()

    if product_id:
        flash("Product created successfully")
    else:
        flash("Error creating product (Database Error)")
    
    return redirect(url_for('product.get_all'))

@product_bp.route('/<product_id>', methods=['GET'])
@login_required
def get_one(product_id):
    conn = get_db_connection()
    product_model = Product(conn)
    manufacturer_model = Manufacturer(conn)
    
    product = product_model.get_product_by_id(product_id)
    manufacturers = manufacturer_model.get_manufacturers()
    
    conn.close()
    
    if product:
        return render_template('product.html', product=product, manufacturers=manufacturers)
    else:
        flash("Product not found")
        return redirect(url_for('product.get_all'))

@product_bp.route('/<product_id>/update', methods=['POST'])
@login_required
def update(product_id):
    data = request.form
    conn = get_db_connection()
    product_model = Product(conn)

    updated_id = product_model.update_product(
        product_id,
        data.get('sku'),
        data.get('name'),
        data.get('description'),
        # data.get('supplier_id'),
        data.get('manufacturer_id'),
        data.get('reorder_level')
    )

    conn.close()

    if updated_id:
        flash(f"Product {updated_id} updated successfully")
        return redirect(url_for('product.get_one', product_id=updated_id))
    else:
        flash("Error updating product")
        return redirect(url_for('product.get_all'))

@product_bp.route('/<product_id>/delete', methods=['POST'])
@login_required
def delete(product_id):
    conn = get_db_connection()
    product_model = Product(conn)
    
    deleted_id = product_model.delete_product(product_id)
    
    conn.close()
    
    if deleted_id:
        flash(f"Product {deleted_id} deleted")
    else:
        flash("Error deleting product")
        
    return redirect(url_for('product.get_all'))