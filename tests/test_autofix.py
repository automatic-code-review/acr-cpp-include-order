import unittest
from pathlib import Path
import sys


class AutofixImportTests(unittest.TestCase):
    def test_import_autofix_module(self):
        src_dir = Path(__file__).resolve().parents[1] / "src"
        sys.path.insert(0, str(src_dir))

        from src import autofix as _autofix_module

        self.assertIsNotNone(_autofix_module)
