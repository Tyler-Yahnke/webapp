#!/bin/bash 

# Remove previous deployment folder
rm -rf /home/ubuntu/prev-deployment

# Backup current deployment
mv /home/ubuntu/webapp /home/ubuntu/prev-deployment

# Create new deployment folder and make owner as ubuntu
mkdir /home/ubuntu/webapp && chown ubuntu:ubuntu /home/ubuntu/webapp
