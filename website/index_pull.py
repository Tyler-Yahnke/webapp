import pymysql
from datetime import datetime, date
from pandas.tseries.offsets import BDay
import requests
from flask_mail import Message
from flask import current_app
from . import mail
import json
from bs4 import BeautifulSoup

def index_rate_updates():
    # Connect to the database
    connection = pymysql.connect(
        host='awseb-e-rvvktpucyf-stack-awsebrdsdatabase-ijbluxt9ye2s.cavhriuewzv4.us-east-1.rds.amazonaws.com',
        user='ebroot',
        password='Yamaha189!',
        database='ebdb',
        cursorclass=pymysql.cursors.DictCursor  # Optional: Return results as dictionaries
    )

    # Create a cursor
    cursor = connection.cursor()

    # Execute SQL queries
    sql = "SELECT * FROM ebdb.swap_rate order by Date desc"
    cursor.execute(sql)

    # Grabbing First Row
    row = cursor.fetchone()

    #Setting Previous Business Day
    prev_Biz_Day = date.today() - BDay(1)
    formatted_dt = prev_Biz_Day.strftime('%Y-%m-%d')

    if row and str(row['Date']) != formatted_dt:
        print('index updates begin')
        url = "https://ondemand.websol.barchart.com/getQuote.json?apikey=f662dbbcc2a45be5307136cb8e74da08&symbols=SOFWAPY3.RT, SOFWAPY5.RT, WSJPRIME.RT"

        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)

        for symbols in response.json()['results']:
            if symbols['symbol'] == 'SOFWAPY3.RT':
                swap_3year = symbols['lastPrice']
                date_3year_str = symbols['tradeTimestamp']

            elif symbols['symbol'] == 'SOFWAPY5.RT':
                swap_5year = symbols['lastPrice']

        # Round the values
        swap_3year = round(swap_3year * 10000) / 10000
        swap_5year = round(swap_5year * 10000) / 10000

        swap_4year = round((swap_3year + swap_5year), 4) / 2


        swap_date = datetime.strptime(date_3year_str, '%Y-%m-%dT%H:%M:%S%z').date()
        swap_date_str = swap_date.strftime('%Y-%m-%d')
        new_vals = [swap_date_str, "{:.2%}".format(swap_3year), "{:.2%}".format(swap_4year), "{:.2%}".format(swap_5year),datetime.today()]


        sql = """
                INSERT INTO ebdb.swap_rate (`Date`, `3Year`,`4Year`,`5Year`,Created_Date)
                VALUES (%s, %s, %s, %s, %s)
            """
        cursor.execute(sql, new_vals)
        connection.commit()

        print('swap index updates end')

    else:
        print('swap pass')
        pass



    # Create a cursor
    cursor = connection.cursor()

    # Execute SQL queries
    sql = "SELECT * FROM ebdb.prime_rate order by Date desc"
    cursor.execute(sql)

    # Grabbing First Row
    row = cursor.fetchone()

    if row and str(row['Date']) != formatted_dt:
        print('Prime updates begin')
        url = "https://ondemand.websol.barchart.com/getQuote.json?apikey=f662dbbcc2a45be5307136cb8e74da08&symbols=SWAEADY3.RT, SWAEADY5.RT, WSJPRIME.RT"

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        for symbols in response.json()['results']:
            if symbols['symbol'] == 'WSJPRIME.RT':
                prime_rate = symbols['lastPrice']
                prime_rate_str = symbols['tradeTimestamp']


        prime_date = datetime.strptime(prime_rate_str, '%Y-%m-%dT%H:%M:%S%z').date()
        prime_date_str = prime_date.strftime('%Y-%m-%d')
        new_prime_vals = [prime_date_str, "{:.2%}".format(prime_rate),datetime.today()]

        sql = """
                    INSERT INTO ebdb.prime_rate (`Date`,`Rate`,Created_Date)
                    VALUES (%s, %s, %s)
                """


        cursor.execute(sql, new_prime_vals)
        connection.commit()


    else:
        print('Prime Pass')
        pass

    # Close the cursor and connection
    cursor.close()
    connection.close()


def index_rate_verification():

    #web scraping barchart to get rate from website
    URL1 = 'https://www.barchart.com/stocks/quotes/SOFWAPY3.RT/price-history/historical'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}

    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    for a in soup.findAll('a', attrs={'class': 'set-alerts-link'}):
        attributes = a.attrs
    raw_price = json.loads(attributes['data-symbol'])['lastPrice']





    # Connect to the database
    connection = pymysql.connect(
        host='awseb-e-rvvktpucyf-stack-awsebrdsdatabase-ijbluxt9ye2s.cavhriuewzv4.us-east-1.rds.amazonaws.com',
        user='ebroot',
        password='Yamaha189!',
        database='ebdb',
        cursorclass=pymysql.cursors.DictCursor  # Optional: Return results as dictionaries
    )

    # Create a cursor
    cursor = connection.cursor()

    # Execute SQL queries
    sql = "SELECT * FROM ebdb.swap_rate order by Date desc"
    cursor.execute(sql)

    # Grabbing First Row
    swap_row = cursor.fetchone()

    sql = "SELECT * FROM ebdb.prime_rate order by Date desc"
    cursor.execute(sql)

    # Grabbing First Row
    prime_row = cursor.fetchone()

    # Setting Previous Business Day
    prev_Biz_Day = date.today() - BDay(1)
    formatted_dt = prev_Biz_Day.strftime('%Y-%m-%d')
    formatted_rate = f"{swap_row['3Year']}%"


    if swap_row and str(swap_row['Date']) != formatted_dt or prime_row and str(prime_row['Date']) != formatted_dt:
        msg = Message('Index Rate not Updated', sender='passwordreset@apcratecard.com',
                      recipients=['tyler.yahnke@applepiecapital.com'])
        msg.body = 'Index Rate is not up to date. Verify if Index Rate is inaccurate in the database.'


        mail.send(msg)

    # adding logic to check if website and api match
    elif raw_price != formatted_rate:
        msg = Message('Index Rate does not match Barchart website', sender='passwordreset@apcratecard.com',
                      recipients=['tyler.yahnke@applepiecapital.com'])
        msg.body = 'Index Rate does not match Barchart website. Verify if Index Rate is inaccurate in the database.'

        mail.send(msg)


    else:
        pass

    # Close the cursor and connection
    cursor.close()
    connection.close()