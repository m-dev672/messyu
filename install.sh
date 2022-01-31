#!/bin/bash
mkdir /etc/messyu

curl -sfL -o /usr/local/bin/messyu.py https://github.com/m-dev672/messyu/releases/download/v0.0.0-alpha/messyu.py
chmod 755 /usr/local/bin/messyu.py

curl -sfL -o /etc/systemd/system/messyu.service https://github.com/m-dev672/messyu/releases/download/v0.0.0-alpha/messyu.service
systemctl daemon-reload
systemctl enable messyu.service
