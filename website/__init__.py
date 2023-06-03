from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_sslify import SSLify
from os import path
from flask_login import LoginManager
from google.oauth2 import service_account
import pygsheets
import json

db = SQLAlchemy()
APC_DB = "APC_Database.db"

def create_app():
    application = Flask(__name__)
    sslify = SSLify(application)
    application.config['SECRET_KEY'] = '54ge5rg4e4eshg4serthg4s5h4esr8t674'
    application.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{APC_DB}'
    db.init_app(application)

    from .views import views
    from .auth import auth
    from .fees import fees

    application.register_blueprint(auth, url_prefix='/')
    application.register_blueprint(fees, url_prefix='/')
    application.register_blueprint(views, url_prefix='/')

    from .models import User

    with application.app_context():
        if not path.exists(APC_DB):
            db.create_all()
            print('Created Database!')

    create_database(application)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(application)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return application

def create_database(application):
    with application.app_context():
        with open('creds.json', 'r') as file:
            cred = json.load(file)

        SCOPES = ('https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive')
        my_credentials = service_account.Credentials.from_service_account_info(cred, scopes=SCOPES)

        # Call the Sheets API
        api_failure = 0
        fail_string = ''
        try:
            gc = pygsheets.authorize(custom_credentials=my_credentials)
            rate_file = gc.open_by_key('13MUnNC1va0bEE_fGU5P0RFLHf-CEqWxOVk6YmEVwB1c')

            try:
                users = rate_file.worksheet_by_title('Users')

                try:
                    users_df = users.get_as_df()

                    from .models import User

                    with db.session.begin_nested():
                        existing_emails = User.query.with_entities(User.email).all()
                        existing_emails = set([email[0] for email in existing_emails])

                        for _, row in users_df.iterrows():
                            email = row['email']
                            if email not in existing_emails:
                                user = User(email=email, name=row['name'], is_active=row['is_active'])
                                db.session.add(user)

                        User.query.filter(User.email.notin_(users_df['email'])).delete(synchronize_session=False)

                        db.session.commit()

                    print('Data inserted into the "user" table.')
                except Exception as e:
                    print(f"Error inserting data into the 'user' table: {str(e)}")
            except:
                print('fail 2')
        except:
            print('fail 1')

application = create_app()

if __name__ == '__main__':
    application.run(debug=True)