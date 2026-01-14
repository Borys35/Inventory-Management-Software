from flask import Blueprint, render_template, request, g, redirect, url_for
from lib.db import get_db_connection
from lib.auth_middleware import login_required
from models.inventory import Inventory  # Importujemy nowy model

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/', methods=['GET'])
@login_required
def stock_levels():
    # Pobieramy to co wpisał user
    search_query = request.args.get('search', '')
    restock_query = request.args.get('restock', '')

    conn = get_db_connection()
    repo = Inventory(conn)
    
    # Przekazujemy frazę do bazy
    stock = repo.get_stock_levels(search_query, restock_query)
    
    conn.close()
    
    # Zwracamy listę + search_query (żeby zostało w pasku wyszukiwania)
    return render_template('inventory.html', stock=stock, search_query=search_query, restock=restock_query)