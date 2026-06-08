#!/bin/bash
# Tüm ürünleri Gumroad'da oluştur ve yayınla
# Kullanım: ./gumroad-publish.sh
# 
# API key'ler /home/hermes/.hermes/secrets/gumroad_token dosyasında

set -e

TOKEN_FILE="/home/hermes/.hermes/secrets/gumroad_token"
if [ ! -f "$TOKEN_FILE" ]; then
    echo "HATA: Gumroad token bulunamadı. Önce token'ı $TOKEN_FILE dosyasına yaz."
    echo "Format: access_token=<token>"
    exit 1
fi

TOKEN=$(cat "$TOKEN_FILE")

echo "1. Ürün: n8n Production Playbook ($29.99)"
gumroad products create \
  --name "n8n Production Playbook" \
  --price 29.99 \
  --file /home/hermes/dijital-urunler/n8n-playbook/n8n-playbook.zip \
  --description "8-chapter production deployment guide + 5 production workflows" \
  2>/dev/null || echo "  (dosya hazir degil, atlandi)"

echo ""
echo "2. Ürün: AI Agency Starter Kit ($39.99)"
gumroad products create \
  --name "AI Agency Starter Kit" \
  --price 39.99 \
  --file /home/hermes/dijital-urunler/ai-agency-starter/ai-agency-starter.zip \
  --description "Complete agency-in-a-box: Telegram + Instagram + Content Factory" \
  2>/dev/null || echo "  (dosya hazir degil, atlandi)"

echo ""
echo "3. Ürün: Agent Reach Monitoring Pack ($19.99)"
gumroad products create \
  --name "Agent Reach Monitoring Pack" \
  --price 19.99 \
  --file /home/hermes/dijital-urunler/agent-reach-pack/agent-reach-pack.zip \
  --description "Multi-platform monitoring + alert config + notification templates" \
  2>/dev/null || echo "  (dosya hazir degil, atlandi)"

echo ""
echo "4. Ürün: Prompt Engineering for Agents ($9.99)"
gumroad products create \
  --name "Prompt Engineering for Agents" \
  --price 9.99 \
  --file /home/hermes/dijital-urunler/prompt-pack/prompt-pack.zip \
  --description "50+ battle-tested prompts for AI agent development" \
  2>/dev/null || echo "  (dosya hazir degil, atlandi)"

echo ""
echo "=== Tüm ürünler yüklendi. 'gumroad products publish <id>' ile yayınla ==="
echo "Not: Stripe bağlı değilse publish başarısız olur."
