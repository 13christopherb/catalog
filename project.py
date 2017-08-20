from flask import Flask, session, render_template,\
     request, redirect, jsonify, url_for, flash, escape
from flask_oauth import OAuth
from flask_login import LoginManager, UserMixin, login_user,\
     logout_user, current_user

from forms import ItemForm

from flask_sqlalchemy import SQLAlchemy
from database_setup import User, Item

from config import Auth


FACEBOOK_APP_ID = Auth.FACEBOOK_APP_ID
FACEBOOK_APP_SECRET = Auth.FACEBOOK_APP_SECRET

SECRET_KEY = 'development key'

# Initialization and configuration
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
app.secret_key = SECRET_KEY

db = SQLAlchemy(app)
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
@app.route('/inventory')
def inventory():
    print(current_user.items.first().name)
    return render_template('index.html')


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

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
