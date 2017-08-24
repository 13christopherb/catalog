from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

categories = db.Table('categories',
                      db.Column('category_id', db.Integer, db.ForeignKey('category.id')),
                      db.Column('item_id', db.Integer, db.ForeignKey('item.id'))
)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    items = db.relationship('Item', backref='user',
                            lazy='dynamic')


class Item(db.Model):
    """Represents an item in an inventory"""
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    categories = db.relationship('Category', secondary=categories,
                                 backref=db.backref('items', lazy='dynamic'))

    @property
    def serialize(self):
        """
        Serializes the Item to a JSON object
        
        :return: JSON representation of the item
        """
        categories = []
        for category in self.categories:
            categories.append(category.name)
        return {
            'id':       self.id,
            'name':     self.name,
            'categories': categories,
            'user_id':  self.user_id
        }

    def add_category(self, category):
        """
        Adds a category to the item's list of categories
        
        :param category: The category to be added
        """
        self.categories.append(category)
        return self

    def remove_category(self, category):
        if len(self.categories) > 1:
            self.categories.remove(category)
            return self


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)