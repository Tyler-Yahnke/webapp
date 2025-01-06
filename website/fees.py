from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from . import db
from .models import Discounts


fees = Blueprint('fees', __name__)

@fees.route('/', methods=['GET', 'POST'])
@login_required
def fees_func():

    if request.method == 'GET':
        discounts = Discounts.query.all()
        discount_table = discounts
        return render_template("fees_tab.html", user=current_user, discount_table=discount_table)

    return render_template("fees_tab.html", user=current_user, discount_table=discount_table)


