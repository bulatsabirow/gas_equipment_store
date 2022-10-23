from flask import Flask, render_template
from models import *

app = Flask(__name__)
db = DataBase()


@app.route('/goods')
def goods_list():
    return render_template('main.html', **{
        'title': 'Магазин газового оборудования',
        'table': db.user,
    })


if __name__ == "__main__":
    app.run(port=5000, debug=True)