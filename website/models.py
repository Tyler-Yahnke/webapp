from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(45), unique=True)
    name = db.Column(db.String(45))
    password = db.Column(db.String(50))
    is_active = db.Column(db.String(45))
    secret_key = db.Column(db.String(45))


