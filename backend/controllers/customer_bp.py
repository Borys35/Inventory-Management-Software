from flask import Blueprint, request, render_template, flash, redirect, url_for
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.customer import Customer

customer_bp = Blueprint('customer', __name__)

@customer_bp.route("/", methods=['GET'])
@login_required
def list_customers():
    conn = get_db_connection()
    repo = Customer(conn)
    items = repo.get_all()
    conn.close()
    return render_template('customers.html', customers=items)

@customer_bp.route("/create", methods=['POST'])
@login_required
def create_customer():
    data = request.form
    conn = get_db_connection()
    repo = Customer(conn)
    
    repo.create(
        data.get('name'),
        data.get('nip'),
        data.get('contact_email'),
        data.get('address')
    )
    conn.close()
    flash("Dodano klienta!")
    return redirect(url_for('customer.list_customers'))