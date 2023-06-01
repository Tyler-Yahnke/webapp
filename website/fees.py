from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from . import db


fees = Blueprint('fees', __name__)


@fees.route('/fee)', methods=['GET', 'POST'])
@login_required

def fees_func():
        print('i came here')
        if request.method == 'GET':
                return render_template("fees_tab.html",user=current_user)
        else:
                return render_template("fees_tab.html",user=current_user)

