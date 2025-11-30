from flask import Blueprint, session, redirect, request, render_template, flash, g, jsonify, url_for
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.product import Product
from models.manufacturer import Manufacturer
from models.supplier import Supplier

product_bp = Blueprint('product', __name__)

@product_bp.route("/", methods=['GET'])
@login_required
def get_all():
    conn = get_db_connection()
    product_model = Product(conn)
    manufacturer_model = Manufacturer(conn)
    supplier_model = Supplier(conn)

    products = product_model.get_products()
    manufacturers = manufacturer_model.get_manufacturers()
    suppliers = supplier_model.get_suppliers()

    conn.close()

    return render_template('products.html', products=products, manufacturers=manufacturers, suppliers=suppliers)

@product_bp.route("/<product_id>", methods=['GET'])
@login_required
def get_one(product_id):
    conn = get_db_connection()
    product_model = Product(conn)
    manufacturer_model = Manufacturer(conn)
    supplier_model = Supplier(conn)

    product = product_model.get_product_by_id(product_id)
    manufacturers = manufacturer_model.get_manufacturers()
    suppliers = supplier_model.get_suppliers()

    conn.close()

    return render_template('product.html', product=product, manufacturers=manufacturers, suppliers=suppliers)

@product_bp.route("/create", methods=['POST'])
@login_required
def create():
    data = request.form
    conn = get_db_connection()
    product_model = Product(conn)

    product_id = product_model.create_product(
        data.get('sku'),
        data.get('name'),
        data.get('description'),
        data.get('supplier_id'),
        data.get('manufacturer_id'),
        data.get('reorder_level')
    )

    conn.close()

    if product_id:
        flash(f"Product (ID={product_id}) created successfully")
        return redirect("/products")
    else:
        flash("Incorrect data")
        return "Product create failed", 400

@product_bp.route("/update", methods=['POST'])
@login_required
def update():
    pass