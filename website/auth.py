from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, mail
from flask_login import login_user, login_required, logout_user, current_user
import secrets
from flask_mail import Message



auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)



@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    button = request.form.get('secret_key')
    if button == 'Email Secret Key':
        generate_reset_token()
        return render_template("password_reset.html", user=current_user)
    else:
        pass

    if request.method == 'POST':
        email = request.form.get('email')
        secret_key = request.form.get('secret_key')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            user = User.query.filter_by(email=email).first()

            if user:
                check_password_hash(user.secret_key, secret_key)
                flash('Secret Key is incorrect or expired', category='error')
            elif user:
                user.password = generate_password_hash(password1, method='scrypt')
                db.session.commit()
                login_user(user, remember=True)
                flash('Password Updated Successfully!', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('User does not exist.', category='error')

    return render_template("password_reset.html", user=current_user)

def generate_reset_token():
    email = request.form.get('email')

    user = User.query.filter_by(email=email).first()

    if user:
        token = secrets.token_urlsafe(5)
        print(token)

        user.secret_key = generate_password_hash(token, method='scrypt')
        db.session.commit()
        email_token(token)
        flash('Please check email for Secret Key', category='success')
    else:
        flash('Email is invalid or blank', category='error')


def email_token(token):
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    recipients = [user.email]


    msg = Message('Password Reset - Secuirty Key', sender='passwordreset@apcratecard.com', recipients=recipients)
    msg.body = 'Copy your Security Key to reset password: "{token}"'
    print(msg.body)
    mail.send(msg)
