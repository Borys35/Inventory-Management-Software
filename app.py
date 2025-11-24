from flask import Flask
from blueprints.user_blueprint import user_blueprint

app = Flask(__name__)
app.register_blueprint(user_blueprint)

@app.route("/")
def hello_world():
    return "<p>Hello</p>"