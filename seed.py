from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from database_setup import User, Item

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
db = SQLAlchemy(app)


if __name__ == '__main__':
    item = Item(name="Longclaw", quantity=1, category="Sword")
    user = User(name="Jon Snow", items=[item])
    db.session.add(user)
    db.session.add(item)
    db.session.commit()