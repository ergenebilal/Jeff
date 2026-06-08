#!/bin/bash
# ErgeneAI One-Click Setup
# "Zero to AI Agent" kitabı için tek komutla kurulum
# Kullanım: curl -fsSL https://ergene.ai/install-agent.sh | bash

set -e

echo "============================================"
echo "  ErgeneAI Agent Kurulumu"
echo "  Zero to AI Agent - Bolum 2"
echo "============================================"
echo ""

# Root kontrol
if [ "$(id -u)" = "0" ]; then
    echo "[!] Root yetkisiyle calistiriliyor..."
fi

# 1. Sistem paketleri
echo "[1/5] Sistem paketleri guncelleniyor..."
apt-get update -qq
apt-get install -y -qq curl git python3 python3-pip python3-venv > /dev/null 2>&1
echo "  OK"

# 2. Hermes Agent
echo "[2/5] Hermes Agent kuruluyor..."
cd /opt
if [ -d "hermes-agent" ]; then
    echo "  Hermes zaten kurulu, guncelleniyor..."
    cd hermes-agent && git pull
else
    git clone https://github.com/NousResearch/hermes-agent.git
    cd hermes-agent
fi
python3 -m venv venv
source venv/bin/activate
pip install -e . -q
echo "  OK - hermes CLI hazir"

# 3. Temel MCP Server'lar
echo "[3/5] MCP server'lar yapilandiriliyor..."
mkdir -p ~/.hermes/mcp-servers

# Time MCP
hermes config set mcp_servers/time/command python3 -q 2>/dev/null || true

# Fetch MCP (web scraping)
hermes config set mcp_servers/fetch/command python3 -q 2>/dev/null || true

# Git MCP
hermes config set mcp_servers/git/command python3 -q 2>/dev/null || true

echo "  OK"

# 4. Baslangic yapilandirmasi
echo "[4/5] Baslangic ayarlari..."
echo ""
echo "  Asagidaki bilgileri girmeniz gerekiyor:"
echo ""
read -p "  Agent adi (ornek: Jeff): " AGENT_NAME
hermes config set agent_name "$AGENT_NAME" -q
echo "  OK"

# 5. Dogrulama
echo "[5/5] Dogrulama..."
echo ""
hermes --version 2>/dev/null && echo "  HERMES: calisiyor" || echo "  HERMES: HATA"
echo ""
echo "============================================"
echo "  KURULUM TAMAMLANDI"
echo "============================================"
echo ""
echo "  API key'lerinizi girmek icin:"
echo "  hermes config set provider openai"
echo "  hermes config set api_key YOUR_KEY"
echo ""
echo "  Detayli rehber: PDF'in Chapter 2 bolumunde"
echo "============================================"
