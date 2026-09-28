import asyncio, json, sys
sys.path.insert(0, '/opt/hermes')
import telegram_claude_bot as bot

async def t():
    msgs = [{'role': 'system', 'content': bot.SYSTEM_PROMPT}, {'role': 'user', 'content': 'Ekran görüntüsü al.'}]
    res = await bot.call_antigravity(msgs)
    msg = res['choices'][0]['message']
    print('CONTENT:', msg.get('content'))
    print('TOOL_CALLS:', msg.get('tool_calls'))

asyncio.run(t())
