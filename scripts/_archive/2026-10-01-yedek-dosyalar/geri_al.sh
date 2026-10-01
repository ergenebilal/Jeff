#!/bin/bash
# Arşivden geri alma — 01.10.2026
set -e
A="$(dirname "$0")"
mkdir -p "$(dirname '/home/hermes/.hermes/scripts/autonomous-health-check.sh.bak.20260820')" && cp -p "$A/scripts__autonomous-health-check.sh.bak.20260820" '/home/hermes/.hermes/scripts/autonomous-health-check.sh.bak.20260820'
mkdir -p "$(dirname '/home/hermes/.hermes/scripts/alfred_tool.py.bak-pre-webop')" && cp -p "$A/scripts__alfred_tool.py.bak-pre-webop" '/home/hermes/.hermes/scripts/alfred_tool.py.bak-pre-webop'
mkdir -p "$(dirname '/home/hermes/.hermes/scripts/gateway-healthcheck.sh.bak-20260905')" && cp -p "$A/scripts__gateway-healthcheck.sh.bak-20260905" '/home/hermes/.hermes/scripts/gateway-healthcheck.sh.bak-20260905'
mkdir -p "$(dirname '/home/hermes/.hermes/scripts/start_gateway.sh.bak-20260908')" && cp -p "$A/scripts__start_gateway.sh.bak-20260908" '/home/hermes/.hermes/scripts/start_gateway.sh.bak-20260908'
mkdir -p "$(dirname '/home/hermes/jeff_repo/scripts/autonomous-health-check.sh.bak.20260820')" && cp -p "$A/scripts__autonomous-health-check.sh.bak.20260820.1" '/home/hermes/jeff_repo/scripts/autonomous-health-check.sh.bak.20260820'
mkdir -p "$(dirname '/home/hermes/jeff_repo/scripts/system_watchdog.py.bak-20260930-093724')" && cp -p "$A/scripts__system_watchdog.py.bak-20260930-093724" '/home/hermes/jeff_repo/scripts/system_watchdog.py.bak-20260930-093724'
mkdir -p "$(dirname '/home/hermes/jeff_repo/scripts/alfred_tool.py.bak-pre-webop')" && cp -p "$A/scripts__alfred_tool.py.bak-pre-webop.1" '/home/hermes/jeff_repo/scripts/alfred_tool.py.bak-pre-webop'
mkdir -p "$(dirname '/home/hermes/jeff_repo/scripts/morning_report.py.bak-20260930-100100')" && cp -p "$A/scripts__morning_report.py.bak-20260930-100100" '/home/hermes/jeff_repo/scripts/morning_report.py.bak-20260930-100100'
mkdir -p "$(dirname '/home/hermes/jeff_repo/scripts/gateway-healthcheck.sh.bak-20260905')" && cp -p "$A/scripts__gateway-healthcheck.sh.bak-20260905.1" '/home/hermes/jeff_repo/scripts/gateway-healthcheck.sh.bak-20260905'
mkdir -p "$(dirname '/home/hermes/jeff_repo/scripts/start_gateway.sh.bak-20260908')" && cp -p "$A/scripts__start_gateway.sh.bak-20260908.1" '/home/hermes/jeff_repo/scripts/start_gateway.sh.bak-20260908'
