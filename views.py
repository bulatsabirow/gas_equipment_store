from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from ORM import *
from forms import RegisterForm, AuthForm
from login import *
app = Flask(__name__)
app.secret_key = '12345'
app.config['SECRET_KEY'] = 'abc'
app.permanent_session_lifetime = timedelta(days=365)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(email):
    return UserModel.select(email)


@app.route('/goods')
def goods_list():
    return render_template('main.html', **{
        'title': 'Магазин газового оборудования',
        'goods': GoodsModel.all(),
    })


@app.route('/register', methods=['GET', 'POST'])
def registration():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = generate_password_hash(form.password.data)
        is_admin = False
        user = UserModel(name, email, password, is_admin)
        user.insert()
        login_user(user)
        print(current_user.is_authenticated)

    return render_template('register.html', form=form)


@app.route('/auth', methods=['POST', 'GET'])
def auth():
    message = None
    form = AuthForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = UserModel.find_user(email)
        if user is not None and check_password_hash(user.password, password):
            login_user(user)
        else:
            message = 'Неправильные адрес электронной почты или пароль'
    return render_template('auth.html', **{
        'message': message,
        'form': form,
    })


@app.route('/logout')
def logout():
    logout_user()
    return redirect('goods')


@app.route('/product/<int:id>')
def product(id):
    return render_template('product.html', **{

    })


if __name__ == "__main__":
    app.run(port=8000, debug=True)
