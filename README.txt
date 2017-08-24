Basic app to catalog items belonging to a user

Dependencies:
Flask
Flask-OAuth
Flask-Login
Flask-SQLAlchemy
WTForms

To run app, clone the repository and run database_setup.py to initialize the database. For Facebook login,
create config.py with an Auth class containing the Facebook app id and Facebook client secret.

Run project.py to begin the server and go to http://localhost:5000 to access the app.
