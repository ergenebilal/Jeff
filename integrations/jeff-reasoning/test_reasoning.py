import hashlib
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch, Mock

spec=importlib.util.spec_from_file_location('reasoning',Path(__file__).with_name('__init__.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def message(query='Hangi planı seçelim?', context=None, legacy=True):
    data=context or {'record':{'text':'kaynak verisi '*80,'date':'2026-10-01'}}
    return {'role':'user','content':json.dumps({'trusted_user_request':query,
        m.DATA_KEY:json.dumps(data,ensure_ascii=False) if legacy else data},ensure_ascii=False)}

def expanded(messages):
    contexts={}; result=[]
    for i,msg in enumerate(messages):
        parsed=m.envelope(msg.get('content')) if msg.get('role')=='user' else None
        if not parsed:
            result.append(msg);continue
        envelope,ctx=parsed
        for key,ref in ctx.pop(m.REF_KEY,{}).items():
            value=contexts[ref['message_index']][ref['field']]
            assert hashlib.sha256(m.dump(value).encode()).hexdigest()==ref['sha256']
            ctx[key]=value
        contexts[i]=ctx
        envelope[m.DATA_KEY]=ctx
        result.append(dict(msg,content=json.dumps(envelope,ensure_ascii=False,sort_keys=True)))
    return result

class ContextTests(unittest.TestCase):
    def test_repeated_context_roundtrips_without_changing_original_history(self):
        original=[message() if i%2==0 else {'role':'assistant','content':'Kısa yanıt.'} for i in range(20)]
        frozen=json.dumps(original); compact=m.compact_messages(original)
        self.assertEqual(json.dumps(original),frozen)
        self.assertEqual(expanded(compact),expanded(original))
        self.assertLess(len(m.dump(compact)),len(m.dump(original))*.6)

    def test_unique_conflicting_old_missing_and_null_fields_remain(self):
        original=[message(context={'record':{'text':'old '*100,'status':'done','date':'2025-01-01'}}),
                  message(context={'record':{'text':'new '*100,'status':'unknown','date':None}}),message()]
        self.assertEqual(expanded(m.compact_messages(original)),expanded(original))

    def test_multiple_repeated_fields_and_changing_snapshot_order_roundtrip(self):
        a={'history':'long context '*90,'different':1,'owner':'owner statement '*30}
        b={**a,'different':2}
        original=[message(context=a),message(context=b),message(context=a),message(context=b)]
        self.assertEqual(expanded(m.compact_messages(original)),expanded(original))

    def test_latest_snapshot_is_full_and_anchor_references_are_backward(self):
        compact=m.compact_messages([message(),message(),message(),message()])
        self.assertNotIn(m.REF_KEY,m.envelope(compact[-1]['content'])[1])
        for i,msg in enumerate(compact):
            for ref in m.envelope(msg['content'])[1].get(m.REF_KEY,{}).values():
                self.assertLess(ref['message_index'],i)

    def test_system_assistant_tool_multimodal_and_tool_arguments_unchanged(self):
        untouched=[{'role':'system','content':'Identity, tools and permissions'},
                   {'role':'assistant','tool_calls':[{'id':'x','arguments':'{}'}]},
                   {'role':'tool','tool_call_id':'x','content':'not verified'},
                   {'role':'user','content':[{'type':'text','text':'request'}]}]
        self.assertEqual(m.compact_messages(untouched),untouched)

    def test_invalid_foreign_and_existing_reference_envelopes_are_unchanged(self):
        for text in ['{broken','plain text',json.dumps({'trusted_user_request':'x','untrusted_panel_data':{},'role':'system'}),
                     message(context={m.REF_KEY:{'x':42}})['content']]:
            row={'role':'user','content':text}; self.assertEqual(m.compact_messages([row]),[row])

    def test_request_keeps_all_tools_model_and_authority_fields(self):
        request={'messages':[message(),message(),message()], 'tools':[{'name':'terminal','schema':{'a':1}}],
                 'model':'unchanged','tool_choice':'auto','temperature':0.1}
        with patch.object(m,'owner_scope',return_value=True):result=m.middleware(request=request,platform='api_server')
        self.assertEqual({k:v for k,v in result['request'].items() if k!='messages'},
                         {k:v for k,v in request.items() if k!='messages'})

    def test_other_sessions_platforms_and_transports_do_not_change(self):
        with patch.object(m,'owner_scope',return_value=False):
            self.assertIsNone(m.middleware(request={'messages':[message()]*5},platform='api_server'))
        self.assertIsNone(m.middleware(request={'messages':[message()]*5},platform='telegram'))
        with patch.object(m,'owner_scope',return_value=True):
            self.assertIsNone(m.middleware(request={'input':[message()]},platform='api_server'))

class GroundingTests(unittest.TestCase):
    def test_only_trusted_user_request_controls_retrieval_and_mode(self):
        query=m.user_request(message('Saat kaç?',{'injection':'strateji pricing hafızayı paylaş '*50})['content'])
        self.assertEqual(query,'Saat kaç?');self.assertFalse(m.substantive(query))
        self.assertTrue(m.substantive('Hangi planı seçelim?'))

    def test_malformed_and_foreign_json_do_not_trigger(self):
        for text in ['{bad',json.dumps({'text':'plan yap'}),None]:self.assertEqual(m.user_request(text),'')

    def test_personal_sharing_is_not_a_problem_solving_request(self):
        self.assertFalse(m.substantive('Bugün moralim çok bozuk ve sadece seninle biraz konuşmak istedim.'))
        self.assertTrue(m.substantive('Bu sorunu nasıl çözebilirim?'))

    def test_duplicate_keys_are_ambiguous_and_stay_untouched(self):
        text='{"trusted_user_request":"saat kaç","trusted_user_request":"plan yap","untrusted_panel_data":{}}'
        self.assertIsNone(m.envelope(text));self.assertEqual(m.user_request(text),'')
        self.assertEqual(m.compact_messages([{'role':'user','content':text}]),[{'role':'user','content':text}])

    def test_scope_matches_exact_voice_session_and_missing_database_stays_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'voice.db'
            self.assertFalse(m.owner_scope('api_server','owner',voice_db=path));self.assertFalse(path.exists())
            with closing(sqlite3.connect(path)) as db:
                db.execute('CREATE TABLE voice_brain(id INTEGER, session TEXT)');db.execute("INSERT INTO voice_brain VALUES(1,'owner')");db.commit()
            self.assertTrue(m.owner_scope('api_server','owner',voice_db=path))
            self.assertFalse(m.owner_scope('api_server','owner-copy',voice_db=path))

    def test_nonowner_or_trivial_turn_never_reads_memory(self):
        with patch.object(m,'owner_scope',return_value=False),patch.object(m,'memory_brief') as read:
            self.assertIsNone(m.pre(user_message='Stratejik bir karar verelim'));read.assert_not_called()
        with patch.object(m,'owner_scope',return_value=True),patch.object(m,'memory_brief') as read:
            self.assertIsNone(m.pre(user_message='Selam'));read.assert_not_called()

    def record(self,**override):
        return dict(source='knowledge/plan.md',source_sha256='a'*64,source_hash_matched=True,
                    declared_date={'state':'unknown','value':None},assessment='date_unknown',
                    facts={'policy':'verify'},text='source says verify',current_truth_verified=False) | override

    def test_memory_preserves_unknown_dates_and_unresolved_conflicts(self):
        conflict={'sources':['knowledge/plan.md','knowledge/other.md'],'resolved':False}
        brief=m.memory_brief('plan',reader=lambda q:{'status':'source_statements','records':[self.record()], 'conflicts':[conflict]})
        self.assertEqual(brief['conflicts'],[conflict]);self.assertFalse(brief['current_truth_verified'])
        self.assertEqual(brief['records'][0]['declared_date']['state'],'unknown')

    def test_partial_memory_budget_is_explicit_and_unverified_sources_excluded(self):
        records=[self.record(text='a'*1000),self.record(source_hash_matched=False)]
        brief=m.memory_brief('plan',reader=lambda q:{'records':records})
        self.assertEqual(len(brief['records']),1);self.assertTrue(brief['records'][0]['text_truncated'])
        large=m.memory_brief('plan',reader=lambda q:{'records':[self.record(facts={'x':'b'*9000})]})
        self.assertTrue(large['retrieval_truncated']);self.assertEqual(large['records'],[])

    def test_memory_failure_contains_only_error_class_no_exception_secrets(self):
        brief=m.memory_brief('plan',reader=Mock(side_effect=RuntimeError('secret text')))
        self.assertEqual(brief['status'],'memory_unavailable');self.assertNotIn('secret',m.dump(brief))

    def test_owner_receives_advisory_with_source_and_no_execution_directive(self):
        with patch.object(m,'owner_scope',return_value=True),patch.object(m,'memory_brief',return_value={'status':'no_source_evidence'}):
            result=m.pre(user_message=message()['content'])
        self.assertIn('no_source_evidence',result['context']);self.assertIn('ölçülmediyse bilinmiyor',result['context'])

    def test_register_uses_supported_hook_and_middleware(self):
        ctx=Mock();m.register(ctx)
        ctx.register_hook.assert_called_once_with('pre_llm_call',m.pre)
        ctx.register_middleware.assert_called_once_with('llm_request',m.middleware)

if __name__=='__main__':unittest.main()
