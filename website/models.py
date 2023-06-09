from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(45), unique=True)
    name = db.Column(db.String(45))
    password = db.Column(db.String(50),onupdate=True)
    is_active = db.Column(db.String(45))
    secret_key = db.Column(db.String(45))
    last_password_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Discounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Brand = db.Column(db.String(45), unique=True)
    low = db.Column(db.String(45))
    medium = db.Column(db.String(50))
    high = db.Column(db.String(45))


