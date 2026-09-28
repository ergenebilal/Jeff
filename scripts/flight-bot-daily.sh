#!/bin/bash
# Ucak Bileti Botu v3 — Apify Flight Price Scraper
# Her gun 08:00'da calisir. 7 kaynaktan fiyat ceker.
# Gidis-donus fiyatlar (subat sonu → nisan/mayis 2027)

cd /opt/hermes/flight-bot
exec /usr/bin/python3 main.py 2>&1
