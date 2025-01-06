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
    global potential_discrepancy, not_located, missing_bwg_data, bawag_indicator
    potential_discrepancy = {}
    not_located = []
    missing_bwg_data = []


    if request.method == 'POST':

        # creating dict/list of mistmatches and not located
        potential_discrepancy = {}
        not_located = []
        missing_bwg_data = []

        doc_extraction()

        looker_data_pull()

        # Return if CL_contract cant be found in platform dashboard
        if platform_df.empty:
            flash('LAI Not Found', category='error')
            return render_template("cm_validation.html", user=current_user,potential_discrepancy=potential_discrepancy, not_located=not_located, missing_bwg_data=missing_bwg_data)
        else:
            flash(f"LAI Found: {platform_df['loans.cl_contract'].iloc[0]}", category='success')


        # If BWG Loan then pull BWG dashboard
        if (platform_df['investor_approved'].iloc[0]=='BWG' or
                platform_df['whole_loan_purchaser'].iloc[0 ]=='BWG' or
                platform_df['projected_whole_loan_purchaser'].iloc[0]=='BWG'):
            bawag_indicator = 'true'
            looker_bwg_table()
        else:
            bawag_indicator = 'false'
            missing_bwg_data = ['Non BWG Loan']

            pass

        # Return if CL_contract cant be found in BWG dashboard
        if bawag_indicator=='true' and matching_df.empty:
            flash('BWG Report Not Found', category='error')
            return render_template("cm_validation.html", user=current_user,potential_discrepancy=potential_discrepancy, not_located=not_located, missing_bwg_data=missing_bwg_data)
        elif bawag_indicator=='true' and not matching_df.empty:
            flash('Validated BWG Report', category='success')
            bwg_completness_check()

        else:
            pass



        #matching logic
        ##Stopped checking breakdown of ownership, personal guarantor, corp guarantor and address based on feedback from Sean
        brand_category_partner()
        #breakdown_of_ownership()
        borrowing_entity()
        #personal_guarantors()
        #corporate_guarantors()
        credit_exception()
        global_exposure()
        #address_of_subject_unit()
        down_payment()
        loan_terms()
        interest_rate()
        investment_grade()
        #fico_results()
        important_ratios()
        acr_pcv_pcr()
        liquidity()

        #checking if potential discrepancies is empty. If so add positive message
        if not potential_discrepancy:
            potential_discrepancy['No Discrepancies Found'] = {
                'document_value':'' ,
                'dataframe_value':''
            }
        # checking if not located is empty. If so add positive message
        if not not_located:
            not_located.append("Able to Compare All Fields")


        #logging data
        log_selections()



        return render_template("cm_validation.html", user=current_user,potential_discrepancy=potential_discrepancy, not_located=not_located, missing_bwg_data=missing_bwg_data)

    return render_template("cm_validation.html", user=current_user, potential_discrepancy=potential_discrepancy, not_located=not_located, missing_bwg_data=missing_bwg_data)

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
            (r'LAI\s*(?:\(\d+\))?', 'LAI #'),
            (r'Franchise\s*(?:\(\d+\))?', 'Franchise Brand | Category |  Partner/Non-Partner'),
            (r'Breakdown\s*(?:\(\d+\))?', 'Breakdown of Ownership'),
            (r'Down\s*(?:\(\d+\))?', 'Down Payment | %'),
            (r'Personal\s+Guarantors\s*(?:\(\d+\))?', 'Personal Guarantors'),
            (r'Corporate\s*(?:\(\d+\))?', 'Corporate guarantor'),
            (r'Borrowing\s+Entity\s*(?:\(\d+\))?', 'Borrowing Entity'),
            (r'FICO\s*(?:\(\d+\))?', 'FICO Results'),
            (r'Previous\s*(?:\(\d+\))?', 'Global Exposure'),
            (r'Important\s*(?:\(\d+\))?', 'Important Ratios'),
            (r'Credit\s+Exception\s*(?:\(\d+\))?', 'Credit Exception Required'),
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

    def extract_text_from_inner_table(cell):
        inner_table_content = ""
        for table in cell.tables:
            for row in table.rows:
                for cell in row.cells:
                    inner_table_content += cell.text.strip() + " "
        return inner_table_content.strip()

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
                if left_text is not None:
                    standardized_title = standardize_column_title(left_text)
                    if standardized_title == 'Important Ratios' and not right_text:
                        # Extract data from the table within the cell to the right of the Important Ratios cell
                        if len(row.cells) > 1:
                            right_text = extract_text_from_inner_table(row.cells[1])
                    table_content[standardized_title] = right_text

        return table_content

    # Extracting text
    def extract_text_from_docx(docx_path):
        global doc
        doc = Document(docx_path)  # Assuming the document is in .docx format
        table_content = extract_text_from_table(doc)
        return table_content

    # Extract content from the temporary document
    content = extract_text_from_docx(temp_doc_path)
    # Remove the temporary document file
    os.remove(temp_doc_path)

    return content

def looker_data_pull():
    global platform_df, matching_df

    # Initialize Looker API client
    looker_loc = 'looker.ini'
    sdk = looker_sdk.init40(looker_loc)


    def df_creator(query):
        slug = sdk.create_sql_query(body=models40.SqlQueryCreate(connection_name='apc_slave', sql=query)).slug
        result = sdk.run_sql_query(slug=slug, result_format='json')
        data = json.loads(result)
        df = pd.DataFrame.from_dict(data)

        return df

    content_value = content.get('LAI #')

    query = f"""
select distinct 
b.cl_contract as "loans.cl_contract",
CASE
        WHEN b.brand_category = 'Category 1' THEN '1'::text
        WHEN b.brand_category IN ('Category 2','Category 2 Qualified') THEN '2'::text
        WHEN b.brand_category = 'Category 3' THEN '3'::text
        ELSE b.brand_category
        END AS "loans.brand_category_at_time_of_application_for_investors",
b.business_name as "legal_entities.name_reformatted", 
b.business_property_full_address as address_of_subject_unit, 
b.amortization_term as "loans.amortization_term",
b.term as "loans.term", 
b.pricing_basis as "loans.pricing_basis",
b.interest_only_period as "loans.interest_only_period",
b.down_payment as "loans.down_payment", 
b.down_payment_percent as "loans.down_payment_percent", 
b.approved_rate_in_commit_letter, 
b.rate_spread as "loans.commitment_letter_spread_rate",
b.investment_grade as "loans.investment_grade", 
CASE WHEN (b.credit_exception_required = 'true') THEN 'Yes' ELSE 'No' END AS "loans.credit_exception_required",
b.global_exposure, 
b.y2_fixed_charge_coverage_ratio as "loans.y2_fixed_charge_coverage_ratio", 
b.global_dscr as "loans.global_dscr", 
b.y2_debt_coverage_ratio as "loans.net_y2_debt_coverage_ratio", 
b.debt_to_ebitda as "loans.debt_to_ebitda", 
b.rent_adjusted_debt_to_ebitdar as "net_rent_adjusted_debt_to_ebitdar_1", 
b.total_owner_net_worth, 
b.asset_coverage_personal_collateral_value,	
b.asset_coverage as "loans.acr", 
b.total_personal_collateral_value as "loans.total_personal_collateral_value", 
b.liquidity_required_6_month_expenses, 
b.post_down_liquidity, 
e.name as corp_guarantor_name,
e.first_name as "guarantor_data.guarantor_first_name", 
e.last_name as "guarantor_data.guarantor_last_name",
go.ownership_percentage as "guarantor_data.ownership_percentage",
e.entity_type as "guarantor_data.entity_type", 
COALESCE(CAST(go.fico_update AS TEXT), CAST(go.fico AS TEXT)) as guarantor_fico,
acct.name "franchisor.name",
CASE WHEN (acct.Brand_Label__c IN ('Fully Integrated Partner', 'Partner')) THEN 'Partner' ELSE 'Non-Partner' END AS "brand_status",
 b.whole_loan_purchaser, 
 b.projected_whole_loan_purchaser, 
 b.investor_approved,
 b.financed_ti_allowance,
b.y2_fixed_charge_coverage_months
from loans b 
left join 
    guarantor_ownerships go ON  b.id = go.loan_id
LEFT JOIN
    legal_entities e ON go.legal_entity_id = e.id
LEFT JOIN 
  salesforce.opportunity sf ON b.opportunity_id = sf.sfid
LEFT JOIN 
  salesforce.account acct ON sf.Franchisor_Account__c = acct.sfid
where b.cl_contract like '%{content_value}'
    """

    # Read in from Looker with query
    platform_df = df_creator(query)
    matching_df = df_creator(query)

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
        matching_df = pd.DataFrame()
        flash('Looker Timeout Error. Wait and Rerun', category='error')
        return render_template("cm_validation.html", user=current_user, potential_discrepancy=potential_discrepancy,
                               not_located=not_located), matching_df

def bwg_completness_check():
    global missing_bwg_data

    # Check each column for no values
    for column in matching_df.columns:
        if matching_df[column].isnull().any():
            missing_bwg_data.append(column)

    #if no missing data add this text
    if not missing_bwg_data:
        missing_bwg_data.append("No Missing Information in BWG Report")


    # Remove text before the dot for each column name in the list
    missing_bwg_data = [column.split('.')[1] if '.' in column else column for column in missing_bwg_data]

    return missing_bwg_data

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


def breakdown_of_ownership():
    global potential_discrepancy, not_located

    try:
        ownership_dict = {}
        # Iterate through each line of text and extract ownership percentage and person's name
        for line in content['Breakdown of Ownership'].split('\n'):

            # Stripping bullet points
            line = line.strip().lstrip('•').lstrip('•')

            pattern = r'(\d+%)\s+owned\s+by\s+([^\n]+)'
            match = re.search(pattern, line)

            additional_pattern = r'([^\n]+):\s*(\d+%)'
            additional_match = re.search(additional_pattern, line)

            additional_matching = r'([^\-]+)\s*-\s*(\d+%)'
            additional_matching_pattern = re.search(additional_matching, line)

            if match:
                ownership_percentage = match.group(1).rstrip('%')
                person_name = match.group(2).strip().upper()
                ownership_dict[person_name] = int(ownership_percentage)

            elif additional_match:
                person_name = additional_match.group(1).strip().upper()
                ownership_percentage = additional_match.group(2).rstrip('%')
                ownership_dict[person_name] = int(ownership_percentage)

            elif additional_matching_pattern:
                person_name = additional_matching_pattern.group(1).strip().upper()
                ownership_percentage = additional_matching_pattern.group(2).rstrip('%')
                ownership_dict[person_name] = int(ownership_percentage)

            else:
                another_pattern = r'([A-Za-z]+\s[A-Za-z]+)\s*–\s*(\d+)%'
                another_pattern_match = re.search(another_pattern, line)
                if another_pattern_match:
                    person_name = another_pattern_match.group(1).strip().upper()
                    ownership_percentage = another_pattern_match.group(2).rstrip('%')
                    ownership_dict[person_name] = int(ownership_percentage)

        # Finding guarantors and their percentages
        guarantors_dict = {}

        filtered_df = matching_df[(matching_df['guarantor_data.entity_type'] == 'individual')]

        # Iterate through each row in the filtered DataFrame
        for index, row in filtered_df.iterrows():
            # Concatenate first name and last name to get guarantor's full name
            guarantor_name = (row['guarantor_data.guarantor_first_name'].strip() + ' ' + row[
                'guarantor_data.guarantor_last_name']).strip().strip().upper()
            # Get ownership percentage from the DataFrame
            ownership_percentage = int(row['guarantor_data.ownership_percentage'])
            # Add guarantor and ownership percentage to the dictionary
            guarantors_dict[guarantor_name] = ownership_percentage

        counter = 1
        # Iterate over each person in the ownership dictionary
        for person, percentage in ownership_dict.items():
            # Check if the person exists in the guarantors dictionary
            if person in guarantors_dict:
                # Compare ownership percentages
                if percentage != guarantors_dict[person]:
                    # If ownership percentages don't match, add discrepancy to potential_discrepancy dictionary
                    potential_discrepancy['Ownership Percentage' + str(counter)] = {
                        'document_value': person + ':'+ str(percentage)+'%',
                        'dataframe_value': person + ':' + str(guarantors_dict[person])+'%'
                    }
                counter +=1
            else:
                # If person doesn't exist in guarantors dictionary, add them to the not_located list
                potential_discrepancy['Ownership Percentage'+str(counter)] = {
                    'document_value': person + ':' + str(percentage) + '%',
                    'dataframe_value': "No Match. Verify Spelling"
                }
                counter += 1

                # Iterate over each person in the guarantors dictionary to find any missing individuals
        counters = 10
        for person in guarantors_dict:
            if person not in ownership_dict:
                potential_discrepancy['Ownership Percentage'+str(counters)] = {
                    'document_value': "No Match. Verify Spelling of Name",
                    'dataframe_value': person + ':'+ str(guarantors_dict[person])+'%'
                }
                counters += 1

        # Return potential discrepancies and not_located list
        return potential_discrepancy, not_located

    except Exception as e:
        not_located.append('Breakdown of Ownerships')
    return potential_discrepancy, not_located

def global_exposure():
    global potential_discrepancy, not_located


    # Define a regular expression pattern to match dollar amounts
    pattern = r'\$([0-9,]+)'

    try:

        # Find all matches in the text
        matches = re.findall(pattern, content['Global Exposure'])

        # Convert matched amounts to integers and find the maximum
        global_exposure_doc = max(int(amount.replace(',', '')) for amount in matches)

        if global_exposure_doc != int(platform_df['global_exposure'].iloc[0]):
            potential_discrepancy['Total Global Exposure to Guarantors'] = {
                'document_value': global_exposure_doc,
                'dataframe_value': int(platform_df['global_exposure'].iloc[0])
            }
    except Exception as e:
        not_located.append('Previous Loans/Total  Global Exposure to  Guarantors')

    return potential_discrepancy, not_located

def credit_exception():
    global potential_discrepancy, not_located

    try:
        if content['Credit Exception Required'] in [ 'No', 'NO','N/A', 'NA','n/a','na','Na','N/a','None', '']:
            credit_exception_doc ='No'
        else:
            credit_exception_doc = 'Yes'

        if credit_exception_doc != matching_df['loans.credit_exception_required'].iloc[0]:
            potential_discrepancy['Credit Exception Required'] = {
                'document_value': content['Credit Exception Required'],
                'dataframe_value': matching_df['loans.credit_exception_required'].iloc[0]
            }
        return potential_discrepancy, not_located
    except Exception as e:
        not_located.append('Credit Exception Required')
    return potential_discrepancy, not_located

def personal_guarantors():
    global potential_discrepancy, not_located
    # Personal Guarantors
    try:
        personal_guarantors_doc_dict = {}
        personal_guarantors_df_dict = {}

        personal_guarantors_doc = set(
            part.strip().upper().replace(',', '')
            for line in str(content['Personal Guarantors']).split('\n')
            for part in line.split(',')
            if part.strip()  # Exclude empty substrings
        )

        for guarantor in personal_guarantors_doc:
            personal_guarantors_doc_dict[guarantor] = None  # or any other initial value



        # Filtering out non guarantors
        filtered_df = matching_df[(matching_df['guarantor_data.ownership_percentage'].notnull()) & (
                matching_df['guarantor_data.entity_type'] == 'individual')]
        personal_guarantors_df = set(
            (filtered_df['guarantor_data.guarantor_first_name'].str.strip()+ " " +
             filtered_df['guarantor_data.guarantor_last_name'].str.strip()).str.upper())

        for guarantor in personal_guarantors_df:
            personal_guarantors_df_dict[guarantor] = None  # or any other initial value

        counter = 1
        for guarantor in personal_guarantors_df_dict:
            if guarantor not in personal_guarantors_doc_dict:
                potential_discrepancy['Personal Guarantors CM'+ str(counter)] = {
                    'document_value': guarantor,
                    'dataframe_value': "No Match. Verify Spelling"
                }
            counter +=1

        counters = 1
        for guarantor in personal_guarantors_doc_dict:
            if guarantor not in personal_guarantors_df_dict:
                potential_discrepancy['Personal Guarantors DB' + str(counters)] = {
                    'document_value': 'No Match. Verify Spelling',
                    'dataframe_value': guarantor
                }
            counters +=1

    except Exception as e:
        not_located.append('Personal Guarantors')
    return potential_discrepancy, not_located

def corporate_guarantors():

    try:
        corp_guarantors_doc = set(str(content['Corporate guarantor']).upper().replace(',', '\n').replace(' ', '').split('\n'))
        corp_guarantors_list = list(corp_guarantors_doc)

        corp_guarantors_doc_ui = set(str(content['Corporate guarantor']).upper().replace(',', '\n').split('\n'))
        corp_guarantors_list_ui = list(corp_guarantors_doc_ui)

        #Filtering out guarantors
        filtered_df = platform_df[platform_df['guarantor_data.entity_type'] != 'individual']
        corp_guarantors_df_list = filtered_df['corp_guarantor_name'].str.strip().str.replace(' ','').str.upper().drop_duplicates().tolist()

        corp_guarantors_df_ui = filtered_df['corp_guarantor_name'].str.strip().str.upper().drop_duplicates().tolist()

        if (len(corp_guarantors_list) > 0 or corp_guarantors_list=='N/A' or corp_guarantors_list=='NA') and len(corp_guarantors_df_list) > 0:

            try:
                # Find corp guarantors in document list but not in DataFrame list
                missing_in_df = set(corp_guarantors_list) - set(corp_guarantors_df_list)
                # Find corp guarantors in DataFrame list but not in document list
                missing_in_doc = set(corp_guarantors_df_list) - set(corp_guarantors_list)

                for corp_guarantor in missing_in_df:
                    potential_discrepancy['Corporate Guarantors CM'] = {
                        'document_value': ', '.join(corp_guarantors_list_ui),
                        'dataframe_value': corp_guarantors_df_ui
                    }

                for corp_guarantor in missing_in_doc:
                    potential_discrepancy['Corporate Guarantors DB'] = {
                        'document_value': ', '.join(corp_guarantors_list_ui),
                        'dataframe_value': corp_guarantors_df_ui
                    }
            except Exception as e:
                not_located.append('Corporate Guarantor')

        else:
            pass
    except Exception as e:
        not_located.append('Corporate Guarantor')

def address_of_subject_unit():
    global potential_discrepancy, not_located


    try:
        # Find addresses in the text
        addresses = content['Address of Subject Unit(s) Collateral'].split('\n')
        cleaned_address = re.sub(r'\([^()]*\)', '',addresses[0])

        address_doc = str(cleaned_address.replace(" ", "").replace(" ", "").upper())

        if bawag_indicator == "true":
            address_df = (
                    str(matching_df['loans.business_property_location_address'].iloc[0]) + ', ' +
                    str(matching_df['loans.business_property_location_city'].iloc[0]) + ', ' +
                    str(matching_df['loans.business_property_location_state'].iloc[0]) +
                    str(matching_df['loans.business_property_location_zip'].iloc[0])
            ).replace(" ", "").upper()

            address_df_ui = (
                    str(matching_df['loans.business_property_location_address'].iloc[0]) + ', ' +
                    str(matching_df['loans.business_property_location_city'].iloc[0]) + ', ' +
                    str(matching_df['loans.business_property_location_state'].iloc[0]) + ', ' +
                    str(matching_df['loans.business_property_location_zip'].iloc[0])
            )


            if address_doc != address_df:
                potential_discrepancy['Address of Subject Unit(s) Collateral'] = {
                    'document_value': addresses[0],
                    'dataframe_value': address_df_ui
                }
        else:

            address_df = platform_df['address_of_subject_unit'].iloc[0]

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


        if '|' in down_payment_str:
            down_payment_parts = down_payment_str.split(" | ")
            if len(down_payment_parts) == 2:
                down_payment_amount_doc = down_payment_parts[0].replace("$", "").replace(" ", "").replace(",", "").replace("%", "").replace("(", "").replace(")", "")
                down_payment_percent_doc = down_payment_parts[1].replace("%", "").replace(" ", "").replace("(","").replace(")", "")
        else:
            # Check if the string matches the pattern "$amount (percentage%)"
            match = re.match(r'\$([\d,]+(?:\.\d+)?)\s*\((\d+(?:\.\d+)?)%\)', down_payment_str)
            if match:
                down_payment_amount_doc = match.group(1).replace("$", "").replace(" ", "").replace(",", "")
                down_payment_percent_doc = match.group(2).replace(" ", "").replace(",", "").replace("%", "").replace("(", "").replace(")", "")

        # Compare the extracted values with the dataframe values
        try:
            if int(down_payment_amount_doc) != int(matching_df['loans.down_payment'].iloc[0]):
                potential_discrepancy['Down Payment Amount'] = {
                    'document_value': down_payment_amount_doc,
                    'dataframe_value': matching_df['loans.down_payment'].iloc[0]
                }
        except Exception as e:
            potential_discrepancy['Down Payment Amount'] = {
                'document_value': "",
                'dataframe_value': matching_df['loans.down_payment'].iloc[0]
            }

        try:

            if round(float(down_payment_percent_doc)) != int(round(matching_df['loans.down_payment_percent'].iloc[0])):
                potential_discrepancy['Down Payment %'] = {
                    'document_value': down_payment_percent_doc,
                    'dataframe_value': int(matching_df['loans.down_payment_percent'].iloc[0])
                }
        except Exception as e:
            potential_discrepancy['Down Payment %'] = {
                'document_value': "",
                'dataframe_value': matching_df['loans.down_payment_percent'].iloc[0]
            }

    except Exception as e:
        not_located.append('Down Payment | %')

    return potential_discrepancy, not_located

def loan_terms():
    global potential_discrepancy, not_located

    # Loan Terms
    term_pattern = r"mature (\d+) years"
    interest_only_pattern = r"(\d+) months of interest only"
    term_after_io_pattern = r"followed by (\d+) principal and interest payments"
    term_no_io_pattern = r"(\d+) principal and interest payments"
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

        # Attempt to find the pattern in the text
        interest_only_match = re.search(interest_only_pattern, content['Loan terms'])

        # Check if a match is found
        if interest_only_match:
            interest_only_doc = interest_only_match.group(1)
        else:
            interest_only_doc = None

        if int(matching_df['loans.interest_only_period'].iloc[0]) > 0 or interest_only_doc is not None:

            if int(interest_only_doc) != int(matching_df['loans.interest_only_period'].iloc[0]):
                potential_discrepancy['Loan Terms (IO Period)'] = {
                    'document_value': interest_only_doc,
                    'dataframe_value': matching_df['loans.interest_only_period'].iloc[0]
                }

        else:
            pass
    except Exception as e:
        not_located.append('Loan Terms (IO Period)')
    try:
        if int(matching_df['loans.interest_only_period'].iloc[0]) > 0 or interest_only_doc is not None:
            term_after_io_doc = re.search(term_after_io_pattern, content['Loan terms']).group(1)
            term_after_io_df = int(
                matching_df['loans.term'].iloc[0] - matching_df['loans.interest_only_period'].iloc[0])

            if int(term_after_io_doc) != term_after_io_df:
                potential_discrepancy['Loan Terms (Term After IO Period)'] = {
                    'document_value': term_after_io_doc,
                    'dataframe_value': term_after_io_df
                }
        else:
            term_no_io_doc = re.search(term_no_io_pattern, content['Loan terms']).group(1)
            term_after_io_df = int(
                matching_df['loans.term'].iloc[0] - matching_df['loans.interest_only_period'].iloc[0])

            if int(term_no_io_doc) != term_after_io_df:
                potential_discrepancy['Loan Terms (Term After IO Period)'] = {
                    'document_value': term_no_io_doc,
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
        if float(interest_rate_doc) != float(platform_df['approved_rate_in_commit_letter'].iloc[0]):
            potential_discrepancy['Interest Rate'] = {
                'document_value': interest_rate_doc,
                'dataframe_value': platform_df['approved_rate_in_commit_letter'].iloc[0]
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
        if float(spread_doc) != float(matching_df['loans.commitment_letter_spread_rate'].iloc[0]):
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

    if not content['Important Ratios']:
        not_located.append('Important Ratios')
    else:
        try:
            projected_gdscr_doc = re.search(projected_gdscr, content['Important Ratios']).group(1)
            if float(projected_gdscr_doc) != float(matching_df['loans.global_dscr'].iloc[0]):
                potential_discrepancy['Important Ratios(GDSCR)'] = {
                    'document_value': projected_gdscr_doc,
                    'dataframe_value': matching_df['loans.global_dscr'].iloc[0]
                }
        except Exception as e:
            not_located.append('Important Ratios(GDSCR)')
        try:
            projected_dscr_doc = re.search(projected_dscr, content['Important Ratios']).group(1)
            if float(projected_dscr_doc) != float(matching_df['loans.dscr_y2_dcr'].iloc[0]):
                potential_discrepancy['Important Ratios(DSCR)'] = {
                    'document_value': projected_dscr_doc,
                    'dataframe_value': matching_df['loans.dscr_y2_dcr'].iloc[0]
                }
        except Exception as e:
            not_located.append('Important Ratios(DSCR)')
        try:
            projected_fccr_doc = re.search(projected_fccr, content['Important Ratios']).group(1)
            if float(projected_fccr_doc) != float(matching_df['loans.y2_fixed_charge_coverage_ratio'].iloc[0]):
                potential_discrepancy['Important Ratios(FCCR)'] = {
                    'document_value': projected_fccr_doc,
                    'dataframe_value': matching_df['loans.y2_fixed_charge_coverage_ratio'].iloc[0]
                }
        except Exception as e:
            not_located.append('Important Ratios(FCCR)')
        try:
            projected_debt_to_ebitda_doc = re.search(projected_debt_to_ebitda, content['Important Ratios']).group(1)
            if float(projected_debt_to_ebitda_doc) != float(matching_df['loans.debt_to_ebitda'].iloc[0]):
                potential_discrepancy['Important Ratios(Debt-EBITDA)'] = {
                    'document_value': projected_debt_to_ebitda_doc,
                    'dataframe_value': matching_df['loans.debt_to_ebitda'].iloc[0]
                }
        except Exception as e:
            not_located.append('Important Ratios(Debt-EBITDA)')
        try:
            projected_lease_adjusted_debt_to_ebitda_doc = re.search(projected_lease_adjusted_debt_to_ebitda,
                                                                    content['Important Ratios']).group(1)
            if float(platform_df['financed_ti_allowance'].iloc[0]) > 0:
                if float(projected_lease_adjusted_debt_to_ebitda_doc) != float(
                        matching_df['net_rent_adjusted_debt_to_ebitdar_1'].iloc[0]):
                    potential_discrepancy['Important Ratios(Projected Lease-Adjusted Debt-to EBITDAR)'] = {
                        'document_value': projected_lease_adjusted_debt_to_ebitda_doc,
                        'dataframe_value': matching_df['net_rent_adjusted_debt_to_ebitdar_1'].iloc[0]
                    }
            else:
                pass
        except Exception as e:
            not_located.append('Important Ratios(Projected Lease-Adjusted Debt-to EBITDAR)')

    return potential_discrepancy, not_located
    # Net of TIs (Excluding TIs)

def fico_results():
    global potential_discrepancy, not_located

    pattern = r'([A-Za-z]+ [A-Za-z]+)\s*(?:[-–,])\s*(\d{3})'

    try:

        # Find all matches in the text
        matches = re.findall(pattern, content['FICO Results'])

        # Extract names and FICO scores
        fico_doc = {match[0].upper(): match[1] for match in matches}

        filtered_df = matching_df[(matching_df['guarantor_data.ownership_percentage'].notnull()) & (
                matching_df['guarantor_data.entity_type'] == 'individual')]

        fico_df = {}




        # Loop over the rows of filtered_df and construct the dictionary entry for each individual
        for index, row in filtered_df.iterrows():
            name = row['guarantor_data.guarantor_first_name'].upper() + " " + row['guarantor_data.guarantor_last_name'].upper()
            fico_df[name] = row['guarantor_fico']

        counter = 1
        for name, fico_score in fico_df.items():
            if name in fico_doc:
                if fico_doc[name] != fico_score:

                    potential_discrepancy['Fico Results'+ str(counter)] = {
                        'document_value': name + ':' + str(fico_doc[name]),
                        'dataframe_value': name + ':' + str(fico_score)
                    }

                counter += 1

            else:
                not_located.append('FICO Results' + '(' + (name) + ')')

    except Exception as e:
        not_located.append('FICO Results')

    return potential_discrepancy, not_located

def acr_pcv_pcr():
    global potential_discrepancy, not_located
    # Also ACR and PCR
    net_worth = r"net\s*worth\s*is\s*[$]?([\d,]+)"
    asset_coverage_ratio = r"Asset\s*Coverage\s*Ratio\s*([\d]+\.[\d]+)"
    personal_collateral_value = r"Personal\s*Collateral\s*Value\s*(?:is\s*\$)?([\d,]+)"
    personal_collateral_ratio = r"Collateral\s*Ratio\s*([\d]+\.[\d]+)"

    #removing ()
    net_worth_parse = content['Total Ownership Net  Worth / ACR / PCV /  PCR']
    net_worth_cleaned = re.sub(r'\([^()]*\)', '', net_worth_parse)

    try:
        net_worth_doc = re.search(net_worth, net_worth_cleaned).group(
            1).replace(',', '').replace(" ", "").upper()

        if int(net_worth_doc) != int(platform_df['total_owner_net_worth'].iloc[0]):
            potential_discrepancy['Net Worth'] = {
                'document_value': net_worth_doc,
                'dataframe_value': int(platform_df['total_owner_net_worth'].iloc[0])
            }
    except Exception as e:
        not_located.append('Net Worth')
    try:
        asset_coverage_ratio_doc = re.search(asset_coverage_ratio,net_worth_cleaned).group(1)

        if str(asset_coverage_ratio_doc) != str(matching_df['loans.acr'].iloc[0]):
            potential_discrepancy['ACR'] = {
                'document_value': asset_coverage_ratio_doc,
                'dataframe_value': matching_df['loans.acr'].iloc[0]
            }
    except Exception as e:
        not_located.append('ACR')
    try:
        personal_collateral_value_doc = re.search(personal_collateral_value,net_worth_cleaned).group(
            1).replace(',', '')
        if int(personal_collateral_value_doc) != int(matching_df['loans.total_personal_collateral_value'].iloc[0]):
            potential_discrepancy['Personal Collateral Value'] = {
                'document_value': personal_collateral_value_doc,
                'dataframe_value': matching_df['loans.total_personal_collateral_value'].iloc[0]
            }
    except Exception as e:
        not_located.append('Personal Collateral Value')
    try:
        personal_collateral_ratio_doc = re.search(personal_collateral_ratio,net_worth_cleaned).group(1)

        if str(personal_collateral_ratio_doc) != str(platform_df['asset_coverage_personal_collateral_value'].iloc[0]):
            potential_discrepancy['PCR'] = {
                'document_value': personal_collateral_ratio_doc,
                'dataframe_value': platform_df['asset_coverage_personal_collateral_value'].iloc[0]
            }
    except Exception as e:
        not_located.append('PCR')
    return potential_discrepancy, not_located

def liquidity():
    global potential_discrepancy, not_located

    pattern = r'\$([0-9,]+)'
    pattern_capital = r'working capital coverage ratio (\d+)'

    try:
        # Find all matches in the text
        matches = re.findall(pattern, content['Liquidity'])

        total_liquidity_required = int(matches[0].replace(',', ''))
        post_down_liquidity = int(matches[1].replace(',', ''))



        if total_liquidity_required != int(platform_df['liquidity_required_6_month_expenses'].iloc[0]):
            potential_discrepancy['Liquidity'] = {
                'document_value': total_liquidity_required,
                'dataframe_value': int(platform_df['liquidity_required_6_month_expenses'].iloc[0])
            }
    except Exception as e:
        not_located.append('Liquidity')

    try:
        if post_down_liquidity != int(platform_df['post_down_liquidity'].iloc[0]):
            potential_discrepancy['Liquidity'] = {
                'document_value': post_down_liquidity,
                'dataframe_value': int(platform_df['post_down_liquidity'].iloc[0])
            }
    except Exception as e:
        not_located.append('Liquidity')


    try:
        # Find all matches in the text
        matches_capital = re.findall(pattern_capital, content['Liquidity'])

        capital_coverage_ratio = int(matches_capital[0].replace(',', ''))

        if capital_coverage_ratio != int(platform_df['y2_fixed_charge_coverage_months'].iloc[0]):
            potential_discrepancy['Liquidity - Capital coverage Ratio'] = {
                'document_value': capital_coverage_ratio,
                'dataframe_value': int(platform_df['y2_fixed_charge_coverage_months'].iloc[0])
            }
    except Exception as e:
        not_located.append('Liquidity - Capital Cover Ratio')

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
