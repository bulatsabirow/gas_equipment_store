from flask import Flask, render_template, request, redirect, url_for
from models import *

app = Flask(__name__)
db = DataBase()

@app.route('/goods')
def goods_list():
    return render_template('main.html', **{
        'title': 'Магазин газового оборудования',
        'table': db.user,
    })


@app.route('/register', methods=['GET', 'POST'])
def registration():
    print(request.method)
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        db.user_insert(password, email, name)
    return render_template('register.html')


if __name__ == "__main__":
    app.run(port=5000, debug=True)