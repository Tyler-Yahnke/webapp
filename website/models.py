from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(45), unique=True)
    name = db.Column(db.String(45))
    password = db.Column(db.String(50))
    is_active = db.Column(db.String(45))
    secret_key = db.Column(db.String(45))
    last_password_update = db.Column(db.DateTime)
    logged_in = db.Column(db.String(45))
    last_login_date = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)

class Discounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Brand = db.Column(db.String(45), unique=True)
    low = db.Column(db.String(45))
    medium = db.Column(db.String(50))
    high = db.Column(db.String(45))

class SwapRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Date = db.Column(db.String(45), unique=True)
    three_Year = db.Column('3Year',db.String(45))
    four_Year = db.Column('4Year',db.String(50))
    five_Year = db.Column('5Year',db.String(45))

class PrimeRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Date = db.Column(db.String(45), unique=True)
    Rate = db.Column(db.String(45))

class EmbeddedFee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Fee_Buy_Down = db.Column(db.String(45), unique=True)
    _60_60 = db.Column('60/60', db.String(45))
    _60_84 = db.Column('60/84', db.String(45))
    _84_84 = db.Column('84/84', db.String(45))
    _84_120 = db.Column('84/120', db.String(45))
    _120_120 = db.Column('120/120', db.String(45))

class Spreads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    PricingBasis = db.Column(db.String(45), unique=True)
    Month = db.Column(db.String(45))
    _60_60 = db.Column('60/60', db.String(45))
    _60_84 = db.Column('60/84', db.String(45))
    _84_84 = db.Column('84/84', db.String(45))
    _84_120 = db.Column('84/120', db.String(45))
    _120_120 = db.Column('120/120', db.String(45))
    Start = db.Column(db.String(45))
    End = db.Column(db.String(45))
    RateType = db.Column(db.String(45))
