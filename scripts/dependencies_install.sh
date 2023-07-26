#!/bin/bash --login
cd /home/ubuntu/webapp
python3 -m venv venv
source venv/bin/activate
pip3  install -r requirements.txt
pip3  install gunicorn
mkdir logs
mkdir tmp
mkdir tmp/pids
