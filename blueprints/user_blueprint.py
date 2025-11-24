from flask import Blueprint

user_blueprint = Blueprint('user_blueprint', __name__)

@user_blueprint.route("/login")
def login():
    return 'login'