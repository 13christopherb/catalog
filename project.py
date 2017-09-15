from flask import Flask, session, render_template,\
     request, redirect, jsonify, url_for, flash, escape, abort
from flask_oauth import OAuth
from flask_login import LoginManager, UserMixin, login_user,\
     logout_user, current_user

from functools import wraps

from forms import ItemForm

from models import User, Item, Category, db

from config import Auth

"""A web app that functions as an inventory tracker"""

FACEBOOK_APP_ID = Auth.FACEBOOK_APP_ID
FACEBOOK_APP_SECRET = Auth.FACEBOOK_APP_SECRET

SECRET_KEY = 'development key'

"""Initialization and configuration"""
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///catalog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = SECRET_KEY

lm = LoginManager(app)

oauth = OAuth()

facebook = oauth.remote_app('facebook',
                            base_url='https://graph.facebook.com/',
                            request_token_url=None,
                            access_token_url='/oauth/access_token',
                            authorize_url='https://www.facebook.com'
                                          '/dialog/oauth',
                            consumer_key=FACEBOOK_APP_ID,
                            consumer_secret=FACEBOOK_APP_SECRET,
                            request_token_params={'scope': 'email'}
                            )


@lm.user_loader
def load_user(id):
    return User.query.get(id)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    return render_template('index.html', current_user=current_user)


def create_category(name):
    """
    Creates a category if it does not exist or fetches existing category

    :param name: name of the category
    :return: the category with the provided name
    """

    category_query = db.session.query(
        Category.name.distinct().label("name"))
    categories = [row.name for row in category_query.all()]

    if name in categories:
        category = Category.query.filter_by(name=name).first()
    else:
        category = Category(name=name)
        db.session.add(category)
    return category


@app.route('/inventory', defaults={'filter': None}, methods=['GET', 'POST'])
@app.route('/inventory/<filter>', methods=['GET', 'POST'])
@login_required
def inventory(filter):
    """
    Function for viewing and adding items to a user

    :param filter: optional string from url to filter items by name
    """

    form = ItemForm(request.form)

    if request.method == 'POST' and form.validate():
        item = Item(name=form.name.data, quantity=form.quantity.data,
                    user_id=current_user.id)
        category = create_category(form.category.data.lower())

        item.add_category(category)
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('inventory'))

    items = current_user.items

    category_query = db.session.query(
        Category.name.distinct().label("name"))
    categories = [row.name for row in category_query.all()]

    if filter is not None:
        items = items.filter(Item.categories.any(name=filter)).all()
    return render_template('inventory.html', items=items,
                           categories=categories, form=form)


@app.route('/items/<obj_id>', methods=['GET', 'POST'])
@login_required
def view_item(obj_id):
    """
    Function for viewing a specific item

    :param obj_id: the id of the item to be viewed
    """

    item = Item.query.filter_by(id=obj_id).first()
    if item is None:
        return redirect(url_for('inventory'))
    if item.user_id == current_user.id:
        if request.method == 'DELETE':
            db.session.delete(item)
            db.session.commit()
            return redirect(url_for('inventory'))

        return render_template('item.html', item=item)
    else:
        return abort(403)


@app.route('/delete_item/<obj_id>', methods=['GET'])
@login_required
def delete_item(obj_id):
    """
    Function for deleting a specific item

    :param obj_id: id of item to be deleted
    """

    item = Item.query.filter_by(id=obj_id).one_or_none()
    if item.user_id == current_user.id:
        """Delete category if item to be deleted is only item in category"""
        for category in item.categories:
            if len(category.items.all()) == 1:
                db.session.delete(category)
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('inventory'))


@app.route('/remove_category/<item_id>/<category_id>', methods=['GET', 'POST'])
@login_required
def remove_category(item_id, category_id):
    item = Item.query.filter_by(id=item_id).one_or_none()
    category = Category.query.filter_by(id=category_id).one_or_none()
    if item.user_id == current_user.id:
        item.remove_category(category)
        # Deletes unused category
        if len(category.items.all()) == 0:
            db.session.delete(category)
            db.session.commit()
        return redirect(url_for('view_item', obj_id=item.id))
    else:
        return abort(403)


@app.route('/edit_item/<obj_id>', methods=['GET', 'POST'])
@login_required
def edit_item(obj_id):
    """
    Function for editing a specific item if it exists

    :param obj_id: id of item to be edited
    """

    item = Item.query.filter_by(id=obj_id).first()
    form = ItemForm(request.form)
    if item is None:
        return redirect(url_for('inventory'))
    if item.user_id == current_user.id:
        if request.method == 'POST':
            if form.name.data:
                item.name = form.name.data
            if form.quantity.data is not None:
                item.quantity = form.quantity.data
            category = create_category(form.category.data.lower())
            if category not in item.categories and form.category.data:
                item.add_category(category)

            db.session.commit()
            return redirect(url_for('view_item', obj_id=item.id))
        return render_template('edit_item.html', item=item, form=form)
    else:
        return abort(403)


# Login/logout using facebook oauth2

@app.route('/login')
def login():
    """Logs in user if not logged in"""

    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    return facebook.authorize(callback=url_for('facebook_authorized',
                                               next=request.args.get('next') or
                                               request.referrer or None,
                                               _external=True))


@app.route('/logout')
@login_required
def logout():
    """Logs user out if logged in"""

    logout_user()
    return redirect(url_for('index'))


@app.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    user = User.query.filter_by(name=me.data['name']).one_or_none()
    if not user:
        user = User(name=me.data['name'])
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


# API

@app.route('/api/v1.0/item/<obj_id>', methods=['GET'])
def get_item(obj_id):
    """
    Returns a json object representing an item

    :param obj_id: id for item to be returned
    :return: json representation of item
    """

    item = Item.query.filter_by(id=obj_id).one_or_none()
    return jsonify(item.serialize)

if __name__ == '__main__':
    db.init_app(app)
    db.app = app
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
