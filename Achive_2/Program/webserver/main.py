import os
import psycopg as pg3
from flask import Flask, request, jsonify
import logging
from time import sleep

DBNAME = os.environ['DBNAME']
DB_USER = os.environ['DB_USER']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_PASSWORD = os.environ['DB_PASSWORD']

SERVER_HOST = os.environ['SERVER_HOST']
SERVER_PORT = int(os.environ['SERVER_PORT'])
WAIT_S = int(os.environ['WAIT_S'])

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def main():
    try:
        http_num = resive_data()
        conn = wait_until_connect(DBNAME, DB_USER, DB_HOST,
                                DB_PORT, DB_PASSWORD, WAIT_S)
        condition = check_condition(conn, http_num)
        insert_f, content = condition_processing(http_num, condition)

        if insert_f:
            insert_to_table(conn, http_num)

        conn.close()
        logging.debug(f'end of request.\r\n')
        return content
    except (Exception, pg3.errors.ConnectionTimeout) as err:
        logging.debug(f'Error: {err}')
        return f"Error: {err}\r\n"
    finally:
        if "conn" in locals():
            if conn is not None:
                conn.close()

#-------------------------------------------------------------------------------------

def resive_data():
    if request.method == 'POST':
        data = request.get_json()
    num = int(data['num'])

    logging.debug(f'resive_data: OK')
    logging.debug(f'data: {data}')

    return num

def condition_processing(http_num, condition):
    if ((condition == None) and (http_num != None and http_num >= 0)):
        insert_f = True
        content = jsonify({'num': http_num+1})
    else:
        insert_f = False
        if http_num == None:
            content = 'Error: Incorrect input data.\r\n'
        elif http_num < 0:
            content = 'Error: The number must be greater than or equal to 0.\r\n' 
        elif (condition == 1 or condition == 3):
            content = 'Error: The number has already been processed.\r\n'
        elif condition == 2:
            content = 'Error: The number is less than the processed number by 1.\r\n'

    logging.debug(f'condition_processing: OK')
    logging.debug(f'insert_f: {insert_f}')

    content_log = content
    if not insert_f:
        content_log = content[:-2]

    logging.debug(f'content: {content_log}')

    return (insert_f, content)

#-------------------------------------------------------------------------------------

def check_condition(conn, http_num):
    if (http_num != None and http_num >= 0):
        with conn.cursor() as cur:
            cur.execute('''
                SELECT SUM(
                CASE WHEN num={0} THEN 1
                    WHEN num={1} THEN 2
                    END)
                FROM numbers;
                        '''.format(http_num, http_num+1))            
            condition = cur.fetchone()
        logging.debug('check_condition: OK')
        return condition[0]
    else:
        logging.debug('check_condition: OK')
        return None

def insert_to_table(conn, num):
    with conn.cursor() as cur:
        cur.execute('''
                    INSERT INTO numbers (num)
                    VALUES
                    (%s);
                    ''', (num,))            
        conn.commit()
    logging.debug('insert_to_table: OK')

def wait_until_connect(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S):
    while True:
        try:
            conn = pg3.connect(dbname=DBNAME, user=DB_USER, host=DB_HOST, 
                            port=DB_PORT, password=DB_PASSWORD, connect_timeout=WAIT_S)
            logging.debug('wait_until_connect: OK')
            break
        except pg3.errors.OperationalError: 
            sleep(WAIT_S)
            logging.debug('wait_until_connect: NOT OK')
    return conn

#-------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host=SERVER_HOST, port=SERVER_PORT)