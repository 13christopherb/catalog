import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'


if __name__ == '__main__':
    db.init_app(app)
    db.app = app
    db.create_all()
