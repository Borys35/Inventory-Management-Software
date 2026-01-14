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
    conn = get_db_connection()
    product_model = Product(conn)

    # Upewnij się, że nazwy pól w data.get() pasują do 'name="..."' w HTML
    product_id = product_model.create(
        data.get('sku'),
        data.get('name'),
        data.get('description'),
        # data.get('supplier_id'),
        data.get('manufacturer_id'),
        data.get('reorder_level')
    )

    conn.close()

    if product_id:
        flash("Product created successfully")
    else:
        flash("Error creating product")
    
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