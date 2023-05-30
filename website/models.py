from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from google.oauth2 import service_account
import pygsheets
import json

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    name = db.Column(db.String(150))
    password = db.Column(db.String(150))
    is_active = db.Column(db.String(150))


