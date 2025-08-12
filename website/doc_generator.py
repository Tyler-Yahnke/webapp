from flask import Blueprint, render_template, request, flash, send_file, make_response
from flask_login import login_required, current_user
from . import db
import pandas as pd
import looker_sdk  # access looker objects
import json
from looker_sdk import methods40, models40
from docx import Document
from datetime import datetime, timedelta
import os
import tempfile

doc_generator = Blueprint('doc_generator', __name__)


@doc_generator.route('/', methods=['GET', 'POST'])
@login_required
def doc_generation():

    previous_data = {}


    if request.method == 'POST':
        button = request.form.get('generate_docs')
        if button == 'Generate Doc':

            user_selection_lai = request.form.get('lai')
            user_selection_nod_type = request.form.get('nod_type')

            previous_data = {
                'lai': user_selection_lai,
                'nod_type': user_selection_nod_type
            }

            if user_selection_lai == "":
                # Render the template if not a POST request or button is not pressed
                flash('LAI Required', category='error')
                return render_template("doc_generator.html", user=current_user, previous_data=previous_data)
            elif user_selection_nod_type =='Make Selection':
                flash('NOD Type Required', category='error')
                return render_template("doc_generator.html", user=current_user, previous_data=previous_data)
            else:
                pass




                # connecting to looker and pulling data
            # Initialize Looker API client
            looker_loc = 'looker.ini'
            sdk = looker_sdk.init40(looker_loc)

            def df_creator(query):
                slug = sdk.create_sql_query(body=models40.SqlQueryCreate(connection_name='apc_slave', sql=query)).slug
                result = sdk.run_sql_query(slug=slug, result_format='json')
                data = json.loads(result)
                df = pd.DataFrame.from_dict(data)

                return df

            #content_value = data.get('LAI')  - Might use this if I want to loop through a big list
            #for lai in content_value:




            query = f"""
            select distinct e.id,
            b.business_name,
            b.cl_contract,
            sf.closedate as funded_date,
            b.Interest_rate,
            e.name,
            e.entity_type, 
            go.guarantor_type,
            go.ownership_percentage,
            e.email, 
            add_borrower.address1 as borrower_address,
            add_borrower.city as borrower_city,
            add_borrower.state as borrower_state, 
            add_borrower.zip_code as borrower_zip_code,
            add_guarantor.address1 as guarantor_address,
            add_guarantor.city as guarantor_city,
            add_guarantor.state as guarantor_state, 
            add_guarantor.zip_code as guarantor_zip_code

            from 
                loans b 
            left join 
                guarantor_ownerships go ON  b.id = go.loan_id
            left join 
                borrower_entity_ownerships d ON b.legal_entity_id = d.legal_entity_id
            LEFT JOIN
                legal_entities e ON go.legal_entity_id = e.id
            LEFT JOIN 
                addresses add_borrower ON d.legal_entity_id = add_borrower.addressable_id AND add_borrower.addressable_type = 'LegalEntity'
            LEFT JOIN 
                addresses add_guarantor ON e.id = add_guarantor.addressable_id AND add_guarantor.addressable_type = 'LegalEntity'
            LEFT JOIN
                salesforce.opportunity sf ON b.opportunity_id = sf.sfid
            LEFT JOIN
                salesforce.user u ON sf.ownerid = u.sfid

            where 1=1
            AND b.cl_contract LIKE '%{user_selection_lai}'
            group by
            e.id,b.business_name,
            b.cl_contract,
            b.Interest_rate,
            e.name,
            e.entity_type, 
            go.guarantor_type,
            go.ownership_percentage,
            e.email, 
            borrower_address,
            borrower_city,
            borrower_state, 
            borrower_zip_code,
            guarantor_address,
            guarantor_city,
            guarantor_state, 
            guarantor_zip_code,
            sf.closedate
            """

            # Read in from Looker with query
            platform_df = df_creator(query)
            if platform_df.empty:
                return render_template("doc_generator.html", user=current_user, previous_data=previous_data)
            else:
                filtered_df = platform_df[platform_df['entity_type'] == 'individual']

            ##creating header
            # borrower header
            borrower_header = f"""
            {platform_df['business_name'].iloc[0]} (“Borrower”)
            {platform_df['borrower_address'].iloc[0]}
            {platform_df['borrower_city'].iloc[0]}, {platform_df['borrower_state'].iloc[0]}, {platform_df['borrower_zip_code'].iloc[0]}
            {platform_df[(platform_df['entity_type'] == 'individual') & (platform_df['guarantor_type'] == 0)]['email'].iloc[0]}
            """
            ##Personal guarantor header
            guarantor_blocks = []

            for index, row in platform_df[platform_df['entity_type'] == 'individual'].iterrows():
                # Extract information for the current borrower
                borrower_name = row['name']
                borrower_address = row['guarantor_address']
                borrower_city = row['guarantor_city']
                borrower_state = row['guarantor_state']
                borrower_zip_code = row['guarantor_zip_code']
                borrower_email = row['email']

                # Create the header block for the current borrower
                header_block = f"""
            {borrower_name} (“Personal Guarantor”)
            {borrower_address}
            {borrower_city}, {borrower_state}, {borrower_zip_code}
            {borrower_email}"""
                # Append the header block to the list
                guarantor_blocks.append(header_block)

            # Join all header blocks into a single string
            Personal_Guarantor_header = '\n'.join(guarantor_blocks)

            ##Corp guarantor header
            corp_guarantor_blocks = []

            for index, row in platform_df[platform_df['entity_type'] != 'individual'].iterrows():
                # Extract information for the current borrower
                borrower_name = row['name']
                borrower_address = row['guarantor_address']
                borrower_city = row['guarantor_city']
                borrower_state = row['guarantor_state']
                borrower_zip_code = row['guarantor_zip_code']
                borrower_email = row['email']

                # Create the header block for the current borrower
                header_block = f"""{borrower_name} (“Corporate Guarantor”)
            {borrower_address}
            {borrower_city}, {borrower_state}, {borrower_zip_code}
            {borrower_email}"""
                # Append the header block to the list
                corp_guarantor_blocks.append(header_block)

            # Join all header blocks into a single string
            Corporate_Guarantor_header = '\n'.join(corp_guarantor_blocks)

            combined_header = borrower_header + Personal_Guarantor_header + Corporate_Guarantor_header

            # creating word doc
            current_date = datetime.now().strftime("%m-%d-%Y")
            #current_date = "03/13/2025"
            header = combined_header
            lai = platform_df['cl_contract'].iloc[0]
            personal_corporate_list = ', '.join(platform_df['name'])
            personal_list = ', '.join(filtered_df['name'])
            rate_increase = str((platform_df['interest_rate'].iloc[0]) + 2)
            effective_date = (datetime.now() + timedelta(days=30)).strftime("%m-%d-%Y")
            funded_date = platform_df['funded_date'].iloc[0]
            ##Missing Tax Returns
            #covenant = 'Failure of Obligor to provide annual federal tax returns, exception made for documented extension (Section: 4.02)'

            #Ownership Structure Change
            #covenant = 'Failure to provide notice of change in ownership structure (Section: 4.03(d))'

            #Annual Monitoring
            covenant = 'Failure to provide year-end financial statements (Section: 4.01(a)(i))'

            pm_dict = {
                "Matin Torabian": {
                    "title": "Portfolio Manager",
                    "email": "Matin.Torabian@applepiecapital.com"
                },
                "Destine Alexander": {
                    "title": "Portfolio Manager",
                    "phone_number": "(415) 539-1640",
                    "email": "Destine.Alexander@applepiecapital.com"
                },
                "Christine Martinski": {
                    "title": "Portfolio Manager",
                    "phone_number": "(415) 930-4450",
                    "email": "Christine.Martinski@applepiecapital.com"
                },
                "Katie Spencer": {
                    "title": "Portfolio Manager",
                    "phone_number": "(415)707-3731",
                    "email": "Katie.Spencer@applepiecapital.com"
                }
            }

            #portfolio_manager = platform_df['portfolio_manager'].iloc[0]

            pm_signature = f"""
            Christine Martinski|Portfolio Manager
            ApplePie Capital Mailing 
            Address: 548 Market Street, PMB 54105, San Francisco, CA 94104 - 5401
            E: christine.martinski@applepiecapital.com|P:(415) 930-4450
        """

            borrower_signature = f"""{platform_df['business_name'].iloc[0]}
            By: ___________________
            Name: _________________
            Title: __________________
            """

            ##Corporate guarantor signature block
            corp_signature_blocks = []
            for borrower in platform_df[platform_df['entity_type'] != 'individual']['name']:
                Corp_Guarantor_Signature_separate = f"""{borrower}
                By: ___________________
                Name: _________________
                Title: __________________
                """
                # Append the signature block to the list
                corp_signature_blocks.append(Corp_Guarantor_Signature_separate)

            Corporate_Guarantor_Signature = '\n'.join(corp_signature_blocks)

            ##Personal guarantor signature block
            signature_blocks = []
            for borrower in platform_df[platform_df['entity_type'] == 'individual']['name']:
                Personal_Guarantor_Signature_separate = f"""By:____________________
            {borrower}, an individual

                """
                # Append the signature block to the list
                signature_blocks.append(Personal_Guarantor_Signature_separate)

            Personal_Guarantor_Signature = '\n'.join(signature_blocks)

            # Read the Word document
            if user_selection_nod_type == 'Covenant Default':
                doc = Document("NOD Covenant Default Tech Version.docx")
            elif user_selection_nod_type == 'Payment Defualt':
                doc = Document("NOD Template Payment Default Tech Version.docx")

            # Loop through the paragraphs in the document
            for paragraph in doc.paragraphs:
                # Replace placeholders with values from the DataFrame
                paragraph.text = paragraph.text.replace("{Current_Date}", current_date)
                paragraph.text = paragraph.text.replace("{funded_date}", funded_date)
                paragraph.text = paragraph.text.replace("{header}", header)
                paragraph.text = paragraph.text.replace("{LAI}", lai)
                paragraph.text = paragraph.text.replace("{personal_corporate_list}", personal_corporate_list)
                paragraph.text = paragraph.text.replace("{personal_list}", personal_list)
                paragraph.text = paragraph.text.replace("{rate_increase}", rate_increase)
                paragraph.text = paragraph.text.replace("{pm_signature}", pm_signature)
                paragraph.text = paragraph.text.replace("{Borrower_Signature}", borrower_signature)
                paragraph.text = paragraph.text.replace("{Corporate_Guarantor_Signature}",
                                                        Corporate_Guarantor_Signature)
                paragraph.text = paragraph.text.replace("{Personal_Guarantor_Signature}",
                                                        Personal_Guarantor_Signature)
                paragraph.text = paragraph.text.replace("{covenant}",covenant)


            # Remove {} from the document
            for paragraph in doc.paragraphs:
                paragraph.text = paragraph.text.replace("{", "").replace("}", "")

            # Create a temporary file path
            temp_dir = tempfile.gettempdir()
            filename = f"NOD_{platform_df['cl_contract'].iloc[0]}.docx"
            temp_filepath = os.path.join(temp_dir, filename)

            # Save to a temporary file
            doc.save(temp_filepath)
            print(f"Saved document at: {temp_filepath}")  # Debugging output

            # Return the file for download
            return send_file(temp_filepath, as_attachment=True, download_name=filename)

        else:
            # Send a flash message indicating missing documents
            flash('Missing Document', category='error')
            return render_template("doc_generator.html", user=current_user, previous_data=previous_data)

    # Render the template if not a POST request or button is not pressed
    return render_template("doc_generator.html", user=current_user, previous_data=previous_data)


def download_file(filename):
    """Send the generated Word document as a downloadable attachment."""
    return send_file(filename,
                     as_attachment=True,
                     download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")