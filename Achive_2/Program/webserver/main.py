import os
import psycopg as pg3
import socket
import json

DBNAME = os.environ['DBNAME']
DB_USER = os.environ['DB_USER']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_PASSWORD = os.environ['DB_PASSWORD']

HDRS = 'http/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n'
SERVER_HOST = os.environ['SERVER_HOST']
SERVER_PORT = int(os.environ['SERVER_PORT'])
SOCKET_SIZE = int(os.environ['SOCKET_SIZE'])

#-------------------------------------------------------------------------------------

def main():
    create_db(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD)
    create_table(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD)

    server = create_server(SERVER_HOST, SERVER_PORT)
    try:
        while True: 
            client_socket, address = server.accept()
            http_num = resive_data(client_socket, SOCKET_SIZE)
            db_num = get_number(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD)
            
            print('Полученное число: {}; Число в базе: {}'.format(http_num, db_num))
        
            insert_f, content = condition(http_num, db_num)
            
            if insert_f:
                insert_to_table(http_num, DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD)
                send_data(client_socket, content)
            else:
                send_data(client_socket, content)
                
            print(content)
    except KeyboardInterrupt:
        print('Сервер отключен по вашей просьбе.')
    except Exception as e: 
        print('Произошла ошибка.\n{}'.format(e))
    finally:
        server.close()    

#-------------------------------------------------------------------------------------

def create_db(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD):
    with pg3.connect(dbname=DBNAME, user=DB_USER, host=DB_HOST, port=DB_PORT, 
                    password=DB_PASSWORD, autocommit=True) as conn:
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


def create_table(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD):
    with pg3.connect(dbname=DBNAME, user=DB_USER, host=DB_HOST, 
                    port=DB_PORT, password=DB_PASSWORD) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    CREATE TABLE IF NOT EXISTS numbers (
                        id serial NOT NULL PRIMARY KEY,
                        num int NOT NULL
                        );
                        ''')            
    conn.close()

def get_number(DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD):
    with pg3.connect(dbname=DBNAME, user=DB_USER, host=DB_HOST, 
                    port=DB_PORT, password=DB_PASSWORD) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    SELECT n1.num
                    FROM numbers n1
                    WHERE n1.id = (SELECT MAX(n2.id) FROM numbers n2);
                        ''' )            
            number = cur.fetchone()
    conn.close()

    if type(number) == type(None):
        return number
    else:
        return number[0]

def insert_to_table(num, DBNAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD):
    with pg3.connect(dbname=DBNAME, user=DB_USER, host=DB_HOST, 
                    port=DB_PORT, password=DB_PASSWORD) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                        INSERT INTO numbers (num)
                        VALUES
                        (%s);
                        ''', (num,))            
            conn.commit()
    conn.close()

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

def condition(http_num, db_num):
    if ((db_num == None and http_num >= 0) or
        (http_num != db_num and http_num != db_num - 1 and http_num >= 0)):
        insert_f = True
        content = 'Результат обработки числа: {}\n\r'.format(http_num+1)
    else:
        insert_f = False
        if http_num < 0:
            content = 'Ошибка: Число должно быть больше или равно 0.\n\r' 
        elif http_num != db_num - 1:
            content = 'Ошибка: Число уже было обработано.\n\r'
        elif http_num != db_num:
            content = 'Ошибка: Число меньше обработанного числа на 1.\n\r'
    
    return (insert_f, content)

#-------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
