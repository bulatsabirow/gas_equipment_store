from flask import Flask, render_template

app = Flask(__name__)


@app.route('/goods')
def goods_list():
    return render_template('main.html', **{
        'title': 'Магазин газового оборудования'
    })
