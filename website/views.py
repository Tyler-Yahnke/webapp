from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from google.oauth2 import service_account
import datetime
from pandas.tseries.offsets import BDay
import pygsheets
import pandas as pd
import json
from . import db

views = Blueprint('views', __name__)


@views.route('/ratecard', methods=['GET', 'POST'])
#@login_required
def home():
    global recommit, userselection_scooters,userselection_bridge_loan,userselection_ratetype,userselection_term, userselection_fee,userselection_pricing, userselection_grade, userselection_dp, selected_date

    data = {'Month':[''],
                       'APC Grade':[''],
                       '60/60':[''],
                       '60/84':[''],
                       '84/84':[''],
                       '84/120':[''],
                       '120/120':['']
                       }
    rate_card_table = pd.DataFrame(data)

    results = {
        'index_rate_used': '',
        'rate_card_used': '',
        'final_rate': '',
        'spread_rate': '',
        'index_rate': '',
        'index_rate_date': '',
        'rate_type': ''
    }

    previous_data = {}

    button = request.form.get('clear')
    if button == 'Clear':
        results = {
            'index_rate_used': '',
            'rate_card_used': '',
            'final_rate': '',
            'spread_rate': '',
            'index_rate': '',
            'index_rate_date': '',
            'rate_type': '',
            'recommit': ''
        }

        return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table, previous_data=previous_data)

        return
    else:
        pass


    if request.method == 'POST':

        previous_data = {
        'recommit':request.form.get('recommit'),
        'userselection_scooters' : request.form.get('scooters_coffee'),
        'userselection_bridge_loan' : request.form.get('bridge_loan'),
        'userselection_ratetype' : request.form.get('rate_type'),
        'userselection_term' : request.form.get('term'),
        'userselection_fee' : request.form.get('embedded_fee'),
        'userselection_pricing' : request.form.get('pricing_basis'),
        'userselection_grade' : request.form.get('investment_grade'),
        'userselection_dp' : request.form.get('down_payment'),
        'selected_date' : request.form.get('selected_date')
                               }

        datapull()

        recommit = request.form.get('recommit')
        userselection_scooters = request.form.get('scooters_coffee')
        userselection_bridge_loan = request.form.get('bridge_loan')
        userselection_ratetype = request.form.get('rate_type')
        userselection_term = request.form.get('term')
        userselection_fee = request.form.get('embedded_fee')
        userselection_pricing = request.form.get('pricing_basis')
        userselection_grade = request.form.get('investment_grade')
        userselection_dp = request.form.get('down_payment')
        selected_date =request.form.get('selected_date')


        today = datetime.datetime.today()
        prime_process_date = datetime.datetime(2023, 2, 6)
        all_prime = datetime.datetime(2023, 5, 4)

        if recommit == 'Y':
            selected_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d")

            if (today - selected_date).days > 120:
                flash('Credit Officer Approval Date > 120 Days Ago, Current Month Rate Card Used', category='error')
                current_credit_policy()
                results = current_credit_policy_results
                rate_card_table = rate_card_df
                return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table,previous_data=previous_data)

            elif selected_date > prime_process_date and selected_date <= all_prime:
                previous_credit_policy()
                results = previous_credit_policy_results
                rate_card_table = rate_card_df
                return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table, previous_data=previous_data)

            else:
                current_credit_policy()
                results = current_credit_policy_results
                rate_card_table = rate_card_df
                return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table, previous_data=previous_data)

        else:
            print('test')
            current_credit_policy()
            results = current_credit_policy_results
            rate_card_table = rate_card_df
            return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table, previous_data=previous_data)



    return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table,previous_data=previous_data)

def missing():
    print('test missing')
    if userselection_term == 'Make Selection':
        return 'Missing Term'
    elif userselection_fee == 'Make Selection':
        return 'Missing Embedded Fee'
    elif userselection_pricing == 'Make Selection':
        return 'Missing Pricing Basis'
    elif userselection_grade == 'Make Selection':
        return 'Missing Grade'
    elif userselection_dp == 'Make Selection':
        return 'Missing Down Payment'
    return None

def datapull():
    print('test data pull')
    global spreads_df, ef_df, daily_swap_df, swap_spread_dic, down_payment_fee_dict, swap_spread_dic_define, api_failure, fail_string, prime_df, bridge_df

    with open('creds.json', 'r') as file:
        cred = json.load(file)

    SCOPES = ('https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive')
    my_credentials = service_account.Credentials.from_service_account_info(cred, scopes=SCOPES)

    # Call the Sheets API
    api_failure = 0
    fail_string = ''
    try:
        gc = pygsheets.authorize(custom_credentials=my_credentials)
        rate_file = gc.open_by_key('13MUnNC1va0bEE_fGU5P0RFLHf-CEqWxOVk6YmEVwB1c')

        try:
            spreads = rate_file.worksheet_by_title('Spreads')
            ef = rate_file.worksheet_by_title('EmbeddedFee')
            daily = rate_file.worksheet_by_title('Dailyswaps')
            prime = rate_file.worksheet_by_title('PrimeRate')
            hb = rate_file.worksheet_by_title('Historical Bridge')

            try:
                spreads_df = spreads.get_as_df()
                ef_df = ef.get_as_df()
                daily_swap_df = daily.get_as_df()
                prime_df = prime.get_as_df()
                bridge_df = hb.get_as_df()

                try:

                    # NEW ADDITION HERE
                    Prev_Biz_Day = datetime.datetime.today() - BDay(1)
                    formatted_dt = Prev_Biz_Day.strftime('%m/%d/%Y')


                    if daily_swap_df['Date'][0] != (formatted_dt):
                        swap_updates()
                        daily = rate_file.worksheet_by_title('Dailyswaps')
                        daily_swap_df = daily.get_as_df()

                    elif prime_df['Date'][0] != (formatted_dt):
                        swap_updates()
                        prime = rate_file.worksheet_by_title('PrimeRate')
                        prime_df = prime.get_as_df()
                    else:
                        pass

                    swap_3year = round(float(daily_swap_df.iloc[0]['3Year'][:-1]) / 100, 4)
                    swap_4year = round(float(daily_swap_df.iloc[0]['4Year'][:-1]) / 100, 4)
                    swap_5year = round(float(daily_swap_df.iloc[0]['5Year'][:-1]) / 100, 4)

                    swap_spread_dic = {'60/60': swap_3year,
                                       '60/84': swap_4year,
                                       '84/84': swap_4year,
                                       '84/120': swap_5year,
                                       '120/120': swap_5year}

                    swap_spread_dic_define = {'60/60': '3 Year',
                                              '60/84': '4 Year',
                                              '84/84': '4 Year',
                                              '84/120': '5 Year',
                                              '120/120': '5 Year'}

                    down_payment_fee_dict = {'Y': 0.0025, 'N': 0.00, 'N/A': 0.00}
                except:
                    fail_string = 'Failed pulling swap values'

            except:
                fail_string = "Failed creating Dataframes"
        except:
            fail_string = "Failed connecting to worksheets"

        fail_string = 'Success'

    except:
        fail_string = "Failed Connecting API"

    if fail_string != 'Success':
        api_failure = 1

def swap_updates():
    print('test swap updates')
    url = "https://ondemand.websol.barchart.com/getQuote.json?apikey=f662dbbcc2a45be5307136cb8e74da08&symbols=SWAEADY3.RT, SWAEADY5.RT, WSJPRIME.RT"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    fail = 0


    cred = {

        "type": "service_account",
        "project_id": "python-rate-sheet",
        "private_key_id": "dd51fec6c0a1a2eb4bc4d42d17dac22c1c7ba850",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCO7viLzuf1f9Ki\npGKuW2oXSlFG5K7sV79hz67dQz40X4SxpY+5eCGZxnC1WmC/q9DcCTjkAm6pG1oy\n5fQ7tjD8YUvHAQfO3SGt7IeveepQU8Kj9/GkW7y81cFxg3vZx54oZsjZMTjKmcH7\nBCz7leTON2Zxah8ZpYSzRrNeCgx8cGOh2VFGcbu6jDama5NRGjYBDRTZOz5UHgOo\nC43/kWeZu/cTJlPboiPP1VknLSEMJ0qXEUu82Gs0Eosi7lkohLhZh/Og0/Bh10e2\nJMDvZN4Faqrbs43+KyeDtuMgZjFNZuTiYKXXMuw2wb6GI98byBeZHASdOk2Z+8Jm\nhs3nOMFFAgMBAAECggEAGxROvewX+aS7IwmqUXaruZhgoCIEuu2f6lfGvRA3iYQc\nN2zStzR5hzD3mwAxqraSRhGwN9B3Jy4xr0luNV7d1n7XdK8vC8PM1O7mQPpDyG6q\nBlcb7oPb1NnZgZhDv12IiwZ4IF/pLsclH1mp7Qs3s1L/I1cT58+6PZ3ULymPtoZq\n5ROFhI1Nya5OrSyuIGCbdSUbByCiteWLORwddUuMMZG8oD16ObxqfV8x6I/cd9BI\nDR00h4brtS2Va4hwKXP3SYkduk/K3eqDMnrIIbioEjfWlTf2/Eq/modTaj4ynVIw\nL9qJIjiXqV58Pl29K7YgxWJ1Y/HV/dpxUR0DF4kmyQKBgQDIt88SLaIbRAjF5DmX\nN5lC3Z7UL0WowgXAzjC5M04F96fQf34T2Q7RCFbkPcm9nbsJ+mMLfw40G2BYNdzv\n1l4qqlHPakNF03aqZzC/uPMsbakXABIgJJhMcgs17kqWmDOwzUGJRfWClHAjtf7R\nTffszhBlxyosGaI6FsFATgCRjQKBgQC2TOaMo+ZIx4pwJ+cALPkEi5OmfKhrRu0U\nQYgEXvdgw8Z9ChiUENnCtZAMaePxIDvVXnHWOniuXC2sfkzK9IgCrUfQ6tbjUEh/\nzdPKsBxpOxmgVKscOkndUNs6ca0n59ZK88r5cGVLsoLj3G2o8jlKA49lSFriHLVx\n040I2P3UmQKBgQDH5ObAf9nVtafXDTedta1YvkYToxCIxNHd9nrntoSZxM7IAnCZ\na64p11hR7ocf5BoGEerZ5CtNEYad0ua5pJAbhYv8OSPOQo8HncUa6yKiuIOReGyU\nvl0+pMUtbKez2th/16rQ/29GIHad2f5wjGnA2GfUNMl3KgA6QbcsR4KhcQKBgBhb\nJeJcc4P9xO0/J4nKeGq3Cz8PIKFUlJBEQRv0ZDC1d2t1UdtWdQGiqGBANYgdumDD\ngYoRvdXt0txc832aNiHFbPboqVUtgMIyib1m0iTtFHtrVIEs+HltOB0S2wOd4e+Z\nquCwt5fpfbtb0/rigez1lM7/X8Ud+NAAZ7Nq6l7hAoGBAKZQIns6ZvStlqpAQ0Rz\ngIXMa+ppx3aZTWNmCiIMzjzTCZf6u4GOuXuewk00ys/M1pNn7iYtzgF0DSUnYyhi\nbArKCSHzeNRVWFH4EH3yTjXd2zOJ8QcCGkHJGq3DYzyitFlJLUBHD3S1xNwBDhCe\n1SHMDaTCFto+98f0iMTEto3G\n-----END PRIVATE KEY-----\n",
        "client_email": "python-connector@python-rate-sheet.iam.gserviceaccount.com",
        "client_id": "117453940853777693588",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/python-connector%40python-rate-sheet.iam.gserviceaccount.com"
    }

    SCOPES = ('https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive')
    my_credentials = service_account.Credentials.from_service_account_info(cred, scopes=SCOPES)

    gc = pygsheets.authorize(custom_credentials=my_credentials)
    rate_file = gc.open_by_key('13MUnNC1va0bEE_fGU5P0RFLHf-CEqWxOVk6YmEVwB1c')

    daily = rate_file.worksheet_by_title('Dailyswaps')

    for symbols in response.json()['results']:
        if symbols['symbol'] == 'SWAEADY3.RT':
            swap_3year = symbols['lastPrice']
            date_3year_str = symbols['tradeTimestamp']

        elif symbols['symbol'] == 'SWAEADY5.RT':
            swap_5year = symbols['lastPrice']
            date_5year_str = symbols['tradeTimestamp']

    swap_4year = round((swap_3year + swap_5year), 4) / 2

    if swap_3year < 0 or swap_5year < 0 or swap_3year == None or swap_5year == None:
        msg = '''
         ... From: DailyBarchartUpdate@gmail.com
         ... Subject: Error Notification
         ...
         ... The API returned with invalid swap rate values '''

        server.sendmail(sender, recip, msg)

    date_3year = dateutil.parser.parse(date_3year_str).strftime('%m/%d/%Y')
    date_5year = dateutil.parser.parse(date_5year_str).strftime('%m/%d/%Y')

    new_vals = [date_3year, "{:.2%}".format(swap_3year), "{:.2%}".format(swap_4year), "{:.2%}".format(swap_5year)]

    daily_swap_df = daily.get_as_df()
    most_recent_date = daily_swap_df['Date'].iloc[0]

    if most_recent_date != date_3year:
        daily.insert_rows(row=1, number=1, values=new_vals)

    elif most_recent_date == date_3year:
        pass

    # Pulling in prime rate and updating table
    daily_prime = rate_file.worksheet_by_title('PrimeRate')

    for symbols in response.json()['results']:
        if symbols['symbol'] == 'WSJPRIME.RT':
            prime_rate = symbols['lastPrice']
            prime_rate_str = symbols['tradeTimestamp']


    prime_rate_date = dateutil.parser.parse(prime_rate_str).strftime('%m/%d/%Y')

    new_prime_vals = [prime_rate_date, "{:.2%}".format(prime_rate)]

    daily_prime_df = daily_prime.get_as_df()
    most_recent_date = daily_prime_df['Date'].iloc[0]

    if most_recent_date != prime_rate_date:
        daily_prime.insert_rows(row=1, number=1, values=new_prime_vals)

def bridge_loan_func():
    print('test bridge')
    global bridgeresults
    bridgeresults = {
    'index_rate_used': 'Prime',
    'rate_card_used': 'Pro Forma',
    'final_rate': float(prime_df.Rate[0].rstrip("%")) + float(bridge_df.Rate[0].rstrip("%")),
    'spread_rate': bridge_df.Rate[0],
    'index_rate': prime_df.Rate[0],
    'index_rate_date': prime_df.Date[0],
    'rate_type': 'Fixed'}

def scooters_func():

    print('test scooters')
    global scootersresults
    scooters_date = datetime.datetime(2023, 4, 6)

    if recommit == 'Y' and datetime.datetime.strptime(selected_date, "%Y-%m-%d") < scooters_date:
            temp_base_spread = 0.75 / 100
            temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].str.rstrip(
                "%").astype(float) / 100
            # 2/14/2023 Adding Logic Here
            base_spread = round(temp_base_spread + temp_embedded.iloc[0], 4)
            final_spread = round(base_spread + float(prime_df.Rate[0].rstrip("%")) / 100, 4)

            loan_buyer_spread =f"{100 * temp_base_spread: .2f}%"
            loan_buyer_fee = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].iloc[0]

            scootersresults = {
                'index_rate_used': 'Prime',
                'rate_card_used': 'Scooters Pricing',
                'final_rate': f"{100 * final_spread: .2f}%",
                'spread_rate': f"{100 * base_spread: .2f}%",
                'index_rate': prime_df.Rate[0],
                'index_rate_date': prime_df.Date[0],
                'rate_type': userselection_ratetype,
                'loan_buyer_spread': loan_buyer_spread,
                'loan_buyer_fee' : loan_buyer_fee

            }

    else:
        temp_base_spread = 1.5 / 100
        temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].str.rstrip(
            "%").astype(float) / 100
        # 2/14/2023 Adding Logic Here
        base_spread = round(temp_base_spread + temp_embedded.iloc[0], 4)
        final_spread = round(base_spread + float(prime_df.Rate[0].rstrip("%")) / 100, 4)

        loan_buyer_spread = f"{100 * temp_base_spread: .2f}%"
        loan_buyer_fee = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].iloc[0]

        scootersresults = {
            'index_rate_used': 'Prime',
            'rate_card_used': 'Scooters Pricing',
            'final_rate': f"{100 * final_spread: .2f}%",
            'spread_rate': f"{100 * base_spread: .2f}%",
            'index_rate': prime_df.Rate[0],
            'index_rate_date': prime_df.Date[0],
            'rate_type': 'Fixed',
            'loan_buyer_spread': loan_buyer_spread,
            'loan_buyer_fee': loan_buyer_fee
        }

def current_credit_policy():

    global current_credit_policy_results, rate_card_df, swapbaserate, baserate, swaprate, swapusedlabel, ratecardresults, Swapratedateresults, missingselection, ratetyperesult, base_field, true_base, dp_field, dp_base, ef_field, ef_base, buyer_header

    current_credit_policy_results = {}


    if recommit =="Y":
        temp_base_spread = spreads_df.loc[
                               (pd.to_datetime(spreads_df['Start'],
                                               format="%m/%d/%Y").dt.date <= datetime.datetime.strptime(
                                   selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date()) &
                               (pd.to_datetime(spreads_df['End'],
                                               format="%m/%d/%Y").dt.date >= datetime.datetime.strptime(
                                   selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date())
                               &
                               (spreads_df['APC Grade'] == userselection_grade) &
                               (spreads_df['PricingBasis'] == userselection_pricing) &
                               (spreads_df['RateType'] == userselection_ratetype)
                               ][userselection_term].str.rstrip("%").astype(float) / 100
        temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].str.rstrip(
            "%").astype(float) / 100
        temp_prime = prime_df['Rate'][0].rstrip("%")
        base_spread = round(temp_base_spread.iloc[0] + temp_embedded.iloc[0] + down_payment_fee_dict[userselection_dp],
                            4)
        final_spread = round(base_spread + (float(temp_prime) / 100), 4)
        loan_buyer_spread = f"{100 * temp_base_spread.iloc[0]: .2f}%"
        loan_buyer_fee = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].iloc[0]
        if userselection_dp == 'Y':
            loan_buyer_dp = '0.25%'
        else:
            loan_buyer_dp = '0.00%'

        # creating logic for table
        temp_table= spreads_df.loc[
            (pd.to_datetime(spreads_df['Start'],
                            format="%m/%d/%Y").dt.date <= datetime.datetime.strptime(
                selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date()) &
            (pd.to_datetime(spreads_df['End'],
                            format="%m/%d/%Y").dt.date >= datetime.datetime.strptime(
                selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date())
            &
            (spreads_df['PricingBasis'] == userselection_pricing) &
            (spreads_df['RateType'] == userselection_ratetype)]

        term_vals = ['60/60', '60/84', '84/84', '84/120', '120/120']
        transformed_values = list()
        for row in temp_table[term_vals].values:
            new_row = list()
            for i, column in enumerate(row):
                temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][term_vals[i]].str.rstrip(
                    "%").astype(float) / 100
                temp_val = round(float(column.rstrip("%")) / 100 + temp_embedded.iloc[0] + down_payment_fee_dict[
                    userselection_dp], 4)
                temp_final = round(100 * (temp_val + (float(temp_prime) / 100)), 2)
                new_row.append("{:.2f}".format(temp_final) + '%')

            transformed_values.append(new_row)

        month_series = temp_table['Month'].reset_index(drop=True)
        grade_series = temp_table['APC Grade'].reset_index(drop=True)
        rate_card_df = pd.concat(
            [month_series, grade_series, pd.DataFrame(transformed_values, columns=term_vals)],
            axis=1)

        current_credit_policy_results = {
            'index_rate_used': 'Prime',
            'rate_card_used': userselection_pricing,
            'final_rate': f"{100 * final_spread: .2f}%",
            'spread_rate': f"{100 * base_spread: .2f}%",
            'index_rate': prime_df.Rate[0],
            'index_rate_date': prime_df.Date[0],
            'rate_type': userselection_ratetype,
            'loan_buyer_spread': loan_buyer_spread,
            'loan_buyer_fee': loan_buyer_fee,
            'loan_buyer_dp': loan_buyer_dp

        }
        return (current_credit_policy_results, rate_card_df)
        print('current_credit_policy_recommit')
    else:
        today = datetime.datetime.today().strftime('%m/%d/%Y')

        temp_base_spread = spreads_df.loc[(spreads_df['Start'] <= today) & (spreads_df['End'] >= today) & (
                spreads_df['APC Grade'] == userselection_grade) & (
                                                  spreads_df['PricingBasis'] == userselection_pricing) & (
                                                  spreads_df['RateType'] == userselection_ratetype)][
                               userselection_term].str.rstrip("%").astype(float) / 100
        temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].str.rstrip("%").astype(float) / 100
        temp_prime = prime_df['Rate'][0].rstrip("%")
        base_spread = round(temp_base_spread.iloc[0] + temp_embedded.iloc[0] + down_payment_fee_dict[userselection_dp], 4)
        final_spread = round(base_spread + (float(temp_prime) / 100), 4)
        loan_buyer_spread = f"{100 * temp_base_spread.iloc[0]: .2f}%"
        loan_buyer_fee = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].iloc[0]
        if userselection_dp == 'Y':
            loan_buyer_dp = '0.25%'
        else:
            loan_buyer_dp = '0.00%'

        # creating logic for table
        temp_table = spreads_df.loc[(spreads_df['Start'] <= today) & (spreads_df['End'] >= today) & (
                spreads_df['PricingBasis'] == userselection_pricing) & (
                                            spreads_df['RateType'] == userselection_ratetype)]

        term_vals = ['60/60', '60/84', '84/84', '84/120', '120/120']
        transformed_values = list()
        for row in temp_table[term_vals].values:
            new_row = list()
            for i, column in enumerate(row):
                temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][term_vals[i]].str.rstrip(
                    "%").astype(float) / 100
                temp_val = round(float(column.rstrip("%")) / 100 + temp_embedded.iloc[0] + down_payment_fee_dict[
                    userselection_dp], 4)
                temp_final = round(100 * (temp_val + (float(temp_prime) / 100)), 2)
                new_row.append("{:.2f}".format(temp_final) + '%')

            transformed_values.append(new_row)

        month_series = temp_table['Month'].reset_index(drop=True)
        grade_series = temp_table['APC Grade'].reset_index(drop=True)
        rate_card_df = pd.concat([month_series, grade_series, pd.DataFrame(transformed_values, columns=term_vals)],
                            axis=1)

        current_credit_policy_results = {
            'index_rate_used': 'Prime',
            'rate_card_used': userselection_pricing,
            'final_rate': f"{100 * final_spread: .2f}%",
            'spread_rate': f"{100 * base_spread: .2f}%",
            'index_rate': prime_df.Rate[0],
            'index_rate_date': prime_df.Date[0],
            'rate_type': userselection_ratetype,
            'loan_buyer_spread': loan_buyer_spread,
            'loan_buyer_fee': loan_buyer_fee,
            'loan_buyer_dp': loan_buyer_dp

        }
        print('current_credit_policy_new')
        return(current_credit_policy_results, rate_card_df)
    return

def previous_credit_policy():
    global previous_credit_policy_results, rate_card_df, swapbaserate, baserate, swaprate, swapusedlabel, ratecardresults, Swapratedateresults, missingselection, base_field, true_base, dp_field, dp_base, ef_field, ef_base, buyer_header


    if userselection_pricing== 'Pro Forma':
        temp_base_spread = spreads_df.loc[
            (pd.to_datetime(spreads_df['Start'], format="%m/%d/%Y").dt.date <= datetime.datetime.strptime(
                selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date()) &
            (pd.to_datetime(spreads_df['End'], format="%m/%d/%Y").dt.date >= datetime.datetime.strptime(
                selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date())
            &
                               (spreads_df['APC Grade'] == userselection_grade) &
                               (spreads_df['PricingBasis'] == userselection_pricing) &
                               (spreads_df['RateType'] == userselection_ratetype)
                               ][userselection_term].str.rstrip("%").astype(float) / 100

        temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].str.rstrip(
            "%").astype(
            float) / 100

        temp_prime = prime_df['Rate'][0].rstrip("%")

        base_spread = round(
            temp_base_spread.iloc[0] + temp_embedded.iloc[0] + down_payment_fee_dict[userselection_dp], 4)

        final_spread = round(base_spread + (float(temp_prime) / 100), 4)
        loan_buyer_spread = f"{100 * temp_base_spread.iloc[0]: .2f}%"
        loan_buyer_fee = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].iloc[0]
        if userselection_dp == 'Y':
            loan_buyer_dp = '0.25%'
        else:
            loan_buyer_dp = '0.00%'

        # creating logic for table
        temp_table= spreads_df.loc[
            (pd.to_datetime(spreads_df['Start'],
                            format="%m/%d/%Y").dt.date <= datetime.datetime.strptime(
                selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date()) &
            (pd.to_datetime(spreads_df['End'],
                            format="%m/%d/%Y").dt.date >= datetime.datetime.strptime(
                selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date())
            &
            (spreads_df['PricingBasis'] == userselection_pricing) &
            (spreads_df['RateType'] == userselection_ratetype)]

        term_vals = ['60/60', '60/84', '84/84', '84/120', '120/120']
        transformed_values = list()
        for row in temp_table[term_vals].values:
            new_row = list()
            for i, column in enumerate(row):
                temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][term_vals[i]].str.rstrip(
                    "%").astype(float) / 100
                temp_val = round(float(column.rstrip("%")) / 100 + temp_embedded.iloc[0] + down_payment_fee_dict[
                    userselection_dp], 4)
                temp_final = round(100 * (temp_val + (float(temp_prime) / 100)), 2)
                new_row.append("{:.2f}".format(temp_final) + '%')

            transformed_values.append(new_row)

        month_series = temp_table['Month'].reset_index(drop=True)
        grade_series = temp_table['APC Grade'].reset_index(drop=True)
        rate_card_df = pd.concat(
            [month_series, grade_series, pd.DataFrame(transformed_values, columns=term_vals)],
            axis=1)

        previous_credit_policy_results = {
            'index_rate_used': 'Prime',
            'rate_card_used': userselection_pricing,
            'final_rate': f"{100 * final_spread: .2f}%",
            'spread_rate': f"{100 * base_spread: .2f}%",
            'index_rate': prime_df.Rate[0],
            'index_rate_date': prime_df.Date[0],
            'rate_type': userselection_ratetype,
            'loan_buyer_spread': loan_buyer_spread,
            'loan_buyer_fee': loan_buyer_fee,
            'loan_buyer_dp': loan_buyer_dp

        }
        print('old_credit_policy_pro_forma')
        return(previous_credit_policy_results, rate_card_df)


    else:
        print('old_credit_policy_cash_flow')
        previous_credit_policy_results = {}

        temp_base_spread = spreads_df.loc[
                               (pd.to_datetime(spreads_df['Start'],
                                               format="%m/%d/%Y").dt.date <= datetime.datetime.strptime(
                                   selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date()) &
                               (pd.to_datetime(spreads_df['End'],
                                               format="%m/%d/%Y").dt.date >= datetime.datetime.strptime(
                                   selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date())
                               &
                               (spreads_df['APC Grade'] == userselection_grade) &
                               (spreads_df['PricingBasis'] == userselection_pricing) &
                               (spreads_df['RateType'] == userselection_ratetype)
                               ][userselection_term].str.rstrip("%").astype(float) / 100

    temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].str.rstrip(
        "%").astype(
        float) / 100

    base_spread = round(
        temp_base_spread.iloc[0] + temp_embedded.iloc[0] + down_payment_fee_dict[userselection_dp], 4)
    final_spread = round(base_spread + swap_spread_dic[userselection_term], 4)
    loan_buyer_spread = f"{100 * temp_base_spread.iloc[0]: .2f}%"
    loan_buyer_fee = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][userselection_term].iloc[0]
    if userselection_dp == 'Y':
        loan_buyer_dp = '0.25%'
    else:
        loan_buyer_dp = '0.00%'

    # Creating Logic so that table that is displayed has the final rate for each cell in matrix
    temp_table = spreads_df.loc[
                           (pd.to_datetime(spreads_df['Start'],
                                           format="%m/%d/%Y").dt.date <= datetime.datetime.strptime(
                               selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date()) &
                           (pd.to_datetime(spreads_df['End'],
                                           format="%m/%d/%Y").dt.date >= datetime.datetime.strptime(
                               selected_date.strftime("%m/%d/%Y"), "%m/%d/%Y").date())
                           &
                           (spreads_df['PricingBasis'] == userselection_pricing) &
                           (spreads_df['RateType'] == userselection_ratetype)
                           ]
    term_vals = ['60/60', '60/84', '84/84', '84/120', '120/120']
    transformed_values = list()
    for row in temp_table[term_vals].values:
        new_row = list()
        for i, column in enumerate(row):
            temp_embedded = ef_df.loc[ef_df['Fee Buy-Down'] == userselection_fee][term_vals[i]].str.rstrip(
                "%").astype(float) / 100
            temp_val = round(float(column.rstrip("%")) / 100 + temp_embedded.iloc[0] + down_payment_fee_dict[
                userselection_dp], 4)
            temp_final = round(100 * (temp_val + swap_spread_dic[term_vals[i]]), 2)
            new_row.append("{:.2f}".format(temp_final) + '%')

        transformed_values.append(new_row)

    month_series = temp_table['Month'].reset_index(drop=True)
    grade_series = temp_table['APC Grade'].reset_index(drop=True)
    rate_card_df = pd.concat([month_series, grade_series, pd.DataFrame(transformed_values, columns=term_vals)],
                        axis=1)

    previous_credit_policy_results = {
        'index_rate_used': 'Prime',
        'rate_card_used': userselection_pricing,
        'final_rate': f"{100 * final_spread: .2f}%",
        'spread_rate': f"{100 * base_spread: .2f}%",
        'index_rate': prime_df.Rate[0],
        'index_rate_date': prime_df.Date[0],
        'rate_type': userselection_ratetype,
        'loan_buyer_spread': loan_buyer_spread,
        'loan_buyer_fee': loan_buyer_fee,
        'loan_buyer_dp': loan_buyer_dp

    }
    return (previous_credit_policy_results, rate_card_df)
    return

