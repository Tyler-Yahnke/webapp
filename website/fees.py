from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from . import db
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
    fees_table = pd.DataFrame(data)


    if request.method == 'GET':
        datapull()
        fees_table = dis_df
        return render_template("fees_tab.html", user=current_user, fees_table=fees_table)

    return render_template("fees_tab.html", user=current_user, fees_table=fees_table)


def datapull():
    global dis_df
    with open('creds.json', 'r') as file:
        cred = json.load(file)

    SCOPES = ('https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive')
    my_credentials = service_account.Credentials.from_service_account_info(cred, scopes=SCOPES)

    # Call the Sheets API
    api_failure = 0
    fail_string = ''

    gc = pygsheets.authorize(custom_credentials=my_credentials)
    rate_file = gc.open_by_key('13MUnNC1va0bEE_fGU5P0RFLHf-CEqWxOVk6YmEVwB1c')
    dis = rate_file.worksheet_by_title('Discounts')

    dis_df = dis.get_as_df()