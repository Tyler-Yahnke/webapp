#!/bin/bash --login
cd /home/ubuntu/webapp
if [ -f tmp/pids/server.pid ]
then
  kill $(cat tmp/pids/server.pid)
else
  echo 'Server pid does not exist' > logs/no_pid.log
fi

