from flask import Flask, render_template
from controllers.user_bp import user_bp
from controllers.supplier_bp import supplier_bp
from controllers.manufacturer_bp import manufacturer_bp
from controllers.product_bp import product_bp
from lib.db import initialize_db_tables

app = Flask(__name__)
app.config.update(
    TESTING=True,
    SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
)

initialize_db_tables()

app.register_blueprint(user_bp)
app.register_blueprint(supplier_bp, url_prefix='/suppliers')
app.register_blueprint(manufacturer_bp, url_prefix='/manufacturers')
app.register_blueprint(product_bp, url_prefix='/products')

@app.route("/")
def hello_world():
    return render_template('index.html')