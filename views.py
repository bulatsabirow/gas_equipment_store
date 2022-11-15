import os
import re
import time
from datetime import timedelta, datetime, timezone
from typing import Callable
from uuid import uuid4

import psycopg2

from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_login import current_user, login_user, logout_user, login_required, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from ORM import GoodsModel, UserModel, OrderModel, BookingModel, CATEGORY_CHOICES, BRAND_CHOICES
from forms import RegisterForm, AuthForm, AddProductForm, EditProductForm, EditProfileForm
from login import *

app = Flask(__name__)
app.secret_key = '12345'
app.config['SECRET_KEY'] = '12345'
app.config['UPLOAD_FOLDER'] = '/Users/bulat/PycharmProjects/gas_equipment_store/static/img'
app.permanent_session_lifetime = timedelta(days=365)
login_manager.init_app(app)


def raw_page_not_found():
    return render_template('error.html')


@app.errorhandler(404)
def page_not_found(exception):
    return raw_page_not_found()


@login_manager.user_loader
def load_user(email: str):
    return UserModel.select(email)


@app.route('/goods')
def goods_list():
    print('goods_list', session)
    print("SESSION{CART}:", session.get('cart', None))
    text_filter = request.args.get('text_filter', None)
    brands = set()
    categories = set()
    for param in request.args:
        if param in BRAND_CHOICES:
            brands.add(request.args.get(param))
        if param in CATEGORY_CHOICES:
            categories.add(request.args.get(param))
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
        'chosen_categories': categories,
        'chosen_brands': brands,
        'search': text_filter,
    })


@app.route('/register', methods=['GET', 'POST'])
def registration():
    form = RegisterForm()
    error = None
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = generate_password_hash(form.password.data)
        is_admin = False
        user = UserModel(name, email, password, is_admin)
        if not user.insert():
            error = True
        else:
            login_user(user)
    return render_template('register.html', form=form, error=error)


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
            print(current_user.is_authenticated)
            if 'next' in request.args:
                return redirect(request.args.get('next'))
            return redirect(url_for('goods_list'))
        else:
            message = 'Неправильные адрес электронной почты или пароль'
    return render_template('auth.html', **{
        'message': message,
        'form': form,
    })


@app.route('/logout')
def logout_view():
    logout_user()
    return redirect(url_for('goods_list'))


@app.route('/clear_session', methods=['POST', 'GET'])
def clear_session():
    session.pop('cart', None)
    time.sleep(0.3)
    return redirect(url_for('my_page_view'))


@app.route('/product/<int:id>', methods=['POST', 'GET'])
def product(id):
    session.modified = True
    value = GoodsModel.select(id).to_json()
    # if request.method == 'POST':
    #     if session.get('cart', None) is None:
    #         session['cart'] = {}
    #     session['cart'][value['id']] = session['cart'].get(value['id'], 0) + \
    #                                    1
    #     return redirect(url_for('cart'))
    in_wishlist = value['id'] in session.get('wishlist', {})
    return render_template('product.html', **{
        'product': GoodsModel.select(id).to_json(),
        'in_wishlist': in_wishlist,
    })


@app.route('/cart')
def cart():
    print('cart', session)
    print('cart session[cart]:', session.get('cart', None))
    goods = GoodsModel.find_all(session.get('cart', None))
    total_amount = None
    if goods:
        total_amount = sum((item.price * session['cart'][item.id] for item in goods))
    return render_template('cart.html', **{
        'cart': goods,
        'total_amount': total_amount,
    })


@app.route('/wishlist')
def wishlist_view():
    wishlist = GoodsModel.find_all(session.get('wishlist', None))
    return render_template('wishlist.html', **{
        'wishlist': wishlist,
    })


@app.route('/add_to_wishlist/<int:id>', methods=['GET', 'POST'])
def add_to_wishlist(id):
    print(session.get('wishlist', None))
    if request.method == 'POST':
        session.modified = True
        value = GoodsModel.select(id).to_json()
        if session.get('wishlist', None) is None:
            session['wishlist'] = {}
        in_wishlist = value['id'] in session['wishlist']
        if not in_wishlist:
            session['wishlist'][value['id']] = True
        else:
            session['wishlist'].pop(value['id'])
        return {'in_wishlist': in_wishlist}
    abort(404)


@app.route('/remove_from_wishlist/<int:id>', methods=["GET", "POST"])
def remove_from_wishlist(id):
    print('wishlist_before_remove:', session['wishlist'])
    if request.method == 'POST':
        session.modified = True
        try:
            session['wishlist'].pop(str(id))
        except KeyError:
            pass
    print('wishlist_after_remove:', session['wishlist'])
    abort(404)


@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product_view():
    error = None
    if type(current_user) != AnonymousUserMixin and current_user.is_admin:
        form = AddProductForm()
        if form.validate_on_submit():
            title = form.title.data
            description = form.description.data
            price = float(form.price.data)
            category = form.category.data if form.category.data != 'null_category' else None
            brand = form.brand.data if form.brand.data != 'null_brand' else None
            image = request.files['file']
            count = int(form.count.data)
            print(request.files['file'])
            print('image:', image)
            print('image.filename', image.filename)
            if image.filename:
                image.save(os.path.join(app.config['UPLOAD_FOLDER'],
                                                  secure_filename(image.filename)))
            product_model = GoodsModel(title=title, description=description, price=price,
                       category=category, image=image.filename if image.filename else None, count=count, brand=brand, id='')
            error = not product_model.insert()
        return render_template('edit_product.html', **{
            'form': form,
            'is_add': True,
            'error': error,
        })
    else:
        abort(404)


@app.route('/admin')
def admin_view():
    print('curr:', current_user)
    print(session.get('cart', None))
    if getattr(current_user, 'is_admin', None):
        return render_template('admin.html', **{
            'products': GoodsModel.all(),
        })
    else:
        abort(404)


@app.route('/delete_product_service/<int:id>', methods=['GET', 'POST'])
def delete_product(id):
    unit = GoodsModel.select(id)
    if request.method == 'POST':
        session.modified = True
        print(session.get('cart', None))
        print('cond:', 'cart' in session and str(unit.id) in session['cart'])
        if 'cart' in session and str(unit.id) in session['cart']:
            session['cart'].pop(str(unit.id))
        unit.remove()
        return {}
    abort(404)


@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product_view(id):
    if getattr(current_user, 'is_admin', None):
        unit = GoodsModel.select(id)
        json_unit = unit.to_json()
        diff = {}
        if unit is None:
            abort(404)
        form = EditProductForm(title=unit.title,
                               description=unit.description,
                               price=unit.price,
                               category=unit.category,
                               brand=unit.brand,
                               count=unit.count)
        print(form.errors)
        print(form.data)
        print(form.validate_on_submit())
        if form.validate_on_submit():
            # title = form.title.data
            # description = form.description.data
            # price = float(form.price.data)
            # category = form.category.data if form.category.data != 'null_category' else None
            # brand = form.brand.data if form.brand.data != 'null_brand' else None
            # count = int(form.count.data)
            for attr in form.data:
                if attr in json_unit and form.data[attr] != json_unit[attr]:
                    if attr == 'image' and not form.data[attr].filename:
                        pass
                    else:
                        diff[attr] = form.data[attr]

            image = request.files['file']
            if image.filename:
                image.save(os.path.join(app.config['UPLOAD_FOLDER'],
                           secure_filename(image.filename)))
                diff['image'] = image.filename
            unit.update(**diff)
            return redirect(url_for('product', id=unit.id))

        return render_template('edit_product.html', **{
            'form': form,
            'is_add': False,
        })
    else:
        abort(404)


@app.route('/append_offer_to_database', methods=['POST', 'GET'])
def append_offer():
    print('append_offer', session)
    if request.method == 'POST':
        session.modified = True
        identification: str = uuid4().hex
        print('id:', identification)
        total_amount = request.form.get('total_amount')
        print(total_amount)
        email = current_user.email
        BookingModel.insert(email=email, time_value=datetime.now(timezone.utc),
                            uuid_key=identification, total_amount=float(total_amount))
        booking = BookingModel.select(uuid_id=identification)
        print('booking:', booking)
        print('session[cart]', session['cart'])
        for product_id in session['cart']:
            OrderModel.insert(product_id, booking.id, session['cart'][product_id])
            value = GoodsModel.select(product_id)
            value.update(count=value.count-session['cart'][product_id])
        print('SESSION after clear:', session)
    abort(404)


@app.route('/append_to_cart/<int:id>', methods=["POST", "GET"])
def append_to_cart(id):
    if request.method == 'POST':
        session.modified = True
        unit = GoodsModel.select(id)
        print('before:', session.get('cart', None))
        if session.get('cart', None) is None:
            session['cart'] = {}
        session['cart'][unit.id] = 1
        print('after:', session['cart'])
        print('cart[unit.id]:', session['cart'][unit.id])
    abort(404)


@app.route("/remove_from_cart/<int:id>", methods=['GET', 'POST'])
def remove_from_cart(id):
    if request.method == 'POST':
        unit = GoodsModel.select(id)
        session.modified = True
        price = unit.price
        print('before_remove:', session['cart'])
        count = session['cart'].pop(str(id))
        print('after_remove:', session['cart'])
        return {
            'price': price,
            'count': count,
                }
    abort(404)


@app.route('/change_product_count/<int:id>', methods=['GET', 'POST'])
def change_product_count(id):
    if request.method == 'POST':
        session.modified = True
        print('before change count:', session['cart'])
        print(int(request.form.get('count')))
        up = session['cart'][str(id)] < int(request.form.get('count'))
        prev = session['cart'][str(id)]
        session['cart'][str(id)] = int(request.form.get('count'))
        print('after change count:', session['cart'])
        return {'up': up, 'prev': prev}
    abort(404)


@app.route('/my')
@login_required
def my_page_view():
    user_bookings = BookingModel.select_by_user(current_user.email)
    return render_template('my.html', **{
        'bookings': user_bookings,
    })


@app.route('/booking/<uuid_id>')
@login_required
def my_orders_view(uuid_id):
    orders_with_titles = OrderModel.select_orders_by_uuid_id(uuid_id)
    print('orders:', orders_with_titles)
    return render_template('order.html', **{
        'orders': orders_with_titles,
        'id': uuid_id,
    })


@app.route('/change_user_data', methods=['GET', 'POST'])
@login_required
def change_user_data():
    error = False
    user = current_user
    json_user = user.to_json()
    form = EditProfileForm(name=user.name, email=user.email)
    diff = {}
    if form.validate_on_submit():
        for attr in form.data:
            if attr in json_user and form.data[attr] != json_user[attr]:
                if attr == 'password':
                    if re.search(r'\w|\d', form.data[attr]):
                        diff[attr] = generate_password_hash(form.data[attr])
                    else:
                        continue
                else:
                    diff[attr] = form.data[attr]
        if 'email' in diff:
            response = UserModel.select(diff['email'])
            if response:
                error = True
        if diff and not error:
            user.update(**diff)
            if 'email' in diff:
                logout_user()
                login_user(UserModel.select(diff['email']))
            return redirect(url_for('my_page_view'))
    return render_template('edit_profile.html', **{'form': form, 'error': error})


@app.route("/delete_profile", methods=['GET', 'POST'])
@login_required
def delete_profile_view():
    if request.method == 'POST':
        UserModel.select(current_user.email).remove()
        logout_user()
        return redirect(url_for('goods_list'))
    return render_template('delete_profile.html')


if __name__ == "__main__":
    app.run(port=7000, debug=True)
