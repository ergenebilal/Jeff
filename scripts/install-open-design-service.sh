#!/bin/bash
sleep 3
sudo cp /opt/open-design/open-design-daemon.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable open-design-daemon
sudo systemctl start open-design-daemon
sleep 2
systemctl status open-design-daemon --no-pager | head -10
