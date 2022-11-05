import os
from datetime import timedelta
from typing import Callable

from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_login import current_user, login_user, logout_user, login_required, AnonymousUserMixin
from werkzeug.datastructures import FileStorage
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from ORM import *
from forms import RegisterForm, AuthForm, AddProductForm, EditProductForm
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
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = generate_password_hash(form.password.data)
        is_admin = False
        user = UserModel(name, email, password, is_admin)
        user.insert()
        login_user(user)
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
            print(current_user.is_authenticated)
        else:
            message = 'Неправильные адрес электронной почты или пароль'
        if 'next' in request.args:
            return redirect(request.args.get('next'))
    return render_template('auth.html', **{
        'message': message,
        'form': form,
    })


@app.route('/logout')
def logout_view():
    logout_user()
    return redirect(url_for('goods_list'))


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


def admin_required(func: Callable) -> Callable:
    if type(current_user) == AnonymousUserMixin  and current_user.is_admin:
        return func
    return raw_page_not_found


@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product_view():
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
            GoodsModel(title=title, description=description, price=price,
                       category=category, image=image.filename if image.filename else None, count=count, brand=brand, id='').insert()
        return render_template('edit_product.html', **{
            'form': form,
            'is_add': True,
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


@app.route('/admin/delete_product')
def delete_product_view():
    if getattr(current_user, 'is_admin', None):
        return render_template('delete_product.html')
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


@app.route('/admin/edit_product/<int:id>', methods=['GET', 'POST'])
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

        return render_template('edit_product.html', **{
            'form': form,
            'is_add': False,
        })
    else:
        abort(404)


@app.route('/admin/append_to_cart/<int:id>')
def append_to_cart(id):
    if request.method == 'GET':
        session.modified = True
        unit = GoodsModel.select(id)
        print(request.args)
        print('before:', session['cart'])
        unit.update(count=unit.count - int(request.args.get('count', 0)))
        if session.get('cart', None) is None:
            session['cart'] = {}
        session['cart'][unit.id] = 1
        print('after:', session['cart'])
        print('cart[unit.id]:', session['cart'][unit.id])
        return {}
    else:
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
"""
                    {#$('#count-input{{ item.id }}').on('change', function() {#}
                        {#document.querySelector('#total_price').innerText = `Всего: ${+document.querySelector('#total_price').innerText.match(/[\d/.]+/g)[0] + +{{item.price}}}`;#}
                        {#document.querySelector('#product{{ item.id }}-price').innerText =#}
                        {#    `Стоимость: ${+document.querySelector('#product{{ item.id }}-price').innerText.match(/[\d/.]+/g)[0] + +{{ item.price }}}`#}
                    {#    $.ajax({#}
                    {#        url: "{{ url_for('change_product_count',id=item.id) }}",#}
                    {#        method: 'post',#}
                    {#        data:{'count': +$("#count-input{{ item.id }}").val()},#}
                    {#        dataType: 'html',#}
                    {#        success: function (data) {#}
                    {#            alert(data);#}
                    {#            alert(document.querySelector('#total_price').innerText.match(/[\d/.]+/g)[0]);#}
                    {#            alert(-{{item.price}});#}
                    {#            alert(document.querySelector('#total_price').innerText.match(/[\d/.]+/g)[0]-{{item.price}});#}
                    {#            if(data['up']){#}
                    {#                let res = document.querySelector('#product{{ item.id }}-price').innerText.match(/[\d/.]+/g)[0]-{{ item.price }};#}
                    {#                document.querySelector('#total_price').innerText = `Всего: ${document.querySelector('#total_price').innerText.match(/[\d/.]+/g)[0]-{{item.price}}}`;#}
                    {#                document.querySelector('#product{{ item.id }}-price').innerText =#}
                    {#                `Стоимость: ${res}`;#}
                    {#            } else {#}
                    {#                document.querySelector('#total_price').innerText = `Всего: ${+document.querySelector('#total_price').innerText.match(/[\d/.]+/g)[0] + +{{item.price}}}`;#}
                    {#                document.querySelector('#product{{ item.id }}-price').innerText =#}
                    {#                `Стоимость: ${+document.querySelector('#product{{ item.id }}-price').innerText.match(/[\d/.]+/g)[0] + +{{ item.price }}}`;#}
                    {#            }#}
                    {#        }#}
                    {#    })#}
                    {#})#}

"""

if __name__ == "__main__":
    app.run(port=7000, debug=True)
