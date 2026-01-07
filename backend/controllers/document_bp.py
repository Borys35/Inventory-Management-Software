from flask import Blueprint, request, render_template, flash, redirect, url_for
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.document import Document
from datetime import datetime

document_bp = Blueprint('document', __name__)

@document_bp.route("/", methods=['GET'])
@login_required
def list_documents():
    conn = get_db_connection()
    repo = Document(conn)
    items = repo.get_all()
    conn.close()
    return render_template('documents.html', documents=items)

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
    
    # Jeśli data pusta, wstawiamy dzisiejszą
    if not doc_date:
        doc_date = datetime.now().strftime('%Y-%m-%d')

    repo.create(doc_number, doc_type, doc_date)
    
    conn.close()
    flash("Dodano nowy dokument!")
    return redirect(url_for('document.list_documents'))