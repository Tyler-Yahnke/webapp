from flask import Flask, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_apscheduler import APScheduler
from pytz import timezone
from .index_pull import index_rate_updates
from datetime import timedelta, datetime

db = SQLAlchemy()
mail = Mail()

def create_app():
    application = Flask(__name__)

    #Setting up connection to DB
    application.config['SECRET_KEY'] = '54ge5rg4e4eshg4ser324243thg4s5h4esr8t674'
    application.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ebroot:Yamaha189!@awseb-e-rvvktpucyf-stack-awsebrdsdatabase-ijbluxt9ye2s.cavhriuewzv4.us-east-1.rds.amazonaws.com:3306/ebdb'
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    application.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=90)  # Set session to 1.5 hour

    #creating mail server
    application.config['MAIL_SERVER'] = 'email-smtp.us-east-1.amazonaws.com'
    application.config['MAIL_PORT'] = 587
    application.config['MAIL_USE_TLS'] = True
    application.config['MAIL_USERNAME'] = 'AKIAT6OFV5CDXO7VJOVE'
    application.config['MAIL_PASSWORD'] = 'BD5UWiIMuiJtY1SHSKRCIBF2NOe0ZrbRhJq2QK+lOVgr'

    mail = Mail(application)

    mail.init_app(application)
    db.init_app(application)

    #Checking to see if user session has expire and routing to login page
    @application.before_request
    def check_user_session():
        if 'logged_in' not in session and request.endpoint != 'auth.login':
            return redirect(url_for('auth.login'))

    #Updating last activity for each user each time the server is called
    @application.before_request
    def update_last_activity():
        if current_user.is_authenticated:
            current_user.last_activity = datetime.now()
            db.session.commit()


    from .views import views
    from .auth import auth
    from .fees import fees

    application.register_blueprint(auth, url_prefix='/')
    application.register_blueprint(fees, url_prefix='/')
    application.register_blueprint(views, url_prefix='/')

    from .models import User


    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(application)

    # scheduler
    scheduler = APScheduler()
    application.config['SCHEDULER_API_ENABLED'] = True

    #Updating Prime and Swap rate nightly
    @scheduler.task('cron', id='index_update', day_of_week='*', hour=23, minute=58, timezone=timezone('US/Pacific'))
    def index_update():
        index_rate_updates()

    #Checking to see when last activity was and updating user logged in
    @scheduler.task('interval', id='cleanup_logged_in', minutes=60)
    def cleanup_logged_in():
        with application.app_context():
            expired_users = User.query.filter(User.last_activity < datetime.now() - timedelta(minutes=90)).all()
            for user in expired_users:
                user.logged_in = False
            db.session.commit()

    scheduler.init_app(application)
    scheduler.start()

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return application

