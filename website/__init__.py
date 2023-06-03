from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()

def create_app():
    application = Flask(__name__)

    application.config['SECRET_KEY'] = '54ge5rg4e4eshg4ser324243thg4s5h4esr8t674'
    application.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://ebroot:Yamaha189!@awseb-e-rvvktpucyf-stack-awsebrdsdatabase-ijbluxt9ye2s.cavhriuewzv4.us-east-1.rds.amazonaws.com:3306/ebdb'
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(application)


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

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return application

