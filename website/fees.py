from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from . import db
from .models import Discounts
import pygsheets
import pandas as pd
import json
from google.oauth2 import service_account

fees = Blueprint('fees', __name__)

@fees.route('/fees', methods=['GET', 'POST'])
@login_required
def fees_func():
    data = {'Brand':[''],
                       '0 - 750K':[''],
                       '751K - 1.5M':[''],
                       '1.5M+':['']
                       }
    discount_table = pd.DataFrame(data)


    if request.method == 'GET':
        discounts = Discounts.query.all()
        discount_table = discounts
        return render_template("fees_tab.html", user=current_user, discount_table=discount_table)

    return render_template("fees_tab.html", user=current_user, discount_table=discount_table)



