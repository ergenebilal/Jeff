#!/bin/bash
# Restore DOCKER-USER chain rules after reboot
# Generated: 2026-08-17
iptables -F DOCKER-USER 2>/dev/null
iptables -I DOCKER-USER 1 -p tcp --dport 8000 -j DROP
iptables -I DOCKER-USER 1 -p tcp --dport 8090 -j DROP
iptables -I DOCKER-USER 1 -p tcp --dport 8642 -j DROP
iptables -I DOCKER-USER 1 -p tcp --dport 6001 -j DROP
iptables -I DOCKER-USER 1 -p tcp --dport 6002 -j DROP
iptables -I DOCKER-USER 1 -p tcp --dport 8765 -j DROP
iptables -I DOCKER-USER 1 -p tcp --dport 8767 -j DROP
echo "$(date -Iseconds) DOCKER-USER rules restored" >> /home/hermes/jeff2/reports/optimization/iptables-restore.log
