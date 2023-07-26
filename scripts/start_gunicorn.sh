#!/bin/bash --login
cd /home/ubuntu/webapp
source venv/bin/activate
gunicorn -D --pid tmp/pids/server.pid --access-logfile logs/gunicorn.log --error-logfile logs/gunicorn.log -b 0.0.0.0:5000 application:application

