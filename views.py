from datetime import timedelta

from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from ORM import *
from forms import RegisterForm, AuthForm
from login import *

app = Flask(__name__)
app.secret_key = '12345'
app.config['SECRET_KEY'] = '12345'
app.permanent_session_lifetime = timedelta(days=365)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(email):
    return UserModel.select(email)


@app.route('/goods')
def goods_list():
    text_filter = request.args.get('text_filter', None)
    brands = []
    categories = []
    for param in request.args:
        if param in BRAND_CHOICES:
            brands.append(request.args.get(param))
        if param in CATEGORY_CHOICES:
            categories.append(request.args.get(param))
    print(text_filter, brands, categories)
    if text_filter or brands or categories:
        goods = GoodsModel.filter(text=text_filter, brand=brands if brands else None,
                                  category=categories if categories else None)
    else:
        goods = GoodsModel.all()
    return render_template('main.html', **{
        'title': 'Магазин газового оборудования',
        'goods': goods,
        'categories': CATEGORY_CHOICES,
        'brands': BRAND_CHOICES,
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


@app.route('/product/<int:id>', methods=['POST', 'GET'])
def product(id):
    session.modified = True
    value = GoodsModel.select(id).to_json()
    if request.method == 'POST':
        if session.get('cart', None) is None:
            session['cart'] = {}
        session['cart'][value['id']] = session['cart'].get(value['id'], 0) + \
                                       int(request.form.get('count', 0))
        return redirect(url_for('cart'))

    return render_template('product.html', **{
        'product': GoodsModel.select(id),
    })


@app.route('/cart')
def cart():
    goods = GoodsModel.find_all(session['cart'])
    total_amount = sum((item.price * session['cart'][item.id] for item in goods))
    return render_template('cart.html', **{
        'cart': goods,
        'total_amount': total_amount,
    })


if __name__ == "__main__":
    app.run(port=8000, debug=True)
