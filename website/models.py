from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(45), unique=True)
    name = db.Column(db.String(45))
    role = db.Column(db.String(45))
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
    Created_Date = db.Column(db.String(45), unique=True)

class PrimeRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Date = db.Column(db.String(45), unique=True)
    Rate = db.Column(db.String(45))
    Created_Date = db.Column(db.String(45), unique=True)

class EmbeddedFee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Fee_Buy_Down = db.Column(db.String(45), unique=True)
    term_60_60 = db.Column(db.String(45))
    term_60_84 = db.Column(db.String(45))
    term_84_84 = db.Column(db.String(45))
    term_84_120 = db.Column(db.String(45))
    term_120_120 = db.Column(db.String(45))

class Spreads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    PricingBasis = db.Column(db.String(45), unique=True)
    Month = db.Column(db.String(45))
    APCGrade = db.Column(db.String(45))
    term_60_60 = db.Column(db.String(45))
    term_60_84 = db.Column(db.String(45))
    term_84_84 = db.Column(db.String(45))
    term_84_120 = db.Column(db.String(45))
    term_120_120 = db.Column(db.String(45))
    Start = db.Column(db.String(45))
    End = db.Column(db.String(45))
    RateType = db.Column(db.String(45))


class CMValidation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(45))
    calculated_date = db.Column(db.String(45))
    lai = db.Column(db.String(45))
    discrepancy = db.Column(db.String(500))
    unable_to_validate = db.Column(db.String(500))


class RateCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(45))
    calculated_date = db.Column(db.String(45))
    recommit = db.Column(db.String(45))
    brand = db.Column(db.String(90))
    bawag = db.Column(db.String(45))
    credit_officer_approval_date = db.Column(db.String(45))
    scooters = db.Column(db.String(45))
    bridge = db.Column(db.String(45))
    rate_type = db.Column(db.String(45))
    term = db.Column(db.String(45))
    embedded_fee = db.Column(db.String(45))
    investment_grade = db.Column(db.String(45))
    pricing_basis = db.Column(db.String(45))
    down_payment = db.Column(db.String(45))
    interest_rate = db.Column(db.String(45))
    spread_rate = db.Column(db.String(45))
    index_rate = db.Column(db.String(45))
    down_payment_penalty = db.Column(db.String(45))
    embedded_fee_penalty = db.Column(db.String(45))
    brand_penalty = db.Column(db.String(45))