from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from . import db
from .models import CMValidation
from sqlalchemy import desc, and_
from docx import Document
import looker_sdk #access looker objects
import json
from looker_sdk import methods40, models40
import pandas as pd
import re
import time
import datetime
import os
import tempfile

cm_validation = Blueprint('cm_validation', __name__)


@cm_validation.route('/', methods=['GET', 'POST'])
@login_required
def credit_memo_validation():
    global potential_discrepancy, not_located
    potential_discrepancy = {}
    not_located = []


    if request.method == 'POST':

        doc_extraction()

        looker_bwg_table()

        # Return if CL_contract cant be found
        if matching_df.empty:
            flash('LAI Not Found', category='error')
            return render_template("cm_validation.html", user=current_user,potential_discrepancy=potential_discrepancy, not_located=not_located)
        else:
            flash('LAI Found', category='success')


            # creating dict/list of mistmatches and not located
            potential_discrepancy = {}
            not_located = []


            #matching logic
            brand_category_partner()
            borrowing_entity()
            personal_guarantors()
            address_of_subject_unit()
            down_payment()
            loan_terms()
            interest_rate()
            investment_grade()
            important_ratios()
            acr_pcv_pcr()


            #logging data
            log_selections()

            # Print the list of mismatches
            #print("Potential Discrepancy:", potential_discrepancy)
            #print("Unable to Compare:", not_located)


            return render_template("cm_validation.html", user=current_user,potential_discrepancy=potential_discrepancy, not_located=not_located)

    return render_template("cm_validation.html", user=current_user, potential_discrepancy=potential_discrepancy, not_located=not_located)

def doc_extraction():
    global content
    if 'file' not in request.files:
        flash('No document was submitted.', category='error')
        return render_template("cm_validation.html", user=current_user, potential_discrepancy=potential_discrepancy,
                               not_located=not_located)

    doc_path = request.files['file']

    if doc_path.filename == '':
        flash('No document was submitted.', category='error')
        return render_template("cm_validation.html", user=current_user, potential_discrepancy=potential_discrepancy,
                               not_located=not_located)

    # Save the uploaded document temporarily
    doc_filename = doc_path.filename
    temp_dir = tempfile.gettempdir()
    temp_doc_path = os.path.join(temp_dir, doc_filename)
    doc_path.save(temp_doc_path)

    def standardize_column_title(title):
        # Regular expression patterns to match variations of column titles
        patterns = [
            (r'Franchise\s*(?:\(\d+\))?', 'Franchise Brand | Category |  Partner/Non-Partner'),
            (r'Personal\s+Guarantors\s*(?:\(\d+\))?', 'Personal Guarantors'),
            (r'Corporate\s+Guarantor\s*(?:\(\d+\))?', 'Corporate Guarantor'),
            (r'Borrowing\s+Entity\s*(?:\(\d+\))?', 'Borrowing Entity'),
            (r'Address of\s*(?:\(\d+\))?', 'Address of Subject Unit(s) Collateral'),
            (r'Total Ownership\s*(?:\(\d+\))?', 'Total Ownership Net  Worth / ACR / PCV /  PCR')
        ]

        # Iterate over patterns and check for matches
        for pattern, standardized_title in patterns:
            match = re.match(pattern, title)
            if match:
                return standardized_title

        # If no match is found, return the original title
        return title

    def extract_text_from_table(doc):
        table_content = {}
        for table in doc.tables:
            for row in table.rows:
                left_text = None
                right_text = None
                for idx, cell in enumerate(row.cells):
                    cell_text = cell.text.strip()
                    if idx == 0:
                        left_text = cell_text
                    elif idx == 1:
                        right_text = cell_text
                    else:
                        # Handle cells with more than two columns
                        # You can skip them or handle them differently based on your requirements
                        pass

                # If both left and right text are found, store them in table_content
                if left_text is not None and right_text is not None:
                    standardized_title = standardize_column_title(left_text)
                    table_content[standardized_title] = right_text

        return table_content

    # Extracting text
    def extract_text_from_docx(docx_path):
        doc = Document(docx_path)  # Assuming the document is in .docx format
        table_content = extract_text_from_table(doc)
        return table_content

    # Extract content from the temporary document
    content = extract_text_from_docx(temp_doc_path)

    # Remove the temporary document file
    os.remove(temp_doc_path)

    return content

def looker_bwg_table():
    global matching_df

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1

    def run_query_with_retry(query):
        for attempt in range(MAX_RETRIES):
            try:
                # Attempt to run the query
                return df_creator(query)
            except looker_sdk.error.SDKTimeoutError:
                # If a timeout occurs, wait for a short delay and retry
                time.sleep(RETRY_DELAY_SECONDS)
                continue
        # If all retries fail, raise an error
        raise Exception("Failed to run query after multiple attempts")

    try:

        # Connecting to Looker
        looker_loc = 'looker.ini'
        sdk = looker_sdk.init40(looker_loc)

        def df_from_look(looker_id):
            look = sdk.look(look_id=str(looker_id))
            try:
                response = sdk.run_look(
                    look_id=look.id,
                    result_format="json"
                )
                data = json.loads(response)
                return pd.DataFrame.from_dict(data)
            except:
                raise Exception(f'Error running look {look.id}')

        def df_creator(query):
            slug = sdk.create_sql_query(body=models40.SqlQueryCreate(connection_name='apc_slave', sql=query)).slug
            # Use run_query_with_retry instead of run_sql_query
            result_df = run_query_with_retry(slug=slug)
            return result_df

        df = df_from_look(1351)

        # searching for CL in looker
        matching_df = df[df['loans.cl_contract'].str.contains(content['LAI #'])]
        return matching_df

    except Exception as e:
        #matching_df = pd.DataFrame()
        flash('Looker Timeout Error. Wait and Rerun', category='error')
        return render_template("cm_validation.html", user=current_user, potential_discrepancy=potential_discrepancy,
                               not_located=not_located), matching_df

def brand_category_partner():
    global potential_discrepancy,not_located
    # Brand, category, Partner
    split_values = content['Franchise Brand | Category |  Partner/Non-Partner'].split(" | ")

    try:
        brand_doc = str(split_values[0]).replace("’", "").replace(" ", "").upper()
        brand_df = str(matching_df['franchisor.name'].iloc[0]).replace("'", "").replace(" ", "").upper()
        if brand_doc != brand_df:
            potential_discrepancy['Franchise Brand'] = {
                'document_value': split_values[0],
                'dataframe_value': matching_df['franchisor.name'].iloc[0]
            }
    except Exception as e:
        not_located.append('Franchise Brand')
    try:
        category_doc = str(split_values[1]).replace("Category", "").replace(" ", "").upper()
        category_df = str(matching_df['loans.brand_category_at_time_of_application_for_investors'].iloc[0]).replace(" ",
                                                                                                                    "").upper()
        if category_doc != category_df:
            potential_discrepancy['Category'] = {
                'document_value': split_values[1],
                'dataframe_value': 'Category ' + str(matching_df['loans.brand_category_at_time_of_application_for_investors'].iloc[0])
            }
    except Exception as e:
        not_located.append('Category')
    try:
        partner_doc = str(split_values[2]).replace(" ", "").upper()
        partner_df = str(matching_df['brand_status'].iloc[0]).replace(" ", "").upper()
        if partner_doc != partner_df:
            potential_discrepancy['Partner/Non-Partner'] = {
                'document_value': split_values[2],
                'dataframe_value': matching_df['brand_status'].iloc[0]
            }
    except Exception as e:
        not_located.append('Partner/Non-Partner')
    return potential_discrepancy,not_located

def borrowing_entity():
    global potential_discrepancy, not_located
    # Borrowing Entity
    try:
        borrowing_entity_doc = str(content['Borrowing Entity']).replace(" ", "").upper()
        borrowing_entity_df = str(matching_df['legal_entities.name_reformatted'].iloc[0]).replace(" ", "").upper()
        if borrowing_entity_doc != borrowing_entity_df:
            potential_discrepancy['Borrowing Entity'] = {
                'document_value': content['Borrowing Entity'],
                'dataframe_value': matching_df['legal_entities.name_reformatted'].iloc[0]
            }
    except Exception as e:
        not_located.append('Borrowing Entity')
    return potential_discrepancy, not_located

def personal_guarantors():
    global potential_discrepancy, not_located
    # Personal Guarantors
    try:
        personal_guarantors_doc = set(
            str(content['Personal Guarantors']).upper().replace(',', '\n').replace(' ', '').split('\n'))
        personal_guarantors_list = list(personal_guarantors_doc)
        # Filtering out non guarantors
        filtered_df = matching_df[(matching_df['guarantor_data.ownership_percentage'].notnull()) & (
                matching_df['guarantor_data.entity_type'] == 'individual')]
        personal_guarantors_df = set(
            (filtered_df['guarantor_data.guarantor_first_name'].str.strip().replace(' ', '') +
             filtered_df['guarantor_data.guarantor_last_name'].str.strip()).str.upper())
        personal_guarantors_df_list = list(personal_guarantors_df)

        # Find guarantors in document list but not in DataFrame list
        missing_in_df = set(personal_guarantors_list) - set(personal_guarantors_df_list)
        # Find guarantors in DataFrame list but not in document list
        missing_in_doc = set(personal_guarantors_df_list) - set(personal_guarantors_list)

        personal_guarantors_doc_ui = set(str(content['Personal Guarantors']).split('\n'))
        personal_guarantors_df_ui = set(filtered_df['guarantor_data.guarantor_first_name'] + filtered_df['guarantor_data.guarantor_last_name'])
        personal_guarantors_df_ui_display = ', '.join(str(name) for name in personal_guarantors_df_ui)

        for guarantor in missing_in_df:
            potential_discrepancy['Personal Guarantors CM'] = {
                'document_value': ', '.join(personal_guarantors_doc_ui),
                'dataframe_value': personal_guarantors_df_ui_display
            }
        for guarantor in missing_in_doc:
            potential_discrepancy['Personal Guarantors DB'] = {
                'document_value': ', '.join(personal_guarantors_doc_ui),
                'dataframe_value': personal_guarantors_df_ui_display
            }
    except Exception as e:
        not_located.append('Personal Guarantors')
    return potential_discrepancy, not_located

def corporate_guarantors():

    #corporate guarantors
    # Personal Guarantors
    corp_guarantors_doc = set(str(content['Corporate guarantor']).upper().replace(',', '\n').replace(' ', '').split('\n'))
    corp_guarantors_list = list(corp_guarantors_doc)
    #Filtering out non guarantors
    filtered_df = matching_df[(matching_df['guarantor_data.entity_type'] != 'individual')]
    corp_guarantors_df = set((filtered_df['guarantor_data.guarantor_first_name'].str.strip().upper()))
    corp_guarantors_df_list = list(personal_guarantors_df)
    #####No Corp guarantors in report?????

    try:
        # Find corp guarantors in document list but not in DataFrame list
        missing_in_df = set(corp_guarantors_list) - set(corp_guarantors_df_list)
        # Find corp guarantors in DataFrame list but not in document list
        missing_in_doc = set(corp_guarantors_df_list) - set(corp_guarantors_list)
        for corp_guarantor in missing_in_df:
            mismatches.append(('Corporate Guarantor missing in Looker', corp_guarantor))
        for corp_guarantor in missing_in_doc:
            mismatches.append(('Corporate Guarantor missing in Credit Memo', corp_guarantor))
    except Exception as e:
        not_located.append('Corporate Guarantor')

def address_of_subject_unit():
    global potential_discrepancy, not_located
    # Address of Subject Unit
    address_pattern = r'\b\d{1,5}\s+\w+.*?,\s+\w+.*?,\s+\w+\s+\d{5}\b'

    try:
        # Find addresses in the text
        addresses = re.findall(address_pattern, content['Address of Subject Unit(s) Collateral'])

        address_doc = str(addresses[0]).replace(" ", "").replace(" ", "").upper()
        address_df = (
                str(matching_df['loans.business_property_location_address'].iloc[0]) + ', ' +
                str(matching_df['loans.business_property_location_city'].iloc[0]) + ', ' +
                str(matching_df['loans.business_property_location_state'].iloc[0]) +
                str(matching_df['loans.business_property_location_zip'].iloc[0])
        ).replace(" ", "").upper()

        if address_doc != address_df:
            potential_discrepancy['Address of Subject Unit(s) Collateral'] = {
                'document_value': addresses[0],
                'dataframe_value': address_df
            }
    except Exception as e:
        not_located.append('Address of Subject Unit(s) Collateral')
    return potential_discrepancy, not_located

def down_payment():
    global potential_discrepancy, not_located
    # Down Payment
    try:
        down_payment_str = str(content.get('Down Payment | %', ''))

        # Check if the string contains the '|' character
        if '|' in down_payment_str:
            down_payment_parts = down_payment_str.split(" | ")
            if len(down_payment_parts) == 2:
                down_payment_amount_doc = down_payment_parts[0].replace("$", "").replace(" ", "").replace(",",
                                                                                                          "").replace(
                    "%", "").replace("(", "").replace(")", "")
                down_payment_percent_doc = down_payment_parts[1].replace("%", "").replace(" ", "").replace("(",
                                                                                                           "").replace(
                    ")", "")
                if down_payment_percent_doc != str(matching_df['loans.down_payment_percent'].iloc[0]):
                    potential_discrepancy['Down Payment % '] = {
                        'document_value': down_payment_parts[1],
                        'dataframe_value': matching_df['loans.down_payment_percent'].iloc[0]
                    }
            else:
                not_located.append('Down Payment | % (Percent Missing)')
        else:
            # If '|' is not present, assume down_payment_str contains only the down payment amount
            down_payment_amount_doc = down_payment_str.replace("$", "").replace(" ", "").replace(",",
                                                                                                 "").replace(
                "%", "").replace("(", "").replace(")", "")
            not_located.append('Down Payment Percent')
            down_payment_percent_doc = None  # Or any default value you want to assign
    except Exception as e:
        not_located.append('Down Payment | %')


    try:
        down_payment_str = str(content.get('Down Payment | %', ''))
        if int(down_payment_amount_doc) != int(matching_df['loans.down_payment'].iloc[0]):
            potential_discrepancy['Down Payment Amount'] = {
                'document_value': down_payment_amount_doc,
                'dataframe_value': matching_df['loans.down_payment'].iloc[0]
            }
    except Exception as e:
        not_located.append('Down Payment | % (Percent Missing)')

    return potential_discrepancy, not_located

def loan_terms():
    global potential_discrepancy, not_located
    # Loan Terms
    term_pattern = r"mature (\d+) years"
    interest_only_pattern = r"(\d+) months of interest only"
    term_after_io_pattern = r"followed by (\d+) principal and interest payments"
    amortizing_pattern = r"based on a (\d+)"

    try:
        term_doc = re.search(term_pattern, content['Loan terms']).group(1)
        term_df = int(matching_df['loans.term'].iloc[0] / 12)
        if int(term_doc) != term_df:
            potential_discrepancy['Loan Terms (Term)'] = {
                'document_value': term_doc,
                'dataframe_value': term_df
            }
    except Exception as e:
        not_located.append('Loan Terms (Term)')
    try:
        interest_only_doc = re.search(interest_only_pattern, content['Loan terms']).group(1)
        if int(interest_only_doc) != int(matching_df['loans.interest_only_period'].iloc[0]):
            potential_discrepancy['Loan Terms (IO Period)'] = {
                'document_value': interest_only_doc,
                'dataframe_value': matching_df['loans.interest_only_period'].iloc[0]
            }
    except Exception as e:
        not_located.append('Loan Terms (IO Period)')
    try:
        term_after_io_doc = re.search(term_after_io_pattern, content['Loan terms']).group(1)
        term_after_io_df = int(
            matching_df['loans.term'].iloc[0] - matching_df['loans.interest_only_period'].iloc[0])

        if int(term_after_io_doc) != term_after_io_df:
            potential_discrepancy['Loan Terms (Term After IO Period)'] = {
                'document_value': term_after_io_doc,
                'dataframe_value': term_after_io_df
            }
    except Exception as e:
        not_located.append('Loan Terms (Term After IO Period)')
    try:
        amortizing_doc = re.search(amortizing_pattern, content['Loan terms']).group(1)
        amortizing_df = int(
            matching_df['loans.amortization_term'].iloc[0] - matching_df['loans.interest_only_period'].iloc[0])
        if int(amortizing_doc) != amortizing_df:
            potential_discrepancy['Loan Terms (Amortization)'] = {
                'document_value': amortizing_doc,
                'dataframe_value': amortizing_df
            }
    except Exception as e:
        not_located.append('Loan Terms (Amortization)')
    return potential_discrepancy, not_located

def interest_rate():
    global potential_discrepancy, not_located
    # Interest Rate
    interest_rate_pattern = r"(\d+(\.\d+)?)% \("
    pricing_pattern = r'\((Pro Forma|Cash Flow) Pricing'
    # month_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b'
    spread_pattern = r'Spread\s?=\s?(\d+(\.\d+)?%)'
    # swap_pattern =r'(?<=Rate\s?=\s?)\d+(?:\.\d+)?%'

    # rate_month_doc = re.search(month_pattern, content['Interest Rate']).group(0)
    # swap_doc = re.search(swap_pattern, content['Interest Rate']).group(1)

    try:
        interest_rate_doc = re.search(interest_rate_pattern, content['Interest Rate']).group(1)
        if interest_rate_doc != str(matching_df['loans.approved_rate_in_commit_letter'].iloc[0]):
            potential_discrepancy['Interest Rate'] = {
                'document_value': interest_rate_doc,
                'dataframe_value': matching_df['loans.approved_rate_in_commit_letter'].iloc[0]
            }
    except Exception as e:
        not_located.append('Interest Rate')
    try:
        pricing_pattern_doc = re.search(pricing_pattern, content['Interest Rate']).group(1)
        if str(pricing_pattern_doc) != str(matching_df['loans.pricing_basis'].iloc[0]):
            potential_discrepancy['Interest Rate (Pricing Basis)'] = {
                'document_value': pricing_pattern_doc,
                'dataframe_value': matching_df['loans.pricing_basis'].iloc[0]
            }
    except Exception as e:
        not_located.append('Interest Rate (Pricing Basis)')
    try:
        spread_doc = re.search(spread_pattern, content['Interest Rate']).group(1).replace("%", "")
        if spread_doc != str(matching_df['loans.commitment_letter_spread_rate'].iloc[0]):
            potential_discrepancy['Interest Rate (Spread Rate)'] = {
                'document_value': spread_doc,
                'dataframe_value': matching_df['loans.commitment_letter_spread_rate'].iloc[0]
            }
    except Exception as e:
        not_located.append('Interest Rate (Spread Rate)')
    return potential_discrepancy, not_located

def investment_grade():
    global potential_discrepancy, not_located
    # Investment Grade
    try:
        if content['Investment Grade'] != matching_df['loans.investment_grade'].iloc[0]:
            potential_discrepancy['Investment Grade'] = {
                'document_value': content['Investment Grade'],
                'dataframe_value': matching_df['loans.investment_grade'].iloc[0]
            }
    except Exception as e:
        not_located.append('Investment Grade')
    return potential_discrepancy, not_located

def important_ratios():
    global potential_discrepancy, not_located
    # Important Ratios section
    projected_gdscr = r"Projected\s*GDSCR:\s*(\d+\.\d+)"
    projected_dscr = r"Projected\s*DSCR:\s*(\d+\.\d+)"
    projected_fccr = r"Projected\s*FCCR:\s*(\d+\.\d+)"
    projected_debt_to_ebitda = r"Projected\s*Debt-to-EBITDA:\s*(\d+\.\d+)"
    projected_lease_adjusted_debt_to_ebitda = r"Projected\s*Lease-Adjusted\s*Debt-to\s*EBITDAR:\s*(\d+\.\d+)"

    # including TIs
    try:
        projected_gdscr_doc = re.search(projected_gdscr, content['Important Ratios']).group(1)
        if str(projected_gdscr_doc) != str(matching_df['loans.global_dscr'].iloc[0]):
            potential_discrepancy['Important Ratios(GDSCR)'] = {
                'document_value': projected_gdscr_doc,
                'dataframe_value': matching_df['loans.global_dscr'].iloc[0]
            }
    except Exception as e:
        not_located.append('Important Ratios(GDSCR)')
    try:
        projected_dscr_doc = re.search(projected_dscr, content['Important Ratios']).group(1)
        if str(projected_dscr_doc) != str(matching_df['loans.dscr_y2_dcr'].iloc[0]):
            potential_discrepancy['Important Ratios(DSCR)'] = {
                'document_value': projected_dscr_doc,
                'dataframe_value': matching_df['loans.dscr_y2_dcr'].iloc[0]
            }
    except Exception as e:
        not_located.append('Important Ratios(DSCR)')
    try:
        projected_fccr_doc = re.search(projected_fccr, content['Important Ratios']).group(1)
        if str(projected_fccr_doc) != str(matching_df['loans.y2_fixed_charge_coverage_ratio'].iloc[0]):
            potential_discrepancy['Important Ratios(FCCR)'] = {
                'document_value': projected_fccr_doc,
                'dataframe_value': matching_df['loans.y2_fixed_charge_coverage_ratio'].iloc[0]
            }
    except Exception as e:
        not_located.append('Important Ratios(FCCR)')
    try:
        projected_debt_to_ebitda_doc = re.search(projected_debt_to_ebitda, content['Important Ratios']).group(1)
        if str(projected_debt_to_ebitda_doc) != str(matching_df['loans.debt_to_ebitda'].iloc[0]):
            potential_discrepancy['Important Ratios(Debt-EBITDA)'] = {
                'document_value': projected_debt_to_ebitda_doc,
                'dataframe_value': matching_df['loans.debt_to_ebitda'].iloc[0]
            }
    except Exception as e:
        not_located.append('Important Ratios(Debt-EBITDA)')
    try:
        projected_lease_adjusted_debt_to_ebitda_doc = re.search(projected_lease_adjusted_debt_to_ebitda,
                                                                content['Important Ratios']).group(1)

        if str(projected_lease_adjusted_debt_to_ebitda_doc) != str(
                matching_df['net_rent_adjusted_debt_to_ebitdar_1'].iloc[0]):
            potential_discrepancy['Important Ratios(Projected Lease-Adjusted Debt-to EBITDAR)'] = {
                'document_value': projected_lease_adjusted_debt_to_ebitda_doc,
                'dataframe_value': matching_df['net_rent_adjusted_debt_to_ebitdar_1'].iloc[0]
            }
    except Exception as e:
        not_located.append('Important Ratios(Projected Lease-Adjusted Debt-to EBITDAR)')

    return potential_discrepancy, not_located
    # Net of TIs (Excluding TIs)

def acr_pcv_pcr():
    global potential_discrepancy, not_located
    # Also ACR and PCR
    net_worth = r"net\s*worth\s*is\s*[$]?([\d,]+)"
    asset_coverage_ratio = r"Asset\s*Coverage\s*Ratio\s*([\d]+\.[\d]+)"
    personal_collateral_value = r"Personal\s*Collateral\s*Value\s*(?:is\s*\$)?([\d,]+)"
    personal_collateral_ratio = r"Collateral\s*Ratio\s*([\d]+\.[\d]+)"

    try:
        net_worth_doc = re.search(net_worth, content['Total Ownership Net  Worth / ACR / PCV /  PCR']).group(
            1).replace(',', '').replace(" ", "").upper()

        if str(net_worth_doc) != str(matching_df['loans.total_owner_net_worth'].iloc[0]):
            potential_discrepancy['Net Worth'] = {
                'document_value': net_worth_doc,
                'dataframe_value': matching_df['loans.total_owner_net_worth'].iloc[0]
            }
    except Exception as e:
        not_located.append('Net Worth')
    try:
        asset_coverage_ratio_doc = re.search(asset_coverage_ratio,
                                             content['Total Ownership Net  Worth / ACR / PCV /  PCR']).group(1)

        if str(asset_coverage_ratio_doc) != str(matching_df['loans.acr'].iloc[0]):
            potential_discrepancy['ACR'] = {
                'document_value': asset_coverage_ratio_doc,
                'dataframe_value': matching_df['loans.acr'].iloc[0]
            }
    except Exception as e:
        not_located.append('ACR')
    try:
        personal_collateral_value_doc = re.search(personal_collateral_value,
                                                  content['Total Ownership Net  Worth / ACR / PCV /  PCR']).group(
            1).replace(',', '')
        if str(personal_collateral_value_doc) != str(matching_df['loans.total_personal_collateral_value'].iloc[0]):
            potential_discrepancy['Personal Collateral Value'] = {
                'document_value': personal_collateral_value_doc,
                'dataframe_value': matching_df['loans.total_personal_collateral_value'].iloc[0]
            }
    except Exception as e:
        not_located.append('Personal Collateral Value')
    try:
        personal_collateral_ratio_doc = re.search(personal_collateral_ratio,
                                                  content['Total Ownership Net  Worth / ACR / PCV /  PCR']).group(1)

        if str(personal_collateral_ratio_doc) != str(
                matching_df['loans.asset_coverage_personal_collateral_value'].iloc[0]):
            potential_discrepancy['PCR'] = {
                'document_value': personal_collateral_ratio_doc,
                'dataframe_value': matching_df['loans.asset_coverage_personal_collateral_value'].iloc[0]
            }
    except Exception as e:
        not_located.append('PCR')
    return potential_discrepancy, not_located


def log_selections():
    #getting each discrepancy field
    discrepancy_keys = ", ".join(potential_discrepancy.keys())
    # Convert not_located list to a string
    not_located_str = ", ".join(map(str, not_located))

    cm_validation = CMValidation(
        user = current_user.name,
        calculated_date = datetime.datetime.today(),
        lai= matching_df['loans.cl_contract'].iloc[0],
        discrepancy = discrepancy_keys,
        unable_to_validate= not_located_str
    )
    db.session.add(cm_validation)
    db.session.commit()
