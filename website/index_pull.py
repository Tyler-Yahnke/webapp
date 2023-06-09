import pymysql
from datetime import date
from datetime import datetime
from pandas.tseries.offsets import BDay
import requests

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
        url = "https://ondemand.websol.barchart.com/getQuote.json?apikey=f662dbbcc2a45be5307136cb8e74da08&symbols=SWAEADY3.RT, SWAEADY5.RT, WSJPRIME.RT"

        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)

        for symbols in response.json()['results']:
            if symbols['symbol'] == 'SWAEADY3.RT':
                swap_3year = symbols['lastPrice']
                date_3year_str = symbols['tradeTimestamp']

            elif symbols['symbol'] == 'SWAEADY5.RT':
                swap_5year = symbols['lastPrice']

        swap_4year = round((swap_3year + swap_5year), 4) / 2

        swap_date = datetime.strptime(date_3year_str, '%Y-%m-%dT%H:%M:%S%z').date()
        swap_date_str = swap_date.strftime('%Y-%m-%d')
        new_vals = [swap_date_str, "{:.2%}".format(swap_3year), "{:.2%}".format(swap_4year), "{:.2%}".format(swap_5year)]

        sql = """
                INSERT INTO ebdb.swap_rate (`Date`, `3Year`,`4Year`,`5Year`)
                VALUES (%s, %s, %s, %s)
            """
        cursor.execute(sql, new_vals)
        connection.commit()

        print('swap index updates end')

    else:
        print('swap pass')
        pass


    ####Prime Check

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
        new_prime_vals = [prime_date_str, "{:.2%}".format(prime_rate)]

        sql = """
                    INSERT INTO ebdb.prime_rate (`Date`,`Rate`)
                    VALUES (%s, %s)
                """


        cursor.execute(sql, new_prime_vals)
        connection.commit()

        print('prime update end')

    else:
        print('Prime Pass')
        pass

    # Close the cursor and connection
    cursor.close()
    connection.close()


