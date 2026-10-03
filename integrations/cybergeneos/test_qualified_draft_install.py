"""Production layout may omit the test directory; exercise the actual installer."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch


def test_install_creates_new_target_parent_and_reinstall_is_noop():
    source = Path(__file__).parent / 'qualification_drafts/install.py'
    spec = importlib.util.spec_from_file_location('qualified_draft_install', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bundle = root / 'bundle'
        live = root / 'live'
        panel = live / 'docs/cybergeneos'
        panel.mkdir(parents=True)
        (panel / 'app.js').write_text('old\n')
        files = {'app.js': 'new\n', 'server/marketing.py': 'marketing\n',
                 'server/qualified_draft.py': 'qualified\n', 'tests/test_qualified_draft.py': 'tests\n'}
        for name, content in files.items():
            dest = bundle / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
        sha = lambda text: hashlib.sha256(text.encode()).hexdigest()
        (bundle / 'baseline-normalized-hashes.json').write_text(json.dumps({'app.js': sha('old\n')}))
        (bundle / 'target-hashes.json').write_text(json.dumps({name: sha(text) for name, text in files.items()}))
        (bundle / 'qualified-draft.patch').write_text(
            'diff --git a/docs/cybergeneos/app.js b/docs/cybergeneos/app.js\n'
            '--- a/docs/cybergeneos/app.js\n+++ b/docs/cybergeneos/app.js\n@@ -1 +1 @@\n-old\n+new\n')
        with patch.object(module, '__file__', str(bundle / 'install.py')):
            module.install(live, apply=True)
            first = {name: (panel / name).stat().st_mtime_ns for name in files}
            module.install(live, apply=True)
            assert first == {name: (panel / name).stat().st_mtime_ns for name in files}
        assert all((panel / name).read_text() == text for name, text in files.items())
