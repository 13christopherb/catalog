from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from database_setup import User, Item

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
db = SQLAlchemy(app)


@app.route('/')
def index():
    user = User.query.first()
    item = Item.query.first()
    return render_template('index.html', user=user, item=item)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
