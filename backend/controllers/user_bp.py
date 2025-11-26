from flask import Blueprint, session, redirect, request, render_template, flash, g
from lib.db import get_db_connection
from models.user import User

user_bp = Blueprint('user', __name__)

@user_bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if not user_id:
        g.user = None
    else:
        conn = get_db_connection()
        user_model = User(conn)

        user = user_model.get_user_by_id(user_id)

        g.user = user

@user_bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        data = request.form
        conn = get_db_connection()
        user_model = User(conn)

        user_id = user_model.create_user(
            data.get('username'),
            data.get('email'),
            data.get('password'),
            data.get('role')
        )

        conn.close()

        if user_id:
            flash("Registered successfully")
            return redirect("/login")
        else:
            flash("Incorrect data")
            return render_template('register.html'), 400
    return None

@user_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    elif request.method == 'POST':
        data = request.form
        conn = get_db_connection()
        user_model = User(conn)

        user = user_model.verify_login(
            data.get('email'),
            data.get('password')
        )

        conn.close()

        if user:
            session['user_id'] = user['id']

            flash("Logged in successfully")
            return redirect("/")
        else:
            flash("Incorrect data")
            return render_template('login.html'), 400

@user_bp.route("/logout", methods=['GET'])
def logout():
    session.clear()
    return redirect("/")