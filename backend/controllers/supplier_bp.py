from flask import Blueprint, session, redirect, request, render_template, flash, g, jsonify, url_for
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.supplier import Supplier

supplier_bp = Blueprint('supplier', __name__)

@supplier_bp.route("/create", methods=['POST'])
@login_required
def create():
    data = request.form
    conn = get_db_connection()
    supplier_model = Supplier(conn)

    supplier_id = supplier_model.create_supplier(
        data.get('name'),
        data.get('contact_email'),
        data.get('phone'),
        data.get('address')
    )

    conn.close()

    if supplier_id:
        flash(f"Supplier (ID={supplier_id}) created successfully")
        return redirect("/suppliers")
    else:
        flash("Incorrect data")
        return "Supplier create failed", 400
    
@supplier_bp.route("/update/<supplier_id>", methods=['POST'])
@login_required
def update(supplier_id):
    data = request.form
    conn = get_db_connection()
    supplier_model = Supplier(conn)

    supplier_id = supplier_model.update_supplier(
        supplier_id,
        data.get('name'),
        data.get('contact_email'),
        data.get('phone'),
        data.get('address')
    )

    conn.close()

    if supplier_id:
        flash(f"Supplier (ID={supplier_id}) updated successfully")
        return redirect(url_for('supplier.get_one', supplier_id=supplier_id))
    else:
        flash("Incorrect data")
        return "Supplier update failed", 400
    
@supplier_bp.route("/delete/<supplier_id>", methods=['POST'])
@login_required
def delete(supplier_id):
    conn = get_db_connection()
    supplier_model = Supplier(conn)

    supplier_id = supplier_model.delete_supplier(
        supplier_id
    )

    conn.close()

    if supplier_id:
        flash(f"Supplier (ID={supplier_id}) deleted successfully")
        return redirect(url_for('supplier.get_all'))
    else:
        flash("Incorrect data")
        return "Supplier delete failed", 400

@supplier_bp.route("/<supplier_id>", methods=['GET'])
@login_required
def get_one(supplier_id):
    conn = get_db_connection()
    supplier_model = Supplier(conn)

    supplier = supplier_model.get_supplier_by_id(
        supplier_id
    )

    conn.close()
    
    if supplier_id:
        flash(f"Supplier (ID={supplier_id}) get one successfully")
        return render_template('supplier.html', supplier=supplier)
    else:
        flash("Incorrect data")
        return "Supplier get one failed", 400

@supplier_bp.route("/", methods=['GET'])
@login_required
def get_all():
    conn = get_db_connection()
    supplier_model = Supplier(conn)

    suppliers = supplier_model.get_suppliers()

    conn.close()

    return render_template('suppliers.html', suppliers=suppliers)

