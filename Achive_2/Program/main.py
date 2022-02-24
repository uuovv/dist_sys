import os
import psycopg as pg3
import socket
import json
from conf_db import dbname, user, db_host, db_port
from conf_server import HDRS, server_host, server_port, socket_size

#-------------------------------------------------------------------------------------
def main():
    create_db(dbname, user, db_host, db_port)
    create_table(dbname, user, db_host, db_port)

    server = create_server(server_host, server_port)
    try:
        while True: 
            client_socket, address = server.accept()
            http_num = resive_data(client_socket, socket_size)
            db_num = get_number(dbname, user, db_host, db_port)
            
            print('Полученное число: {}; Число в базе: {}'.format(http_num, db_num))
        
            insert_f, content = condition(http_num, db_num)
            
            if insert_f:
                insert_to_table(http_num, dbname, user, db_host, db_port)
                send_data(client_socket, content)
            else:
                send_data(client_socket, content)
                
            print(content)
    except KeyboardInterrupt:
        print('Сервер отключен по вашей просьбе.')
    except:
        print('Произошла неизвестная ошибка.')
    finally:
        server.close()    

#-------------------------------------------------------------------------------------

def create_db(dbname, user, db_host, db_port):
    with pg3.connect(user=user, host=db_host, port=db_port, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    SELECT datname FROM pg_database;
                        ''')
    
            db_list = cur.fetchall()
            conn.commit()
    
            if (dbname,) not in db_list:
                cur.execute('''
                    CREATE DATABASE achive_2;
                            ''')
    conn.close()    


def create_table(dbname, user, db_host, db_port):
    with pg3.connect(dbname=dbname, user=user, host=db_host, port=db_port) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    CREATE TABLE IF NOT EXISTS nums (
                        id serial NOT NULL PRIMARY KEY,
                        num int NOT NULL
                        );
                        ''')            
    conn.close()

def get_number(dbname, user, db_host, db_port):
    with pg3.connect(dbname=dbname, user=user, host=db_host, port=db_port) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    SELECT n1.num
                    FROM nums n1
                    WHERE n1.id = (SELECT MAX(n2.id) FROM nums n2);
                        ''' )            
            number = cur.fetchone()
    conn.close()

    if type(number) == type(None):
        return number
    else:
        return number[0]

def insert_to_table(num, dbname, user, db_host, db_port):
    with pg3.connect(dbname=dbname, user=user, host=db_host, port=db_port) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                        INSERT INTO nums (num)
                        VALUES
                        (%s);
                        ''', (num,))            
            conn.commit()
    conn.close()

def create_server(server_host, server_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_host, server_port))
    server.listen(5)
    return server

def resive_data(client_socket, socket_size):
    data = client_socket.recv(socket_size).decode('utf-8').split('\r\n')[-1]
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
