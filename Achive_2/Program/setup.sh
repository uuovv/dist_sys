#!/bin/bash

sudo apt-get update;
sudo apt-get install python3-venv python3-pip libpq-dev;
sudo apt install python3-venv python3-pip libpq-dev;
sudo pip install --upgrade pip;

python3 -m venv venv;
