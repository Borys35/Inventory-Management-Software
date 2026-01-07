from flask import Blueprint, request, render_template, flash, redirect, url_for
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.invoice import Invoice

invoice_bp = Blueprint('invoice', __name__)

@invoice_bp.route("/", methods=['GET'])
@login_required
def list_invoices():
    conn = get_db_connection()
    repo = Invoice(conn)
    items = repo.get_all()
    conn.close()
    return render_template('invoices.html', invoices=items)

@invoice_bp.route("/create", methods=['POST'])
@login_required
def create_invoice():
    data = request.form
    conn = get_db_connection()
    repo = Invoice(conn)
    
    try:
        # Konwersja na liczby (float)
        net = float(data.get('net_cost').replace(',', '.'))
        gross = float(data.get('gross_cost').replace(',', '.'))
        
        repo.create(
            data.get('invoice_number'),
            net,
            gross
        )
        flash("Dodano fakturę!")
    except ValueError:
        flash("Błąd! Koszt musi być liczbą.")
    finally:
        conn.close()
        
    return redirect(url_for('invoice.list_invoices'))