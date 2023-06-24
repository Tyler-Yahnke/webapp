from flask import Blueprint, render_template, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from . import db
from docx import Document
from openpyxl import load_workbook
import openpyxl
import os
import tempfile
from datetime import datetime

doc_generator = Blueprint('doc_generator', __name__)


@doc_generator.route('/', methods=['GET', 'POST'])
@login_required
def doc_generation():
    if request.method == 'POST':
        button = request.form.get('generate_docs')
        if button == 'Generate Docs':
            excel_file = request.files['excel-file']
            word_file = request.files['word-file']
            if excel_file and word_file:
                # Save the uploaded files temporarily
                excel_path = os.path.join(tempfile.gettempdir(), 'uploaded_excel.xlsx')
                word_path = os.path.join(tempfile.gettempdir(), 'uploaded_word.docx')
                excel_file.save(excel_path)
                word_file.save(word_path)

                # Open the Excel spreadsheet
                wb = openpyxl.load_workbook(excel_path)
                sheet = wb.active

                # Get the column names from the first row in the spreadsheet
                column_names = [cell.value for cell in sheet[1]]

                # Iterate through each row in the spreadsheet
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    # Create a new instance of the Document class for each row
                    doc = Document(word_path)

                    # Replace placeholders in the Word document with data from the current row
                    for paragraph in doc.paragraphs:
                        for column_name in column_names:
                            placeholder = f"{{{column_name}}}"  # Format the placeholder with curly braces
                            if placeholder in paragraph.text:
                                column_index = column_names.index(column_name)
                                column_value = row[column_index]
                                # Check if the column value is a date
                                if isinstance(column_value, datetime):
                                    # Convert the date to "mm-dd-yyyy" format
                                    formatted_date = column_value.strftime('%m-%d-%Y')
                                    column_value = formatted_date
                                paragraph.text = paragraph.text.replace(placeholder, str(column_value))

                    # Save the populated Word document for each row and Word document
                    name = row[0]  # Assuming the first column contains a unique identifier
                    output_dir = os.path.expanduser("~/Desktop")  # Get the user's desktop directory
                    output_path = os.path.join(output_dir,
                                               f'{name}_{os.path.basename(word_path)}.docx')  # Specify the output file path
                    doc.save(output_path)

                # Close the Excel spreadsheet
                wb.close()

                # Clean up the temporary files
                os.remove(excel_path)
                os.remove(word_path)

                # Send a flash message indicating success
                flash('Documents generated successfully', category='success')

                # Return the rendered template
                return render_template("doc_generator.html", user=current_user)
            else:
                # Send a flash message indicating success
                flash('Missing Document', category='error')
                return render_template("doc_generator.html", user=current_user)

    # Render the template if not a POST request or button is not pressed
    return render_template("doc_generator.html", user=current_user)


