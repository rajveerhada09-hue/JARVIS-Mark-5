import importlib
import unittest


class BrainImportTest(unittest.TestCase):
    def test_brain_module_imports(self):
        module = importlib.import_module("brain.brain")
        self.assertTrue(hasattr(module, "JarvisBrain"))


if __name__ == "__main__":
    unittest.main()
