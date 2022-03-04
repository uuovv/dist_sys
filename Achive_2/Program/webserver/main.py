import  os
import psycopg as pg3
import socket
import json
from time import sleep

DBNAME = os.environ['DBNAME']
DB_USER = os.environ['DB_USER']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_PASSWORD = os.environ['DB_PASSWORD']

HDRS = 'http/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n'
SERVER_HOST = os.environ['SERVER_HOST']
SERVER_PORT = int(os.environ['SERVER_PORT'])
SOCKET_SIZE = int(os.environ['SOCKET_SIZE'])

WAIT_S = int(os.environ['WAIT_S'])

#-------------------------------------------------------------------------------------

def main():
    create_db(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S)
    create_table(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S)

    server = create_server(SERVER_HOST, SERVER_PORT)
    try:
        while True: 
            client_socket, address = server.accept()
            http_num = resive_data(client_socket, SOCKET_SIZE)
            condition = check_condition(http_num, DBNAME, DB_USER, 
                                        DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S)
            
            print('http_num: {};'.format(http_num))
        
            insert_f, content = condition_processing(http_num, condition)
            
            if insert_f:
                insert_to_table(http_num, DBNAME, DB_USER, 
                                DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S)
                send_data(client_socket, content)
            else:
                send_data(client_socket, content)
                
            print(content)
    except KeyboardInterrupt:
        print('Server turned off.')
    except Exception as e: 
        print('Exception\n{}'.format(e))
    finally:
        server.close()    

#-------------------------------------------------------------------------------------

def create_db(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S):
    conn = wait_until_connect(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S)
    with conn.cursor() as cur:
        cur.execute('''
            SELECT datname FROM pg_database;
                    ''')
    
        db_list = cur.fetchall()
        conn.commit()
    
        if (DBNAME,) not in db_list:
            cur.execute('''
                CREATE DATABASE achive_2;
                        ''')
    conn.close()    


def create_table(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S):
    conn = wait_until_connect(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S)
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS numbers (
                id serial NOT NULL PRIMARY KEY,
                num int NOT NULL
                );
                    ''')            
    conn.close()

def check_condition(http_num, DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S):
    conn = wait_until_connect(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S)
    with conn.cursor() as cur:
        cur.execute('''
            SELECT SUM(
                CASE WHEN num={0} THEN 1
                    WHEN num={1} THEN 2
                    ELSE 0
                    END)
                FROM numbers;
                    '''.format(http_num, http_num+1))            
        condition = cur.fetchone()
    conn.close()

    return condition[0]

def insert_to_table(num, DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S):
    conn = wait_until_connect(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S)
    with conn.cursor() as cur:
        cur.execute('''
            INSERT INTO numbers (num)
            VALUES
            (%s);
                    ''', (num,))            
        conn.commit()
    conn.close()

def wait_until_connect(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD, WAIT_S):
    while True:
        try:
            conn = pg3.connect(dbname=DBNAME, user=DB_USER, host=DB_HOST, 
                            port=DB_PORT, password=DB_PASSWORD)
            break
        except pg3.errors.OperationalError: 
            sleep(WAIT_S)
    return conn
    
#-------------------------------------------------------------------------------------

def create_server(SERVER_HOST, SERVER_PORT):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    return server

def resive_data(client_socket, SOCKET_SIZE):
    data = client_socket.recv(SOCKET_SIZE).decode('utf-8').split('\r\n')[-1]
    num = json.loads(data)['num']
    return num

def send_data(client_socket, content):
    client_socket.send(HDRS.encode('utf-8') + content.encode('utf-8'))
    client_socket.shutdown(socket.SHUT_WR)

def condition_processing(http_num, condition):
    if (condition == 0 and http_num >= 0):
        insert_f = True
        content = 'Result of processing the http_num: {}\n\r'.format(http_num+1)
    else:
        insert_f = False
        if http_num < 0:
            content = 'Error: The number must be greater than or equal to 0.\n\r' 
        elif (condition == 1 or condition == 3):
            content = 'Error: The number has already been processed.\n\r'
        elif condition == 2:
            content = 'Error: The number is less than the processed number by 1.\n\r'
    
    return (insert_f, content)

#-------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
