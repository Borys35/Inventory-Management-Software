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
        # Pobieramy dane
        invoice_number = data.get('invoice_number')
        net_str = data.get('net_cost')
        gross_str = data.get('gross_cost')

        # Zabezpieczenie: Jeśli formularz nie wysłał danych (np. przez disabled)
        if not net_str or not gross_str:
            flash("Błąd: Brak kwoty Netto lub Brutto! Sprawdź formularz.")
            return redirect(url_for('invoice.list_invoices'))

        # Konwersja na liczby (float) - zamiana przecinka na kropkę
        net = float(net_str.replace(',', '.'))
        gross = float(gross_str.replace(',', '.'))
        
        repo.create(
            invoice_number,
            net,
            gross
        )
        flash("Dodano fakturę!")
    except ValueError:
        flash("Błąd! Koszt musi być liczbą.")
    except Exception as e:
        flash(f"Wystąpił nieoczekiwany błąd: {e}")
    finally:
        conn.close()
        
    return redirect(url_for('invoice.list_invoices'))