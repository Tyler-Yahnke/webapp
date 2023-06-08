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

class Discounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Brand = db.Column(db.String(45), unique=True)
    low = db.Column(db.String(45))
    medium = db.Column(db.String(50))
    high = db.Column(db.String(45))


