from datetime import timedelta
import flask_bcrypt
from flask import Flask, render_template, request, redirect, url_for
from flask_login import current_user, login_user

from ORM import *
from login import *

app = Flask(__name__)
bcrypt = flask_bcrypt.Bcrypt(app)
app.secret_key = '12345'
app.permanent_session_lifetime = timedelta(days=365)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(email):
    return UserModel.select(email)


@app.route('/goods')
def goods_list():
    return render_template('main.html', **{
        'title': 'Магазин газового оборудования',
    })


@app.route('/register', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = bcrypt.generate_password_hash(request.form.get('password'))
        is_admin = False
        user = UserModel(name, email, password, is_admin)
        UserModel.insert(user)
        login_user(user)
        print(current_user.is_authenticated)

    return render_template('register.html')


@app.route('/auth', methods=['POST', 'GET'])
def auth():
    message = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = bcrypt.generate_password_hash(request.form.get('password'))
        user = UserModel.find_user(email, password)
        if user is not None:
            login_user(user)
        else:
            message = 'Неправильные адрес электронной почты или пароль'
    return render_template('auth.html', **{
        'message': message,
    })


if __name__ == "__main__":
    app.run(port=8000, debug=True)
