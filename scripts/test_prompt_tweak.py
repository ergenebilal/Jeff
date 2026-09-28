import asyncio, json, sys
sys.path.insert(0, '/opt/hermes')
import telegram_claude_bot as bot

async def run(prompt, extra_sys=''):
    sys_p = bot.SYSTEM_PROMPT + '\n' + extra_sys
    msgs = [{'role': 'system', 'content': sys_p}, {'role': 'user', 'content': prompt}]
    res = await bot.call_antigravity(msgs)
    msg = res['choices'][0]['message']
    print('PROMPT:', prompt)
    print('EXTRA_SYS:', repr(extra_sys))
    print('CONTENT:', msg.get('content'))
    print('TOOL_CALLS:', [tc['function']['name'] for tc in (msg.get('tool_calls') or [])])
    print('-'*50)

async def main():
    await run('Ekran görüntüsü al.', 'Kullanıcı doğrudan bir eylem istediğinde (ekran görüntüsü al, dosya aç vb.) selamlama yapmadan hemen ilgili toolu çağır.')
    await run('Windows masaüstü ekran görüntüsü al.')

asyncio.run(main())
