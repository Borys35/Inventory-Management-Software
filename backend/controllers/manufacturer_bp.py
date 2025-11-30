from flask import Blueprint, session, redirect, request, render_template, flash, g, jsonify, url_for
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.manufacturer import Manufacturer

manufacturer_bp = Blueprint('manufacturer', __name__)

@manufacturer_bp.route("/create", methods=['POST'])
@login_required
def create():
    data = request.form
    conn = get_db_connection()
    manufacturer_model = Manufacturer(conn)

    manufacturer_id = manufacturer_model.create_manufacturer(
        data.get('name'),
        data.get('contact_email'),
        data.get('phone'),
        data.get('address')
    )

    conn.close()

    if manufacturer_id:
        flash(f"Manufacturer (ID={manufacturer_id}) created successfully")
        return redirect("/manufacturers")
    else:
        flash("Incorrect data")
        return "Manufacturer create failed", 400
    
@manufacturer_bp.route("/update/<manufacturer_id>", methods=['POST'])
@login_required
def update(manufacturer_id):
    data = request.form
    conn = get_db_connection()
    manufacturer_model = Manufacturer(conn)

    manufacturer_id = manufacturer_model.update_manufacturer(
        manufacturer_id,
        data.get('name'),
        data.get('contact_email'),
        data.get('phone'),
        data.get('address')
    )

    conn.close()

    if manufacturer_id:
        flash(f"Manufacturer (ID={manufacturer_id}) updated successfully")
        return redirect(url_for('manufacturer.get_one', manufacturer_id=manufacturer_id))
    else:
        flash("Incorrect data")
        return "Manufacturer update failed", 400
    
@manufacturer_bp.route("/delete/<manufacturer_id>", methods=['POST'])
@login_required
def delete(manufacturer_id):
    conn = get_db_connection()
    manufacturer_model = Manufacturer(conn)

    manufacturer_id = manufacturer_model.delete_manufacturer(
        manufacturer_id
    )

    conn.close()

    if manufacturer_id:
        flash(f"Manufacturer (ID={manufacturer_id}) deleted successfully")
        return redirect(url_for('manufacturer.get_all'))
    else:
        flash("Incorrect data")
        return "Manufacturer delete failed", 400

@manufacturer_bp.route("/<manufacturer_id>", methods=['GET'])
@login_required
def get_one(manufacturer_id):
    conn = get_db_connection()
    manufacturer_model = Manufacturer(conn)

    manufacturer = manufacturer_model.get_manufacturer_by_id(
        manufacturer_id
    )

    conn.close()
    
    if manufacturer_id:
        flash(f"Manufacturer (ID={manufacturer_id}) get one successfully")
        return render_template('manufacturer.html', manufacturer=manufacturer)
    else:
        flash("Incorrect data")
        return "Manufacturer get one failed", 400

@manufacturer_bp.route("/", methods=['GET'])
@login_required
def get_all():
    conn = get_db_connection()
    manufacturer_model = Manufacturer(conn)

    manufacturers = manufacturer_model.get_manufacturers()

    conn.close()

    return render_template('manufacturers.html', manufacturers=manufacturers)

