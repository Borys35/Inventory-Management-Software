from flask import Blueprint, render_template
from lib.db import get_db_connection
from lib.auth_middleware import login_required

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route("/", methods=['GET'])
@login_required
def stock_levels():
    conn = get_db_connection()
    cur = conn.cursor()
    # Pobieramy dane z widoku, który sumuje partie towaru (Tabela 10)
    cur.execute("SELECT * FROM v_stock_levels ORDER BY total_quantity DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    inventory = []
    for row in rows:
        inventory.append({
            'product_id': row[0],
            'sku': row[1],
            'product_name': row[2],
            'quantity': row[3],
            'reorder_level': row[4],
            'manufacturer': row[5]
        })

    return render_template('inventory.html', inventory=inventory)