#!/usr/bin/env python3
"""Automated Test Runner for AI-Enhanced LibreOffice Writer using standard library."""

import importlib.util
import os
import sys
import time
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def discover_and_run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Load from tests directory recursively using file paths
    for root, _, files in os.walk(os.path.join(PROJECT_ROOT, "tests")):
        for file in sorted(files):
            if file.startswith("test_") and file.endswith(".py"):
                file_path = os.path.join(root, file)
                mod_name = f"test_module_{os.path.splitext(file)[0]}"
                try:
                    spec = importlib.util.spec_from_file_location(mod_name, file_path)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules[mod_name] = mod
                        spec.loader.exec_module(mod)

                        for attr_name in sorted(dir(mod)):
                            attr = getattr(mod, attr_name)
                            if isinstance(attr, type) and issubclass(attr, unittest.TestCase):
                                suite.addTests(loader.loadTestsFromTestCase(attr))
                            elif callable(attr) and attr_name.startswith("test_") and not isinstance(attr, type):
                                # Wrap standalone function
                                test_func = attr
                                class StandaloneTest(unittest.TestCase):
                                    pass
                                def make_test(fn):
                                    return lambda self: fn()
                                setattr(StandaloneTest, attr_name, make_test(test_func))
                                suite.addTest(StandaloneTest(attr_name))

                except Exception as e:
                    print(f"Error loading {file_path}: {e}")

    runner = unittest.TextTestRunner(verbosity=2)
    start = time.time()
    result = runner.run(suite)
    elapsed = time.time() - start

    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Time: {elapsed:.3f}s")
    print("=" * 60)

    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    discover_and_run_tests()

