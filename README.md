# webapp
This is a web application built in Flask. It handles complex pricing strategies, user authentication, doc generation, doc/database validation, and automated task handling

auth.py = Handles all user login, password reset and new user setup. Creates secret keys for password changes and hashes information before being put into DB
cm_validation.py = Tons of REGEX. User uploads a document and the program scans the document and parses the info. It then pull info from a DB and does a compare against the doc. It then displays all discrepancies to the user
doc_geneartor = User uploads an excel doc and word doc and then this loops through the excel doc replacing specific fields in the word doc and then saves each word doc for the user
fees.py = Static text displaying information for the users
index_pull.py = Automated validation and updates being done to update the database. Completes API calls and updates the DB
models.py = Flask models to link with DB
views.py = Complicated pricing strategy for determine rates
init.py = Base setup for flask. Handles scheduling to perform tasks at specific times. Links with mail server to send emails and database to send and return data. 
