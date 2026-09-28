#!/bin/bash
# Model geçisi icin config'i direkt duzenle
# Not: JSON string yazmaz, YAML dict formatinda yazar

ACTION="${1:-gemini}"

if [ "$ACTION" = "deepseek" ]; then
  python3 -c "
import re
with open('/home/hermes/.hermes/config.yaml', 'r') as f:
    c = f.read()
# Replace model section
c = re.sub(r'model:.*?(?=\n\w|\Z)', '''model:
  provider: deepseek
  base_url: https://api.deepseek.com/v1
  default: deepseek-v4-flash''', c, flags=re.DOTALL)
with open('/home/hermes/.hermes/config.yaml', 'w') as f:
    f.write(c)
"
  echo "-> DeepSeek V4 Flash"
elif [ "$ACTION" = "gemini" ]; then
  python3 -c "
import re
with open('/home/hermes/.hermes/config.yaml', 'r') as f:
    c = f.read()
c = re.sub(r'model:.*?(?=\n\w|\Z)', '''model:
  provider: harici-provider
  base_url: https://harici-provider.ai/api/v1
  default: google/gemini-3.5-flash''', c, flags=re.DOTALL)
with open('/home/hermes/.hermes/config.yaml', 'w') as f:
    f.write(c)
"
  echo "-> Gemini 3.5 Flash (harici LLM provider)"
else
  echo "Kullanim: $0 [deepseek|gemini]"
  exit 1
fi

echo "Gateway'i yeniden baslatmak icin: sudo systemctl restart hermes"
