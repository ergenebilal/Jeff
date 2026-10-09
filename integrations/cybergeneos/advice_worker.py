"""Private child: existing Jeff prompt/provider, SDK call once, no agent loop."""
from contextlib import redirect_stdout,redirect_stderr
from copy import deepcopy
from pathlib import Path
import io,json,os,subprocess,sys,time
_attempts=0

def main():
    global _attempts
    sys.dont_write_bytecode=True
    sys.path[:0]=['/home/hermes/cybergeneos/docs/cybergeneos','/home/hermes/jeff-v0.21.5/live_ext','/home/hermes/jeff-v0.21.5/src','/home/hermes/jeff-v0.21.5/site','/home/hermes/.local/lib/python3.11/site-packages']
    raw=sys.stdin.read(50001)
    if len(raw)>50000:raise ValueError()
    request=json.loads(raw)
    if set(request)!={'packet','expected'}:raise ValueError()
    expected=request['expected'];packet=request['packet']
    if expected['answer_scope']!='selected_task_only' or any(expected[k] is not False for k in expected if k not in ('answer_scope','task_outcome')):raise ValueError()
    os.environ['TERMINAL_CWD']='/home/hermes/jeff_repo'
    with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
        pid=subprocess.check_output(['systemctl','show','hermes-gateway.service','-p','MainPID','--value'],text=True).strip()
        environment=dict(item.split('=',1) for item in Path('/proc/'+pid+'/environ').read_bytes().decode().split('\0') if '=' in item)
        if 'OPENCODE_GO_API_KEY' in environment:os.environ['OPENCODE_GO_API_KEY']=environment['OPENCODE_GO_API_KEY']
        from gateway.run import _resolve_runtime_agent_kwargs,_resolve_gateway_model
        from run_agent import AIAgent
        from agent.system_prompt import build_system_prompt
        from server import jeff
        runtime=_resolve_runtime_agent_kwargs()
        if runtime.pop('_fallback_notice',None):raise RuntimeError('primary_unavailable')
        model=runtime.pop('model',None) or _resolve_gateway_model()
        agent=AIAgent(model=model,**runtime,enabled_toolsets=[],platform='api_server',quiet_mode=True,
            verbose_logging=False,fallback_model=None,reasoning_config={'effort':'low'})
        system=build_system_prompt(agent)
        agent.max_tokens=1200
        body=deepcopy(packet)
        if set(body)!={'trusted_user_request','untrusted_panel_data'}:raise ValueError()
        body['untrusted_panel_data']['reply_field_observations']=expected
        body['trusted_user_request']+='\nYalnız seçilen işi değerlendir. Başka işlerin sonucu veya kalıcı öğrenme çıkarmayacağız. Araç, yürütme veya hafıza yazımı yok. JSON nesnesi ver: answer_scope, task_outcome, source_current_truth_verified, permanent_rule_saved, permanent_memory_write_authorized, execution_authorized, reexecution_authorized, customer_delivery_verified, rationale. İlk sekiz alanı reply_field_observations program gözlemiyle aynen koru; rationale kısa Türkçe değerlendirmen olsun, bilinmeyeni söyle; gözlemi dış iş başarısı veya kaynak doğruluğu sayma.'
        kwargs=agent._build_api_kwargs([{'role':'system','content':system+'\n'+jeff.DATA_RULES},
            {'role':'user','content':json.dumps(body,ensure_ascii=False)}])
        kwargs.pop('tools',None);kwargs.pop('tool_choice',None);kwargs.pop('parallel_tool_calls',None)
        client=agent.client.with_options(max_retries=0,timeout=45)
        _attempts=1;response=client.chat.completions.create(**kwargs)
    choice=response.choices[0]
    return dict(status='completed',raw_answer=choice.message.content,finish_reason=choice.finish_reason,
        requested_tool_calls=len(choice.message.tool_calls or []),provider_calls=1,agent_loop_run=False,
        tool_execution_invoked=False,provider_retries=0,model=model)

if __name__=='__main__':
    try:result=main()
    except Exception as exc:result=dict(status='unavailable',error_kind=type(exc).__name__,private_detail_omitted=True)
    result['provider_request_attempts']=_attempts
    print(json.dumps(result,ensure_ascii=False))
