#!/bin/bash --login
cd /home/ubuntu/webapp
source venv/bin/activate
pip3  install -r requirements.txt
mkdir logs
mkdir tmp/pids
