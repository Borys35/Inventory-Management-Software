from flask import Flask
import psycopg2
from lib.init_db import init_tables
from blueprints.user_blueprint import user_blueprint

app = Flask(__name__)

conn = psycopg2.connect(database="inventory_db", user="postgres",
                        password="admin", host="localhost", port="5432")

cur = conn.cursor()

init_tables(cur)

app.register_blueprint(user_blueprint)

@app.route("/")
def hello_world():
    return "<p>Hello</p>"