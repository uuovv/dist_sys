import os
import psycopg as pg3
import socket
import json

dbname = os.environ['dbname']
db_user = os.environ['db_user']
db_host = os.environ['db_host']
db_port = int(os.environ['db_port'])
db_password = os.environ['db_password']

HDRS = 'http/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n'
server_host = os.environ['server_host']
server_port = int(os.environ['server_port'])
socket_size = int(os.environ['socket_size'])

#-------------------------------------------------------------------------------------

def main():
    create_db(dbname, db_user, db_host, db_port, db_password)
    create_table(dbname, db_user, db_host, db_port, db_password)

    server = create_server(server_host, server_port)
    try:
        while True: 
            client_socket, address = server.accept()
            http_num = resive_data(client_socket, socket_size)
            db_num = get_number(dbname, db_user, db_host, db_port, db_password)
            
            print('Полученное число: {}; Число в базе: {}'.format(http_num, db_num))
        
            insert_f, content = condition(http_num, db_num)
            
            if insert_f:
                insert_to_table(http_num, dbname, db_user, db_host, db_port, db_password)
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

def create_db(dbname, db_user, db_host, db_port, db_password):
    with pg3.connect(user=db_user, host=db_host, port=db_port, 
                    password=db_password, autocommit=True) as conn:
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


def create_table(dbname, db_user, db_host, db_port, db_password):
    with pg3.connect(dbname=dbname, user=db_user, host=db_host, 
                    port=db_port, password=db_password) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    CREATE TABLE IF NOT EXISTS nums (
                        id serial NOT NULL PRIMARY KEY,
                        num int NOT NULL
                        );
                        ''')            
    conn.close()

def get_number(dbname, db_user, db_host, db_port, db_password):
    with pg3.connect(dbname=dbname, user=db_user, host=db_host, 
                    port=db_port, password=db_password) as conn:
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

def insert_to_table(num, dbname, db_user, db_host, db_port, db_password):
    with pg3.connect(dbname=dbname, user=db_user, host=db_host, 
                    port=db_port, password=db_password) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                        INSERT INTO nums (num)
                        VALUES
                        (%s);
                        ''', (num,))            
            conn.commit()
    conn.close()

#-------------------------------------------------------------------------------------

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
