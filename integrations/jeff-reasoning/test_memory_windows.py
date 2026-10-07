import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

spec=importlib.util.spec_from_file_location('windows',Path(__file__).with_name('__init__.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class MemoryWindowTests(unittest.TestCase):
    def test_relevant_late_evidence_survives_where_prefix_loses_it(self):
        text='Genel giriş. '*90+'Falcon sözleşme: yenileme kararı durduruldu; onay yok. '+'Genel son. '*70
        query='Falcon yenileme kararı neydi?'
        self.assertNotIn('onay yok',text[:650])
        window=m.source_window(text,query)
        self.assertIn('onay yok',window['text']);self.assertGreater(window['excerpt_start_char'],0)
        self.assertEqual(window['text'],text[window['excerpt_start_char']:window['excerpt_end_char']])
        self.assertLessEqual(len(window['text']),650)

    def test_unicode_offsets_remain_exact_with_turkish_uppercase(self):
        text='İstanbul IĞDIR ıslak. '*55+'İZMİR yenileme durduruldu. '+ 'Kapanış. '*50
        window=m.source_window(text,'İzmir yenileme')
        self.assertIn('İZMİR',window['text'])
        self.assertEqual(window['text'],text[window['excerpt_start_char']:window['excerpt_end_char']])

    def test_no_matches_and_short_records_preserve_prefix(self):
        for text in ('', 'Kısa kayıt.', 'abc '*400):
            window=m.source_window(text,'Falcon yenileme')
            self.assertEqual(window['text'],text[:650]);self.assertEqual(window['excerpt_start_char'],0)
            self.assertEqual(window['excerpt_selection'],'prefix_no_query_match')

    def test_rich_passage_beats_repeated_single_term(self):
        text='Falcon '*80+'Dolgu. '*120+'Falcon yenileme takvim kararı açık. '+'Son. '*90
        window=m.source_window(text,'Falcon yenileme takvim')
        self.assertIn('takvim kararı açık',window['text']);self.assertEqual(window['query_match_terms'],3)

    def test_secrets_are_not_reread_and_invalid_sources_are_not_selected(self):
        record={'source':'knowledge/fixture.md','source_hash_matched':True,'source_sha256':'a'*64,
                'declared_date':{'state':'unknown'},'assessment':'source_statement','facts':{},
                'text':'Giriş. '*150+'Falcon anahtar [REDACTED]. ','text_truncated':True}
        reader=Mock(return_value={'records':[record,{**record,'source_hash_matched':False,'text':'Falcon SECRET'}],
                                 'conflicts':[{'sources':['knowledge/fixture.md','knowledge/other.md'],'resolved':False}]})
        brief=m.memory_brief('Falcon anahtar',reader=reader)
        reader.assert_called_once_with('Falcon anahtar')
        self.assertEqual(len(brief['records']),1);self.assertNotIn('SECRET',m.dump(brief))
        self.assertIn('[REDACTED]',brief['records'][0]['text'])
        self.assertFalse(brief['current_truth_verified']);self.assertFalse(brief['conflicts'][0]['resolved'])
        self.assertTrue(brief['records'][0]['text_truncated'])
        self.assertEqual(brief['records'][0]['offset_scope'],'validated_redacted_reader_excerpt')

    def test_budget_is_enforced_with_window_metadata(self):
        records=[{'source':f'knowledge/{i}.md','source_hash_matched':True,'facts':{},'text':'Falcon '*300} for i in range(9)]
        brief=m.memory_brief('Falcon',reader=lambda q:{'records':records},budget=2500)
        self.assertLessEqual(len(m.dump(brief)),2500);self.assertTrue(brief['retrieval_truncated'])
        self.assertLess(len(brief['records']),len(records))

if __name__=='__main__':unittest.main()
