"""Run with the deployed Hermes framework on PYTHONPATH; no network calls."""
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from hermes_constants import set_hermes_home_override, reset_hermes_home_override
from hermes_cli.plugins import PluginManager, parse_manifest_file

class ActualPluginRuntimeTests(unittest.TestCase):
    def test_real_loader_and_hook_dispatch_isolate_profiles_a_b_a(self):
        with tempfile.TemporaryDirectory() as root:
            homes=[Path(root)/name for name in ('a','b')]
            managers=[]
            source=Path(__file__).resolve().parents[1]/'integrations/model-route-receipts'
            for home in homes:
                target=home/'plugins/model-route-receipts'; shutil.copytree(source,target)
                (home/'config.yaml').write_text('{}\n')
                manifest=parse_manifest_file(target/'plugin.yaml',target,'user','')
                manager=PluginManager(scope_key=str(home)); manager._load_plugin(manifest)
                loaded=manager._plugins['model-route-receipts']
                self.assertTrue(loaded.enabled,loaded.error)
                self.assertFalse(manager._plugin_tool_names)
                self.assertFalse(manager._system_prompt_sections)
                managers.append(manager)
            for index in (0,1,0):
                token=set_hermes_home_override(homes[index])
                try:
                    data={'session_id':str(index),'turn_id':'turn','api_request_id':str(index),
                          'provider':'fixture','model':'fixture','assistant_content_chars':2,'finish_reason':'stop'}
                    managers[index].invoke_hook('pre_api_request',**data)
                    managers[index].invoke_hook('post_api_request',**data)
                finally:
                    reset_hermes_home_override(token)
            for index,count in ((0,2),(1,1)):
                with sqlite3.connect(homes[index]/'state.db') as db:
                    rows=db.execute('SELECT session_id,status FROM model_route_receipts').fetchall()
                self.assertEqual(rows,[(str(index),'succeeded')]*count)
