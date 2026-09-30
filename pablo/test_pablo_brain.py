"""Deterministic guard tests for pablo_brain (no network, no model): tool allowlist,
required parameters, parsing tolerance, and the rule that nothing runs after an
approval is required."""
import unittest

import pablo_brain as pb


def brain_with(replies):
    it = iter(replies)
    b = pb.PabloBrain()
    b._call_llm = lambda msgs: next(it)
    return b


class ParsingTests(unittest.TestCase):
    def test_alias_tool_key(self):
        self.assertEqual(pb.PabloBrain._extract_tool('TOOL: {"tool_name": "youtube_play", "query": "lofi"}'),
                         ("youtube_play", {"query": "lofi"}))

    def test_params_outside_wrapper_are_collected(self):
        name, params = pb.PabloBrain._extract_tool(
            'TOOL: {"tool": "marketing_playbook", "playbook": "instagram_bio", "text": "a", "public_post": true}')
        self.assertEqual(name, "marketing_playbook")
        self.assertEqual(params, {"playbook": "instagram_bio", "text": "a", "public_post": True})

    def test_plain_text_has_no_tool(self):
        self.assertIsNone(pb.PabloBrain._extract_tool("Merhaba"))


class RequiredParamTests(unittest.TestCase):
    def test_missing(self):
        self.assertEqual(pb.PabloBrain._missing_params("browser_open", {}), ["url"])
        self.assertEqual(pb.PabloBrain._missing_params("marketing_playbook", {"playbook": "instagram_bio"}), ["text"])

    def test_complete(self):
        self.assertEqual(pb.PabloBrain._missing_params("whatsapp_send", {"phone": "905", "text": "m"}), [])


class LoopSafetyTests(unittest.TestCase):
    def test_unknown_and_incomplete_tools_never_run(self):
        b = brain_with([
            'TOOL: {"tool": "social_post", "params": {"content": "merhaba"}}',
            'TOOL: {"tool": "browser_open", "params": {}}',
            'TOOL: {"tool": "browser_open", "params": {"url": "https://cybergene.co"}}',
            'Siteyi actim.',
        ])
        ran = []
        out = b.think_and_respond("siteyi ac", tool_executor=lambda n, p: ran.append((n, p)) or {"ok": True, "status": "SUCCESS", "result": {}})
        self.assertEqual(ran, [("browser_open", {"url": "https://cybergene.co"})])
        self.assertEqual(out["text"], "Siteyi actim.")

    def test_nothing_runs_after_approval_required(self):
        b = brain_with([
            'TOOL: {"tool": "whatsapp_send", "params": {"phone": "905", "text": "m", "is_new_contact": true}}',
            'TOOL: {"tool": "gui_type", "params": {"text": "x", "enter": true}}',
            'Onay bekliyor.',
        ])
        ran = []
        out = b.think_and_respond("mesaj at", tool_executor=lambda n, p: ran.append(n) or {"ok": False, "status": "APPROVAL_REQUIRED"})
        self.assertEqual(ran, ["whatsapp_send"])
        self.assertEqual(out["stopped"], "approval")

    def test_failure_stops_and_does_not_retry(self):
        b = brain_with([
            'TOOL: {"tool": "screenshot", "params": {}}',
            'Ekran goruntusu alinamadi.',
        ])
        ran = []
        out = b.think_and_respond("ekran al", tool_executor=lambda n, p: ran.append(n) or {"ok": False, "status": "FAILED", "error": "kilitli"})
        self.assertEqual(ran, ["screenshot"])
        self.assertEqual(out["stopped"], "failed")

    def test_step_limit(self):
        b = brain_with(['TOOL: {"tool": "window_list", "params": {"n": %d}}' % i for i in range(20)] + ["Bitti."])
        ran = []
        out = b.think_and_respond("surekli calis", tool_executor=lambda n, p: ran.append(n) or {"ok": True, "status": "SUCCESS", "result": {}})
        self.assertLessEqual(len(ran), pb.MAX_STEPS)


if __name__ == "__main__":
    unittest.main()
