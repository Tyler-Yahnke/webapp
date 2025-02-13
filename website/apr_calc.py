from flask import Blueprint, render_template, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from . import db
import looker_sdk  # Access Looker API
import json
from looker_sdk import models40
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from scipy.optimize import fsolve
import numpy as np
import os


apr_calc = Blueprint('apr_calc', __name__)

@apr_calc.route('/', methods=['GET', 'POST'])
@login_required



def apr_calc_logic():
    print('apr_calc')

    data = {'LAI': [''],
            'APR': [''],
            'Borrower State': [''],
            'State': [''],
            'Funded Date': [''],
            'Net Loan Amount': ['']
            }
    apr_table = pd.DataFrame(data)

    previous_data = {}

    if request.method == 'POST':

        user_selection_lai = request.form.get('lai')
        user_selection_state = request.form.get('state')
        user_selection_start_date = request.form.get('start_date')
        user_selection_end_date = request.form.get('end_date')

        previous_data = {
            'lai': user_selection_lai,
            'state': user_selection_state,
            'start_date': user_selection_start_date,
            'end_date': user_selection_end_date
        }

        #print(previous_data)

        if user_selection_lai=="" and user_selection_state =="Select State" and user_selection_start_date=="" and user_selection_end_date=="":
            flash('At least one search criteria must be given', category='error')
            return render_template("apr_calc.html", user=current_user, apr_table=apr_table,
                                   previous_data=previous_data)

        # Call looker_data_pull and capture the result
        platform_apr_df = looker_data_pull(user_selection_lai, user_selection_state, user_selection_start_date,
                                           user_selection_end_date)
        if platform_apr_df.empty:
            flash('No Results Found. Verify Search Criteria', category='error')
            print("No results were added to platform_apr_df.empty")
            return render_template("apr_calc.html", user=current_user, apr_table=apr_table,
                                   previous_data=previous_data)
            return

        # Initialize payment_results before starting the loop
        payment_results = []

        def process_row(row):
            """Process a single row of the DataFrame."""
            # Convert necessary columns to appropriate data types
            funding_date = pd.to_datetime(row['funded_date'])
            expected_first_payment_date = pd.to_datetime(row['expected_first_payment_date'])
            term = int(row['term']) if pd.notna(row['term']) else 0
            origination_fee = row['origination_fee']
            amount_financed = row['net_loan_amount']
            interest_rate = row['interest_rate'] / 100
            balloon_payment = row['balloon_payment']
            first_period_payment = row['first_period_payment']
            loan_amount = row['loan_amount']
            monthly_payment = row['monthly_payment']
            life_insurance_required = row['life_insurance_required']
            pre_existing_policy_value = row['pre_existing_policy_value']
            borrowing_entity_state = row['borrowing_entity_state']
            lai = row['cl_contract']

            apr_table = {}

            # Determine payments dynamically
            if row['interest_only_period'] > 0:
                payment_1 = round((loan_amount * (interest_rate / 12)) + first_period_payment, 2)
                payment_2 = round((loan_amount * (interest_rate / 12)), 2)
                payment_3 = monthly_payment

                interest_only_period = int((row['interest_only_period'] - 1))

                calculate_payment_schedule(funding_date, expected_first_payment_date, term, lai)

                # Calculate remaining balance after each payment
                remaining_balances, insurance_premiums = calculate_remaining_balance(loan_amount, interest_rate,
                                                                                     payment_periods,
                                                                                     payment_1, payment_2, payment_3,
                                                                                     interest_only_period,
                                                                                     pre_existing_policy_value)
                payment_4 = remaining_balances[-1] + monthly_payment

                #print(payment_4)
                #print(payment_periods[0])

            else:
                payment_1 = monthly_payment + first_period_payment
                payment_2 = monthly_payment
                payment_3 = 0
                payment_4 = 0  # No fourth payment when no IO
                interest_only_period = int(row['interest_only_period']) if pd.notna(row['interest_only_period']) else 0

                calculate_payment_schedule(funding_date, expected_first_payment_date, term, lai)

                # Calculate remaining balance after each payment
                remaining_balances, insurance_premiums = calculate_remaining_balance(loan_amount, interest_rate,
                                                                                     payment_periods,
                                                                                     payment_1, payment_2, payment_3,
                                                                                     interest_only_period,
                                                                                     pre_existing_policy_value)
                payment_3 = remaining_balances[-1] + monthly_payment


                #print(remaining_balances)


            if life_insurance_required != 't':
                insurance_premiums = [0] * row['term']



            #print(payment_1)
            #print(payment_2)
            #print(payment_3)
            #print(payment_4)

            # Calculate APR
            calculate_apr(payment_1, payment_2, payment_3, payment_4, amount_financed, payment_periods, interest_only_period, insurance_premiums)



            # Collect results after processing each row
            payment_results.append({
                'lai': row['cl_contract'],
                'net_loan_amount': row['net_loan_amount'],
                'apr': apr,
                'borrower_state': row['borrowing_entity_state'],
                'funded_date': row['funded_date']
            })

        # Loop through the rows in platform_apr_df and process each row
        for index, row in platform_apr_df.iterrows():
            process_row(row)

        # After the loop, if the payment_results list is empty, check for any issues
        if payment_results:
            payment_results_df = pd.DataFrame(payment_results)

        else:
            flash('No Results Found. Verify Search Criteria', category='error')
            print("No results were added to payment_results.")

        # Check if the download button was clicked
        button = request.form.get('download')
        if button == 'Download File':
            # Call the download_file function if the button was clicked
            return download_file(payment_results_df)

        return render_template("apr_calc.html", user=current_user, apr_table=payment_results_df, previous_data=previous_data)

    return render_template("apr_calc.html", user=current_user, apr_table=apr_table, previous_data=previous_data)


def download_file(payment_results_df):
    # Create the output file path (you can specify a temporary folder)
    output_filename = "/tmp/APR_Calculations.xlsx"  # Temporary location for the file

    # Export the DataFrame to Excel
    payment_results_df.to_excel(output_filename, index=False)

    # Send the file as a response to the client
    return send_file(output_filename, as_attachment=True)

def looker_data_pull(user_selection_lai, user_selection_state, user_selection_start_date, user_selection_end_date):

    # Initialize Looker API client
    looker_loc = 'looker.ini'
    sdk = looker_sdk.init40(looker_loc)

    # Modify df_creator_apr to work without params argument
    def df_creator_apr(query_apr):
        """Fetch data from Looker using SQL query."""
        try:
            slug_apr = sdk.create_sql_query(
                body=models40.SqlQueryCreate(connection_name='apc_slave', sql=query_apr)).slug
            result_apr = sdk.run_sql_query(slug=slug_apr, result_format='json')

            if not result_apr.strip():  # Check if response is empty
                print("No data returned from Looker.")
                return pd.DataFrame()

            data_apr = json.loads(result_apr)  # Convert JSON to Python Dict
            df_apr = pd.DataFrame.from_dict(data_apr)
            return df_apr
        except Exception as e:
            print(f"Error in df_creator_apr: {str(e)}")
            return pd.DataFrame()

    # Define the query with direct string formatting for parameters
    query_apr = """
    SELECT DISTINCT 
    b.cl_contract,
    b.loan_amount,
    b.monthly_payment,
    b.first_period_payment,
    b.net_loan_amount,
    b.interest_rate,
    sf.closedate as funded_date,
    b.expected_first_payment_date,
    b.term,
    b.interest_only_period,
    b.origination_fee,
    b.documentation_fee,
    b.balloon_payment,
    add_borrower.state as borrowing_entity_state,
    sf.Financing_Type__c,
    b.life_insurance_required,
    b.pre_existing_policy_value
    FROM loans b 
    LEFT JOIN salesforce.opportunity sf ON b.opportunity_id = sf.sfid
    LEFT JOIN borrower_entity_ownerships d ON b.legal_entity_id = d.legal_entity_id
    LEFT JOIN addresses add_borrower ON d.legal_entity_id = add_borrower.addressable_id AND add_borrower.addressable_type = 'LegalEntity'
    WHERE 1=1
    AND sf.loan_product__c = 'Core'
    AND b.stage = '17'
    """

    # Dynamically add conditions based on user input
    if user_selection_state !="" and user_selection_state != 'Select State':
        query_apr += f" AND add_borrower.state = '{user_selection_state}'"
        if user_selection_state =='CA':
            query_apr += f"AND b.net_loan_amount < 500001"
        elif user_selection_state =='NY':
            query_apr += f"AND b.net_loan_amount < 2500001"

    if user_selection_start_date !="" and user_selection_end_date !="":
        query_apr += f" AND sf.closedate BETWEEN '{user_selection_start_date}' AND '{user_selection_end_date}'"

    if user_selection_lai !="":
        query_apr += f" AND b.cl_contract LIKE '%{user_selection_lai}'"

    # Manually substitute user input into the query string (ensure input is sanitized)
    query_apr = query_apr.format(
        user_selection_lai=user_selection_lai if user_selection_lai else '',
        user_selection_state=user_selection_state if user_selection_state else '',
        user_selection_start=user_selection_start_date if user_selection_start_date else '',
        user_selection_end=user_selection_end_date if user_selection_end_date else ''
    )

    return df_creator_apr(query_apr)


def calculate_payment_schedule(funding_date, expected_first_payment_date, term, lai):
    global payment_periods
    """Calculate payment schedule based on funding and first payment dates."""
    if not isinstance(funding_date, datetime):
        funding_date = pd.to_datetime(funding_date)
    if not isinstance(expected_first_payment_date, datetime):
        expected_first_payment_date = pd.to_datetime(expected_first_payment_date)

    previous_month_date = expected_first_payment_date - relativedelta(months=1)
    first_payment_period = 1 + ((previous_month_date - funding_date).days / 30)
    payment_periods = [round(first_payment_period, 2)]
    for i in range(1, term):
        payment_periods.append(round(payment_periods[-1] + 1, 5))

    #print(payment_periods[0])


def calculate_apr(payment_1, payment_2, payment_3, payment_4, amount_financed, payment_periods,interest_only_period, insurance_premiums):
    global apr
    """Calculate APR by solving for the discount rate."""

    def npv_function(apr_monthly_rate):
        if apr_monthly_rate <= 0:
            return 1e10  # Prevents negative APR

        npv = 0
        present_values = []

        total_payment = payment_1 + (insurance_premiums[0]*payment_periods[0])

        # First payment
        pv_first_payment = total_payment / (1 + apr_monthly_rate[0]) ** payment_periods[0]
        npv += pv_first_payment
        present_values.append(pv_first_payment)


        if interest_only_period > 0:
            # Payment 2 - If IO period then this will be IO payment
            for i, period in enumerate(payment_periods[1:interest_only_period + 1]):
                insurance_premium = insurance_premiums[i + 1]  # i+1 to account for starting from index 2

                total_payment = payment_2 + insurance_premium

                pv_payment = total_payment / (1 + apr_monthly_rate[0]) ** period
                npv += pv_payment
                present_values.append(pv_payment)
                # print(f"{float(pv_payment):.2f}")

            # Payment 3 - If IO period then this will be normal payment.
            for i, period in enumerate(payment_periods[interest_only_period + 1:-1]):
                insurance_premium = insurance_premiums[interest_only_period + 1 + i]# Shift insurance premiums
                # Calculate the total payment (including insurance premium)
                total_payment = payment_3 + insurance_premium

                # Apply the discount to the total payment for the period
                pv_payment = total_payment / (1 + apr_monthly_rate[0]) ** period

                npv += pv_payment
                present_values.append(pv_payment)
                # print(f"{float(pv_payment):.2f}")

            # Payment 4 - If IO period then this will be balloon amount + normal payment. If no IO period then no payment 4
            final_period = payment_periods[-1]  # Extract the final payment period correctly
            total_payment = payment_4 + insurance_premiums[-2]

            pv_final_payment = total_payment / (1 + apr_monthly_rate[0]) ** final_period
            npv += pv_final_payment
            present_values.append(pv_final_payment)
            # print(f"{float(pv_final_payment):.2f}")

        else:
            # Regular payments for non-IO period loans
            for i, period in enumerate(payment_periods[1:-1]):

                insurance_premium = insurance_premiums[i + 1]  # i+1 to account for starting from index 2

                total_payment = payment_2 + insurance_premium

                pv_payment = total_payment / (1 + apr_monthly_rate[0]) ** period
                npv += pv_payment
                present_values.append(pv_payment)
                # print(f"Month {i + 2}: {float(pv_payment):.2f}")

            # Final payment including balloon if applicable
            final_period = payment_periods[-1]
            total_payment = payment_3 + insurance_premiums[-2]

            pv_final_payment = total_payment / (1 + apr_monthly_rate[0]) ** final_period
            npv += pv_final_payment
            present_values.append(pv_final_payment)
            # print(f"Month {len(payment_schedule)} (Final Payment): {float(pv_final_payment):.2f}")

        return npv - amount_financed  # Goal: Should be equal to zero

    estimated_apr = [0.08 / 12]  # Approximate monthly rate from an 8% annual rate
    apr_monthly_rate = fsolve(npv_function, estimated_apr)[0]
    apr_annual = max(apr_monthly_rate * 12 * 100, 0)  # Ensure non-negative APR
    apr = round(apr_annual, 2)

    return apr


def round_up_to_nearest_tier(amount):
    global tier
    """Round up to the nearest available insurance tier."""
    insurance_premium_table = {
        100000: 11.54,
        250000: 15.15,
        500000: 19.36,
        1000000: 29.56,
        1100000: 41.10,
        1250000: 44.71,
        1500000: 48.92,
        2000000: 59.12,
        2100000: 70.66,
        2250000: 74.27,
        2500000: 78.48,
        3000000: 88.68,
        3100000: 100.22,
        3250000: 103.83,
        3500000: 108.04,
        4000000: 118.24,
        4100000: 129.78,
        4250000: 133.39,
        4500000: 137.60,
        5000000: 147.80
    }

    for tier in sorted(insurance_premium_table.keys()):
        if amount <= tier:
            return tier, insurance_premium_table[tier]
    return tier


def calculate_remaining_balance(loan_amount, interest_rate, payment_schedule, payment_1, payment_2, payment_3,
                                interest_only_period, pre_existing_policy_value):

    """Calculate remaining balance after each payment and determine life insurance premium based on prior month's balance."""
    balance = loan_amount
    remaining_balances = []
    insurance_premiums = []

    previous_balance = balance  # Set the initial balance for Month 1 insurance calculation

    if interest_only_period > 0:
        # First payment (Insurance premium for the first month)
        insurance_tier, premium = round_up_to_nearest_tier(max(previous_balance - pre_existing_policy_value, 0))
        insurance_premiums.append(premium)

        remaining_balances.append(round(balance, 2))
        previous_balance = balance  # Store balance before applying payment

        # Interest-Only Payments
        for month in range(interest_only_period):
            # No principal payment, just interest
            balance -= 0  # Principal does not change
            insurance_tier, premium = round_up_to_nearest_tier(max(previous_balance - pre_existing_policy_value, 0))
            insurance_premiums.append(premium)  # Add premium based on remaining balance

            remaining_balances.append(round(balance, 2))
            previous_balance = balance  # Update for next month

        # Regular Payments (After IO Period)
        for month in range(len(payment_schedule) - interest_only_period - 1):
            interest = balance * (interest_rate / 12)
            principal = payment_3 - interest
            balance -= principal

            insurance_tier, premium = round_up_to_nearest_tier(max(previous_balance - pre_existing_policy_value, 0))
            insurance_premiums.append(premium)  # Add premium based on remaining balance

            remaining_balances.append(round(balance, 2))
            previous_balance = balance  # Update for next month

            #print(remaining_balances)

        return remaining_balances, insurance_premiums

    else:
        # First payment (Insurance premium for the first month)
        insurance_tier, premium = round_up_to_nearest_tier(max(previous_balance - pre_existing_policy_value, 0))
        insurance_premiums.append(premium)


        interest = balance * ((interest_rate / 12))
        principal = payment_1 - interest * payment_schedule[0]
        balance -= principal
        remaining_balances.append(round(balance, 2))
        previous_balance = balance  # Update for next month


        # Regular Payments
        for _ in range(len(payment_schedule) - 1):
            interest = balance * (interest_rate / 12)
            principal = payment_2 - interest
            balance -= principal

            insurance_tier, premium = round_up_to_nearest_tier(max(previous_balance - pre_existing_policy_value, 0))
            insurance_premiums.append(premium)  # Add premium based on remaining balance

            remaining_balances.append(round(balance, 2))
            previous_balance = balance  # Update for next month

       # # Final Payment (Balloon Payment)
        #if payment_3 > 0:
          #  insurance_premiums.append(0)  # No insurance needed when balance is zero
          #  balance = 0
           # remaining_balances.append(round(balance, 2))


    return remaining_balances, insurance_premiums



