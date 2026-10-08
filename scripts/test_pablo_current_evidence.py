import contextlib
import io
import json
import unittest
from unittest.mock import patch
from scripts import pablo_outcome_evidence as evidence


class CurrentEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.criterion=dict(task_id='fixture',input_digest='a'*64,expected_sha256='b'*64,
                            expected_bytes=12,execution_state='recorded')
        self.proof=dict(schema_version=1,request_id='fixture',status='matched',
                        method='independent_current_file_read',observed_at=1000,
                        input_digest='a'*64,expected_sha256='b'*64,expected_bytes=12,
                        observed_sha256='b'*64,observed_bytes=12,
                        file_bytes_matched_at_observation=True,
                        scope='private_draft_bytes_at_this_observation',read_only=True,
                        journal_status_updated=False,execution_authorized=False,
                        reexecution_authorized=False,customer_delivery_verified=False,
                        semantic_quality_verified=False,reason='current bytes')

    def view(self,proof=None,**kw):
        return evidence.current_evidence_view(self.proof if proof is None else proof,
                                             **(self.criterion|kw),now=1020)

    def test_positive_matches_only_the_explicit_file_criterion_at_a_dated_instant(self):
        view=self.view()
        self.assertEqual(view['new_task_outcome'],'matched_at_observation')
        self.assertTrue(view['current_file_outcome_verified']);self.assertTrue(view['fresh_file_read'])
        self.assertEqual(view['current_observation']['observed_at'],1000)
        for key in ('execution_outcome_verified','customer_delivery_verified',
                    'semantic_quality_verified','execution_authorized','reexecution_authorized'):
            self.assertIs(view[key],False)

    def test_matching_current_bytes_do_not_promote_unknown_execution_to_success(self):
        view=self.view(execution_state='unknown')
        self.assertEqual(view['new_task_outcome'],'unknown')
        self.assertTrue(view['current_file_outcome_verified'])
        self.assertFalse(view['execution_outcome_verified']);self.assertFalse(view['reexecution_authorized'])

    def test_different_current_bytes_invalidate_the_previous_success(self):
        changed=self.proof|dict(status='mismatch',observed_sha256='c'*64,
                               file_bytes_matched_at_observation=False)
        view=self.view(changed)
        self.assertEqual(view['new_task_outcome'],'mismatch')
        self.assertFalse(view['current_file_outcome_verified']);self.assertTrue(view['fresh_file_read'])

    def test_same_bytes_cannot_transfer_to_another_task_input_or_criterion(self):
        for kw in (dict(task_id='other'),dict(input_digest='d'*64),
                   dict(expected_sha256='d'*64),dict(expected_bytes=11)):
            with self.subTest(kw=kw):
                view=self.view(**kw);self.assertEqual(view['new_task_outcome'],'binding_mismatch')
                self.assertFalse(view['current_file_outcome_verified']);self.assertIsNone(view['current_observation'])

    def test_stale_future_broken_or_escalated_evidence_is_never_accepted(self):
        changes=[{'observed_at':900},{'observed_at':1021},{'observed_at':True},
                 {'observed_at':float('inf')},{'schema_version':True},
                 {'observed_bytes':True},{'read_only':1},{'status':'matched','observed_bytes':11},
                 {'file_bytes_matched_at_observation':1},{'input_digest':'broken'},
                 {'method':'independent_file_read'},{'scope':'customer_delivery'},
                 {'request_id':'../fixture'},{'api_key':'secret'}]
        changes += [{key:True} for key in ('journal_status_updated','execution_authorized',
                                         'reexecution_authorized','customer_delivery_verified','semantic_quality_verified')]
        for change in changes:
            with self.subTest(change=change):
                view=self.view(self.proof|change)
                self.assertFalse(view['current_file_outcome_verified']);self.assertFalse(view['fresh_file_read'])
        view=self.view({k:v for k,v in self.proof.items() if k!='read_only'})
        self.assertFalse(view['current_file_outcome_verified'])

    def test_unavailable_and_deferred_reads_cannot_authorize_replay(self):
        for status in ('unavailable','deferred','unsupported'):
            view=self.view(self.proof|{'status':status})
            self.assertEqual(view['new_task_outcome'],'unknown');self.assertFalse(view['reexecution_authorized'])

    def test_proposed_cli_request_does_not_contact_the_node(self):
        args=['--current','--task-id','fixture','--input-digest','a'*64,
              '--expected-sha256','b'*64,'--expected-bytes','12','--execution-state','proposed']
        with patch.object(evidence,'load_current_observation') as load,contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(evidence.main(args),0)
        load.assert_not_called();self.assertEqual(json.loads(output.getvalue())['new_task_outcome'],'not_run')

    def test_transport_targets_one_authenticated_get_and_rejects_wrong_identity(self):
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*a):self.close()
        requests=[]
        def opener(req,timeout):requests.append(req);return Response(json.dumps(self.proof).encode())
        with patch.object(evidence,'bridge_key',return_value='fixture-key'),patch.object(evidence,'urlopen',side_effect=opener):
            self.assertEqual(evidence.load_current_observation('fixture'),self.proof)
        self.assertTrue(requests[0].full_url.endswith('/tasks/fixture/observation'))
        self.assertEqual(requests[0].get_method(),'GET');self.assertEqual(requests[0].get_header('X-bridge-key'),'fixture-key')
        with patch.object(evidence,'bridge_key',return_value='fixture-key'),patch.object(evidence,'urlopen',return_value=Response(json.dumps(self.proof|{'request_id':'other'}).encode())):
            with self.assertRaises(ValueError):evidence.load_current_observation('fixture')


if __name__=='__main__':unittest.main()
