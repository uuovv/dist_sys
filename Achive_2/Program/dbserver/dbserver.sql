DROP DATABASE IF EXISTS achive_2;
DROP USER IF EXISTS web_server;

CREATE USER web_server WITH PASSWORD 'achive_2';
CREATE DATABASE achive_2 WITH OWNER web_server;

\c achive_2 web_server

CREATE TABLE IF NOT EXISTS numbers (
    id serial NOT NULL PRIMARY KEY,
    num int NOT NULL
    );