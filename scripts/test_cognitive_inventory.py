import tempfile
import unittest
from pathlib import Path
from scripts.cognitive_inventory import inventory, differences


class InventoryTests(unittest.TestCase):
    def test_only_source_is_included_and_changes_are_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'core.py').write_text('value = 1')
            (root / 'memory.db').write_bytes(b'private runtime data')
            (root / '.env').write_text('private configuration')
            expected = inventory(root)
            self.assertEqual(set(expected), {'core.py'})
            (root / 'core.py').write_text('value = 2')
            self.assertEqual(differences(expected, inventory(root))['changed'], ['core.py'])
            (root / 'core.py').unlink()
            self.assertEqual(differences(expected, inventory(root))['missing'], ['core.py'])


if __name__ == '__main__':
    unittest.main()
