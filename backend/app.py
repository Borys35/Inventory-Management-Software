from flask import Flask, render_template
from controllers.user_bp import user_blueprint
from lib.db import initialize_db_tables

app = Flask(__name__)

initialize_db_tables()

app.register_blueprint(user_blueprint)

@app.route("/")
def hello_world():
    return render_template('index.html')