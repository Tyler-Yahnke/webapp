from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
import datetime
from datetime import date, timedelta
from pandas.tseries.offsets import BDay
import requests
from .models import SwapRate, PrimeRate, Spreads, EmbeddedFee, RateCard
from sqlalchemy import desc, and_
import pandas as pd
from . import db


views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    global today_date_time, recommit, today, rate_card_index, prime_rate, swap_rate, userselection_brand, userselection_term_missing, userselection_bawag_loan, userselection_bridge_loan,userselection_ratetype,userselection_term, userselection_fee,userselection_pricing, userselection_grade, userselection_dp, selected_date, down_payment_fee_dict



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
        print('post start')
        previous_data = {
        'recommit':request.form.get('recommit'),
        'userselection_brand' : request.form.get('brand'),
        'userselection_bawag_loan' : request.form.get('bawag_loan'),
        'userselection_bridge_loan' : request.form.get('bridge_loan'),
        'userselection_ratetype' : request.form.get('rate_type'),
        'userselection_term' : request.form.get('term'),
        'userselection_fee' : request.form.get('embedded_fee'),
        'userselection_pricing' : request.form.get('pricing_basis'),
        'userselection_grade' : request.form.get('investment_grade'),
        'userselection_dp' : request.form.get('down_payment'),
        'selected_date' : request.form.get('selected_date')
                               }
        print('previous data')

        recommit = request.form.get('recommit')
        userselection_brand = request.form.get('brand')
        userselection_bawag_loan = request.form.get('bawag_loan')
        userselection_bridge_loan = request.form.get('bridge_loan')
        userselection_ratetype = request.form.get('rate_type')
        userselection_fee = request.form.get('embedded_fee')
        userselection_pricing = request.form.get('pricing_basis')
        userselection_grade = request.form.get('investment_grade')
        userselection_dp = request.form.get('down_payment')
        selected_date =request.form.get('selected_date')
        userselection_term_missing = request.form.get('term')


        if selected_date == '' and recommit == 'Y':
            flash('Date Selection Required or Update Recommit to N', category='error')
            return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table,previous_data=previous_data)
        else:
            pass

        missing_selection = missing()
        if missing_selection == 'Missing':
            return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table,previous_data=previous_data)
        else:
            pass

        term_dict = {
            '60/60': 'term_60_60',
            '60/84': 'term_60_84',
            '84/84': 'term_84_84',
            '84/120': 'term_84_120',
            '120/120': 'term_120_120'
        }
        userselection_term = term_dict.get(request.form.get('term'))

        down_payment_fee_dict = {'Y': 0.25, 'N': 0.00, 'NA': 0.00, None: 0.00}


        prime_rate = PrimeRate.query.order_by(desc(PrimeRate.Date)).first()
        swap_rate = SwapRate.query.order_by(desc(SwapRate.Date)).first().three_Year
        today_date_time = datetime.datetime.today()
        today = today_date_time.date()

        if recommit=='Y':
            selected_date = datetime.datetime.strptime(selected_date, "%Y-%m-%d")
        else:
            # Handle the case when no date is selected. Set selected_date to today's date
            selected_date = datetime.datetime.today().date()

        try:
            # Pulling most recent spread to ensure it has been updated
            selected_spread = Spreads.query.filter(
                and_(
                    Spreads.Start <= today,
                    Spreads.End >= today,
                    Spreads.APCGrade == userselection_grade,
                    Spreads.PricingBasis == userselection_pricing,
                    Spreads.RateType == userselection_ratetype
                )
            ).order_by(Spreads.End.desc()).first()
            if selected_spread == None:
                flash('Spread Rates have not been updated. Please notify Tyler Yahnke', category='error')
                return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table,
                                       previous_data=previous_data)
            else:
                pass

        except:
            flash('Spread Rates have not been updated. Please notify Tyler Yahnke', category='error')
            return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table,
                                   previous_data=previous_data)

        if recommit == 'Y' and selected_date > today_date_time:
            flash('Can\'t select a future date', category='error')
            return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table,previous_data=previous_data)

        if userselection_bridge_loan == 'Y':
            bridge_loan_func()
            results = bridge_results
            log_selections()
            return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table, previous_data=previous_data)


        if recommit == 'Y':

            if (today_date_time - selected_date).days > 120:
                flash('Credit Officer Approval Date > 120 Days Ago, Current Month Rate Card Used', category='error')
                current_credit_policy()
                rate_card_index = SwapRate.query.order_by(desc(SwapRate.Date)).first().three_Year
                rate_card()
                results = current_credit_policy_results
                rate_card_table = rate_card_df
                log_selections()
                return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table,previous_data=previous_data)


            else:
                current_credit_policy()
                rate_card_index = SwapRate.query.order_by(desc(SwapRate.Date)).first().three_Year
                rate_card()
                results = current_credit_policy_results
                rate_card_table = rate_card_df
                log_selections()
                return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table, previous_data=previous_data)

        else:
            current_credit_policy()
            rate_card_index = SwapRate.query.order_by(desc(SwapRate.Date)).first().three_Year
            rate_card()
            results = current_credit_policy_results
            rate_card_table = rate_card_df
            log_selections()
            return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table, previous_data=previous_data)


    return render_template("home.html", user=current_user, results=results, rate_card_table=rate_card_table,previous_data=previous_data)

def missing():
    if userselection_term_missing == 'Make Selection':
        flash('Missing term', category='error')
        return 'Missing'
    elif userselection_brand == 'Make Selection':
        flash('Missing brand', category='error')
        return 'Missing'
    elif userselection_brand == 'Urban Air Adventure Park' and userselection_bawag_loan is None:
        flash('Missing Bawag Loan', category='error')
        return 'Missing'
    elif userselection_fee == 'Make Selection':
        flash('Missing fee', category='error')
        return 'Missing'
    elif userselection_pricing == 'Make Selection':
        flash('Missing pricing', category='error')
        return 'Missing'
    elif userselection_grade == 'Make Selection':
        flash('Missing grade', category='error')
        return 'Missing'
    elif userselection_dp == 'Make Selection':
        flash('Missing down payment', category='error')
        return 'Missing'
    return None

def log_selections():
    print('logging results')

    if userselection_bridge_loan=='Y':
        rate_card = RateCard(
            user=current_user.name,
            calculated_date=datetime.datetime.today(),
            recommit=recommit,
            credit_officer_approval_date=selected_date,
            scooters='N',
            brand=userselection_brand,
            bawag=userselection_bawag_loan,
            bridge=userselection_bridge_loan,
            rate_type=userselection_ratetype ,
            term=userselection_term,
            embedded_fee=userselection_fee ,
            investment_grade = userselection_grade,
            pricing_basis=userselection_pricing ,
            down_payment = userselection_dp,
            interest_rate = bridge_results['final_rate'].strip('%'),
            spread_rate = bridge_results['spread_rate'].strip('%'),
            index_rate = bridge_results['index_rate'].strip('%'),
            down_payment_penalty = '0.00',
            brand_penalty=bridge_results['loan_buyer_brand_fee'].strip('%'),
            embedded_fee_penalty = '0.00'
        )
        db.session.add(rate_card)
        db.session.commit()
        print('logged_successfully')

    else:
        if userselection_brand =='Scooters':
            scooters = 'Y'
        else:
            scooters = 'N'

        rate_card = RateCard(
            user=current_user.name,
            calculated_date=datetime.datetime.today(),
            recommit=recommit,
            credit_officer_approval_date=selected_date,
            scooters=scooters,
            brand=userselection_brand,
            bawag=userselection_bawag_loan,
            bridge=userselection_bridge_loan,
            rate_type=userselection_ratetype ,
            term=userselection_term,
            embedded_fee=userselection_fee ,
            investment_grade = userselection_grade,
            pricing_basis=userselection_pricing ,
            down_payment = userselection_dp,
            interest_rate = current_credit_policy_results['final_rate'].strip('%'),
            spread_rate = current_credit_policy_results['spread_rate'].strip('%'),
            index_rate = current_credit_policy_results['index_rate'].strip('%'),
            down_payment_penalty = current_credit_policy_results['loan_buyer_dp'].strip('%'),
            brand_penalty= current_credit_policy_results['loan_buyer_brand_fee'].strip('%'),
            embedded_fee_penalty = current_credit_policy_results['loan_buyer_fee'].strip('%')
        )
        db.session.add(rate_card)
        db.session.commit()
        print('logged_successfully')

def bridge_loan_func():
    global bridge_results
    print('bridge_process')
    bridge_results = {
    'index_rate_used': 'Prime',
    'rate_card_used': 'Pro Forma',
    'final_rate': f"{float(prime_rate.Rate) + float(3.5)}%",
    'spread_rate': '3.50%',
    'index_rate': f"{prime_rate.Rate}%",
    'index_rate_date': prime_rate.Date.strftime('%m/%d/%Y'),
    'loan_buyer_brand_fee': "0.00%",
    'rate_type': 'Fixed'}
    return(bridge_results)


def current_credit_policy():
    print('new process')
    global current_credit_policy_results

    current_credit_policy_results = {}

    if recommit =="Y" and (today_date_time - selected_date).days < 120:
        # Selecting rate card
        selected_spread = Spreads.query.filter(
            and_(
                Spreads.Start <= selected_date,
                Spreads.End >= selected_date,
                Spreads.APCGrade == userselection_grade,
                Spreads.PricingBasis == userselection_pricing,
                Spreads.RateType == userselection_ratetype
            )
        ).first()
        temp_base_spread = getattr(selected_spread, userselection_term)

    else:
        # Selecting rate card
        selected_spread = Spreads.query.filter(
            and_(Spreads.Start <= today,Spreads.End >= today,
                Spreads.APCGrade == userselection_grade,
                Spreads.PricingBasis == userselection_pricing,
                Spreads.RateType == userselection_ratetype
            )
        ).first()
        temp_base_spread = getattr(selected_spread, userselection_term)

        rate_change_message()


    # selecting the embedded fee
    selected_fee = db.session.query(EmbeddedFee).filter(EmbeddedFee.Fee_Buy_Down == userselection_fee).first()
    temp_embedded = getattr(selected_fee, userselection_term)

    # base spread
    base_spread = round(
        float(temp_base_spread) + float(temp_embedded) + float(down_payment_fee_dict[userselection_dp]), 4)

    if userselection_brand=='Casago' and userselection_pricing=='Cash Flow':
        print(base_spread)
        base_spread = base_spread + 1
        print(base_spread)
    else:
        pass

    # final interest rate
    final_spread = round(base_spread + float(swap_rate), 4)

    #return results
    current_credit_policy_results = {
        'index_rate_used': "Swap - 3 Year",
        'rate_card_used': userselection_pricing,
        'final_rate': f"{final_spread: .2f}%",
        'spread_rate': f"{base_spread: .2f}%",
        'index_rate': f"{swap_rate}%",
        'index_rate_date': SwapRate.query.order_by(desc(SwapRate.Date)).first().Date.strftime('%m/%d/%Y'),
        'rate_type': 'Fixed',
        'loan_buyer_spread': f"{temp_base_spread: .2f}%",
        'loan_buyer_fee': f"{temp_embedded}%",
        'loan_buyer_dp': f"{down_payment_fee_dict[userselection_dp]: .2f}%",
        'loan_buyer_brand_fee': "0.00%"
    }
    return (current_credit_policy_results)

def rate_card():
    global rate_card_df

    if recommit =="Y" and (today_date_time - selected_date).days < 120:
        # selecting rate card for the table
        temp_table = db.session.query(Spreads).filter(
            and_(
                Spreads.Start <= selected_date,
                Spreads.End >= selected_date,
                Spreads.PricingBasis == userselection_pricing,
                Spreads.RateType == userselection_ratetype
            )
        ).all()

    else:
        # selecting rate card for the table
        temp_table = db.session.query(Spreads).filter(
            and_(
                Spreads.Start <= today,
                Spreads.End >= today,
                Spreads.PricingBasis == userselection_pricing,
                Spreads.RateType == userselection_ratetype
            )
        ).all()

    # table creation
    nice_term_vals = ['60/60', '60/84', '84/84', '84/120', '120/120']
    # Mapping between attribute names and nice terms
    term_map = {'term_60_60': '60/60', 'term_60_84': '60/84', 'term_84_84': '84/84', 'term_84_120': '84/120',
                'term_120_120': '120/120'}
    transformed_values = list()
    for spread_object in temp_table:
        new_row = list()
        for attr, term_val in term_map.items():
            column = getattr(spread_object, attr)
            selected_fee_table = EmbeddedFee.query.filter_by(Fee_Buy_Down=userselection_fee).first()
            temp_embedded_table = getattr(selected_fee_table, attr)

            temp_val = round(
                float(column) + float(temp_embedded_table) + float(down_payment_fee_dict[userselection_dp]), 4)

            temp_final = round((temp_val + float(rate_card_index)), 2)

            new_row.append("{:.2f}".format(temp_final) + '%')

        transformed_values.append(new_row)

    month_list = [spread_object.Month for spread_object in temp_table]
    grade_list = [spread_object.APCGrade for spread_object in temp_table]
    rate_card_df = pd.DataFrame(transformed_values, columns=nice_term_vals)
    rate_card_df.insert(0, 'Month', month_list)
    rate_card_df.insert(1, 'APC Grade', grade_list)

    return rate_card_df

def rate_change_message():
    #selecting current pro forma rate
    selected_spread_pro_forma = Spreads.query.filter(
        and_(Spreads.Start <= today, Spreads.End >= today,
             Spreads.APCGrade == userselection_grade,
             Spreads.PricingBasis == 'Pro Forma',
             Spreads.RateType == userselection_ratetype
             )
    ).first()
    temp_base_spread_pro_forma = getattr(selected_spread_pro_forma, userselection_term)




    #selecting current cash flow rate
    selected_spread_cash_flow = Spreads.query.filter(
        and_(Spreads.Start <= today, Spreads.End >= today,
             Spreads.APCGrade == userselection_grade,
             Spreads.PricingBasis == 'Cash Flow',
             Spreads.RateType == userselection_ratetype
             )
    ).first()
    temp_base_spread_cash_flow = getattr(selected_spread_cash_flow, userselection_term)

    # Displaying change in rate from previous month rate card for users
    spread_end_date = (selected_spread_pro_forma.End).strftime('%m-%d-%Y')
    spread_start_date = (selected_spread_pro_forma.Start).strftime('%m-%d-%Y')

    previous_spread_start_date = (selected_spread_pro_forma.Start - timedelta(days=1))

    # Prior month Pro Forma Spread Rate
    selected_spread_previous_month = Spreads.query.filter(
        and_(Spreads.Start <= previous_spread_start_date, Spreads.End >= previous_spread_start_date,
             Spreads.APCGrade == userselection_grade,
             Spreads.PricingBasis == 'Pro Forma',
             Spreads.RateType == userselection_ratetype
             )
    ).first()
    previous_month_pro_forma = getattr(selected_spread_previous_month, userselection_term)

    #Prior month Cash Flow Spread Rate
    selected_spread_previous_month = Spreads.query.filter(
        and_(Spreads.Start <= previous_spread_start_date, Spreads.End >= previous_spread_start_date,
             Spreads.APCGrade == userselection_grade,
             Spreads.PricingBasis == 'Cash Flow',
             Spreads.RateType == userselection_ratetype
             )
    ).first()
    previous_month_cash_flow = getattr(selected_spread_previous_month, userselection_term)

    pro_forma_rate_change = f"{(temp_base_spread_pro_forma - previous_month_pro_forma)}%"
    cash_flow_rate_change = f"{(temp_base_spread_cash_flow - previous_month_cash_flow)}%"

    if temp_base_spread_pro_forma - previous_month_pro_forma > 0:
        pro_forma_message = f"Pro Forma Rates have increased {pro_forma_rate_change}"
    elif temp_base_spread_pro_forma - previous_month_pro_forma < 0:
        pro_forma_message = f"Pro Forma Rates have decreased {pro_forma_rate_change}"
    else:
        pro_forma_message = "Pro Forma Rates are unchanged from previous month"

    if temp_base_spread_cash_flow - previous_month_cash_flow > 0:
        cash_flow_message = f"Cash Flow Rates have increased {cash_flow_rate_change}"
    elif temp_base_spread_cash_flow - previous_month_cash_flow < 0:
        cash_flow_message = f"Cash Flow Rates have decreased {cash_flow_rate_change}"
    else:
        cash_flow_message = "Cash Flow Rates are unchanged from previous month"

    flash(
        f"{pro_forma_message} and {cash_flow_message} as of {spread_start_date}. Current Rate Card Expires {spread_end_date}.",
        category='error'
)