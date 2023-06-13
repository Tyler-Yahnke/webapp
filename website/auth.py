from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, mail
from flask_login import login_user, login_required, logout_user, current_user
import secrets
from flask_mail import Message
from datetime import datetime



auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                session['logged_in'] = True
                session.permanent = True
                flash(f'Logged in successfully! Welcome {user.name}', category='success')
                login_user(user, remember=True)
                user.logged_in = True
                user.last_login_date = datetime.now()
                session['user_id'] = user.id
                db.session.commit()
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)



@auth.route('/logout')
@login_required
def logout():
    current_user.logged_in = False  # Update the logged_in attribute for the current user
    db.session.commit()
    session.pop('user_id', None)  # Remove the user's id from the session
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    button = request.form.get('secret_key')

    prev_data = {}

    if button == 'Email Secret Key':
        generate_reset_token()
        prev_data = user_email_reset
        return render_template("password_reset.html", user=current_user, prev_data=prev_data)
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
                if check_password_hash(user.secret_key, secret_key):
                    user.password = generate_password_hash(password1, method='scrypt')
                    user.last_password_update = datetime.now()
                    user.last_login_date = datetime.now()
                    user.logged_in = True
                    db.session.commit()
                    login_user(user, remember=True)
                    flash(f'Password Updated Successfully! Welcome {user.name}', category='success')
                    return redirect(url_for('views.home'))
                else:
                    flash('Secret Key is incorrect or expired', category='error')
            else:
                flash('User does not exist.', category='error')

    return render_template("password_reset.html", user=current_user, prev_data=prev_data)

def generate_reset_token():
    global user_email_reset
    email = request.form.get('email')

    user = User.query.filter_by(email=email).first()

    user_email_reset = {'email' : request.form.get('email')}

    if user:
        token = secrets.token_urlsafe(5)

        user.secret_key = generate_password_hash(token, method='scrypt')
        db.session.commit()
        email_token(token)
        flash('Please check email for Secret Key', category='success')
        return (user_email_reset)
    else:
        flash('Email is invalid or blank', category='error')


def email_token(token):
    email = request.form.get('email')

    user = User.query.filter_by(email=email).first()
    recipients = [user.email]


    msg = Message('Password Reset - Secuirty Key', sender='passwordreset@apcratecard.com', recipients=recipients)
    msg.body = f'Secret Key: "{token}"'

    mail.send(msg)
