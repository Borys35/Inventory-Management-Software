from flask import Blueprint, request, render_template, flash, redirect, url_for
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.document import Document
from models.invoice import Invoice  # <--- Importujemy model faktury
from datetime import datetime

document_bp = Blueprint('document', __name__)

@document_bp.route("/", methods=['GET'])
@login_required
def list_documents():
    conn = get_db_connection()
    doc_repo = Document(conn)
    inv_repo = Invoice(conn)
    
    # Pobieramy dokumenty I faktury (do listy rozwijanej)
    documents = doc_repo.get_all()
    invoices = inv_repo.get_all()
    
    conn.close()
    return render_template('documents.html', documents=documents, invoices=invoices)

@document_bp.route("/create", methods=['POST'])
@login_required
def create_document():
    data = request.form
    conn = get_db_connection()
    repo = Document(conn)
    
    # Pobieramy dane z formularza
    doc_number = data.get('document_number')
    doc_type = data.get('document_type')
    doc_date = data.get('document_date')
    
    # Pobieramy ID faktury (pusty string zamieniamy na None)
    invoice_id = data.get('invoice_id')
    if not invoice_id:
        invoice_id = None
    
    # Jeśli data pusta, wstawiamy dzisiejszą
    if not doc_date:
        doc_date = datetime.now().strftime('%Y-%m-%d')

    repo.create(doc_number, doc_type, doc_date, invoice_id)
    
    conn.close()
    flash("Dodano nowy dokument!")
    return redirect(url_for('document.list_documents'))