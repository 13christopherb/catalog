from flask import Flask, session, render_template,\
     request, redirect, jsonify, url_for, flash, escape, abort
from flask_oauth import OAuth
from flask_login import LoginManager, UserMixin, login_user,\
     logout_user, current_user

from forms import ItemForm, ItemDelete

from models import User, Item, db

from config import Auth

FACEBOOK_APP_ID = Auth.FACEBOOK_APP_ID
FACEBOOK_APP_SECRET = Auth.FACEBOOK_APP_SECRET

SECRET_KEY = 'development key'

# Initialization and configuration
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
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


@app.route('/')
def index():
    return render_template('index.html', current_user=current_user)


# Displays all the items belonging to the current user
# optionally filters by category
@app.route('/inventory', defaults={'filter': None}, methods=['GET', 'POST'])
@app.route('/inventory/<filter>', methods=['GET', 'POST'])
def inventory(filter):
    form = ItemForm(request.form)
    if request.method == 'POST' and form.validate():
        item = Item(name=form.name.data, quantity=form.quantity.data,
                    category=form.category.data.lower(),
                    user_id=current_user.id)
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('inventory'))

    items = current_user.items

    category_query = db.session.query(
        Item.category.distinct().label("category"))
    categories = [row.category for row in category_query.all()]

    if filter is not None:
        items = items.filter_by(category=filter)
    return render_template('inventory.html', items=items,
                           categories=categories, form=form)


@app.route('/items/<obj_id>', methods=['GET', 'POST', 'DELETE'])
def view_item(obj_id):
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


# Creates a new item belonging to current user
@app.route('/new_item', methods=['GET', 'POST'])
def new_item():
    form = ItemForm(request.form)
    if request.method == 'POST' and form.validate():
        item = Item(name=form.name.data, quantity=form.quantity.data,
                    user_id=current_user.id)
        db.session.add(item)
        db.session.commit()
        flash('Thanks for registering')
        return redirect(url_for('index'))
    return render_template('new_item.html', form=form)


@app.route('/delete_item/<obj_id>', methods=['GET'])
def delete_item(obj_id):
    item = Item.query.filter_by(id=obj_id).first()
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('inventory'))


@app.route('/edit_item/<obj_id>', methods=['GET', 'POST'])
def edit_item(obj_id):
    item = Item.query.filter_by(id=obj_id).first()
    form = ItemForm(request.form)
    if item is None:
        return redirect(url_for('inventory'))
    if item.user_id == current_user.id:
        if request.method == 'POST':
            item.name = form.name.data
            item.quantity = form.quantity.data
            db.session.commit()
            return redirect(url_for('view_item', obj_id=item.id))
        return render_template('edit_item.html', item=item, form=form)
    else:
        return abort(403)


# Login/logout using facebook oauth2

@app.route('/login')
def login():
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    return facebook.authorize(callback=url_for('facebook_authorized',
                                               next=request.args.get('next') or
                                               request.referrer or None,
                                               _external=True))


@app.route('/logout')
def logout():
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
    user = User.query.filter_by(name=me.data['name']).first()
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
    item = Item.query.filter_by(id=obj_id).first()
    return jsonify(item.serialize)

if __name__ == '__main__':
    db.init_app(app)
    db.app = app
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
