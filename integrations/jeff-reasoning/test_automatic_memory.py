import importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch

PLUGIN=Path(__file__).with_name('__init__.py')
def load():
    spec=importlib.util.spec_from_file_location('fresh_anonymous_reasoning',PLUGIN)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class AutomaticMemoryTests(unittest.TestCase):
    def test_fresh_plugin_helper_does_not_use_stale_global_module(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)/'reader.py'
            source.write_text("def read_context(query,strict=False):\n return {'strict':strict,'query':query,'version':1}\n")
            stale=types.SimpleNamespace(read_context=lambda q: {'stale':True})
            module=load();module.MEMORY_READER_PATH=source
            with patch.dict(sys.modules,{'scripts.jeff_memory_context':stale}):
                self.assertEqual(module.automatic_memory('Beta plan'),{'strict':True,'query':'Beta plan','version':1})
                source.write_text("def read_context(query,strict=False):\n return {'strict':strict,'query':query,'version':222}\n")
                fresh=load();fresh.MEMORY_READER_PATH=source
                self.assertEqual(fresh.automatic_memory('Atlas control')['version'],222)
                self.assertTrue(module.automatic_memory('Beta plan')['strict'])
    def test_missing_helper_is_unavailable_without_returning_private_error_text(self):
        module=load();module.MEMORY_READER_PATH=Path('/missing-anonymous-reader.py')
        result=module.memory_brief('Beta plan')
        self.assertEqual(result['status'],'memory_unavailable');self.assertEqual(result['records'],[])
        self.assertNotIn('/missing-anonymous',json.dumps(result))

if __name__=='__main__':unittest.main()
