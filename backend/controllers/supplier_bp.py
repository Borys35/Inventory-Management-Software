from flask import Blueprint, session, redirect, request, render_template, flash, g
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
        flash("Created successfully")
        return redirect("/suppliers")
    else:
        flash("Incorrect data")
        return redirect("/suppliers"), 400
    
@supplier_bp.route("/<supplier_id>", methods=['PUT'])
@login_required
def update():
    data = request.form
    conn = get_db_connection()
    supplier_model = Supplier(conn)

    supplier_id = supplier_model.update_supplier(
        data.get('name'),
        data.get('contact_email'),
        data.get('phone'),
        data.get('address')
    )

    conn.close()

    if supplier_id:
        flash("Updated successfully")
        return redirect("/suppliers")
    else:
        flash("Incorrect data")
        return redirect("/suppliers"), 400

@supplier_bp.route("/", methods=['GET'])
@login_required
def get_all():
    conn = get_db_connection()
    supplier_model = Supplier(conn)

    suppliers = supplier_model.get_suppliers()

    conn.close()

    return render_template('suppliers.html', suppliers=suppliers)

