"""A Telegram approval button may only approve something that is actually waiting for approval.
Stale cards (already rejected, still a draft, unknown id) must change nothing and run nothing."""
import unittest
from unittest import mock

import marketing_telegram_gateway as gw

USER = 42


def call(action, ref, campaign=None, idea=None):
    """Run the callback with the database, Telegram and delivery all replaced by mocks."""
    pipeline = mock.Mock()
    if campaign is not None:
        campaign=dict(channel='email',recipient_target='fixture@example.test',message_body='fixture',**campaign)
    if idea is not None:
        idea=dict(caption_draft='fixture',**idea)
    pipeline.get_campaign.return_value = campaign
    pipeline.get_content_idea.return_value = idea
    playbooks = mock.Mock()
    playbooks.execute_campaign_delivery.return_value = {"ok": True, "status": "SIMULATED", "verified": False}
    with mock.patch.object(gw, 'MarketingPipeline', pipeline), \
            mock.patch.object(gw, 'MarketingPlaybooks', playbooks), \
            mock.patch.object(gw, 'send_telegram_raw') as tg, \
            mock.patch.object(gw, 'ApprovalClient') as client, \
            mock.patch.object(gw, 'get_telegram_config', return_value={'telegram_default_chat_id': str(USER)}):
        result = gw.handle_marketing_callback('cb', f'{action}:{ref}:fixture-id', USER, USER)
    return result, pipeline, playbooks, tg


class CampaignApprovalGuard(unittest.TestCase):
    def test_pending_campaign_can_be_approved(self):
        result, pipeline, playbooks, _ = call('mkt_appr', 6, campaign={'status': 'PENDING_APPROVAL'})
        pipeline.update_campaign_status.assert_any_call(6, 'APPROVED', approved_by=f'telegram_{USER}')
        playbooks.execute_campaign_delivery.assert_called_once()
        self.assertEqual(playbooks.execute_campaign_delivery.call_args.kwargs.get('simulated'), True)

    def test_stale_or_wrong_state_never_approves_or_runs(self):
        for state in ('REJECTED', 'DRAFTED', 'APPROVED', 'SENT', 'FAILED'):
            result, pipeline, playbooks, tg = call('mkt_appr', 6, campaign={'status': state})
            self.assertEqual(result['status'], 'NOT_PENDING', state)
            pipeline.update_campaign_status.assert_not_called()
            playbooks.execute_campaign_delivery.assert_not_called()
            tg.assert_not_called()

    def test_unknown_campaign_is_refused(self):
        result, pipeline, playbooks, _ = call('mkt_appr', 999, campaign=None)
        self.assertEqual(result['status'], 'NOT_PENDING')
        pipeline.update_campaign_status.assert_not_called()
        playbooks.execute_campaign_delivery.assert_not_called()

    def test_simulation_is_reported_as_unsent(self):
        result, _, _, tg = call('mkt_appr', 6, campaign={'status': 'PENDING_APPROVAL'})
        self.assertEqual(result['status'], 'SIMULATED')
        self.assertIn('Mesaj gönderilmedi', tg.call_args.args[1]['text'])
        self.assertNotIn('VERIFIED', tg.call_args.args[1]['text'])

    def test_failed_delivery_never_reports_success(self):
        with mock.patch.object(gw, 'MarketingPipeline') as pipeline, \
                mock.patch.object(gw, 'MarketingPlaybooks') as playbooks, \
                mock.patch.object(gw, 'send_telegram_raw') as tg, \
                mock.patch.object(gw, 'ApprovalClient'), \
                mock.patch.object(gw, 'get_telegram_config', return_value={'telegram_default_chat_id': USER}):
            pipeline.get_campaign.return_value = {'status': 'PENDING_APPROVAL','channel':'email','recipient_target':'fixture@example.test','message_body':'fixture'}
            playbooks.execute_campaign_delivery.return_value = {'ok': False, 'error': '<fixture failure>'}
            result = gw.handle_marketing_callback('cb', 'mkt_appr:6:fixture-id', USER, USER)
        self.assertFalse(result['ok'])
        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('tamamlanamadı', tg.call_args.args[1]['text'])
        self.assertIn('&lt;fixture failure&gt;', tg.call_args.args[1]['text'])

    def test_owner_in_wrong_chat_and_missing_owner_are_rejected(self):
        for config, chat in (({'telegram_default_chat_id': USER}, 1), ({}, USER)):
            with mock.patch.object(gw, 'get_telegram_config', return_value=config), \
                    mock.patch.object(gw, 'MarketingPipeline') as pipeline, \
                    mock.patch.object(gw, 'send_telegram_raw') as tg:
                self.assertEqual(gw.handle_marketing_callback('cb', 'mkt_appr:6', USER, chat)['status'], 'UNAUTHORIZED')
                pipeline.get_campaign.assert_not_called()
                tg.assert_not_called()

    def test_reject_still_works_from_any_state(self):
        result, pipeline, _, _ = call('mkt_rejc', 6, campaign={'status': 'PENDING_APPROVAL'})
        self.assertEqual(result['status'], 'REJECTED')

    def test_other_users_are_rejected_before_anything_else(self):
        pipeline = mock.Mock()
        with mock.patch.object(gw, 'MarketingPipeline', pipeline), \
                mock.patch.object(gw, 'send_telegram_raw'), \
                mock.patch.object(gw, 'get_telegram_config', return_value={'telegram_default_chat_id': '7'}):
            result = gw.handle_marketing_callback('cb', 'mkt_appr:6', USER, 1)
        self.assertEqual(result['status'], 'UNAUTHORIZED')
        pipeline.get_campaign.assert_not_called()


class ContentIdeaApprovalGuard(unittest.TestCase):
    def test_only_pending_idea_can_advance(self):
        result, pipeline, _, _ = call('ig_appr', 9, idea={'status': 'PENDING_APPROVAL'})
        self.assertNotEqual(result.get('status'), 'NOT_PENDING')
        for state in ('REJECTED', 'DRAFTED', None):
            result, pipeline, _, _ = call('ig_appr', 9, idea={'status': state} if state else None)
            self.assertEqual(result['status'], 'NOT_PENDING')
            pipeline.update_content_idea_status.assert_not_called()


if __name__ == '__main__':
    unittest.main()
