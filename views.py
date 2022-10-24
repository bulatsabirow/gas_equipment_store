from datetime import timedelta

from flask import Flask, render_template, request, redirect, url_for
from flask_login import current_user, login_user

from ORM import *
from login import *

app = Flask(__name__)
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
        password = request.form.get('password')
        is_admin = False
        user = UserModel(name, email, password, is_admin)
        UserModel.insert(user)
        login_user(user)
        print(current_user.is_authenticated)

    return render_template('register.html')


if __name__ == "__main__":
    app.run(port=8000, debug=True)
