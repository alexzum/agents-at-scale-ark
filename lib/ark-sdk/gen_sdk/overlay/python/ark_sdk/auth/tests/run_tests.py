#!/usr/bin/env python3
"""Test runner for ark-sdk authentication module."""
import sys
import unittest
import os

# Add the parent directory to the path so we can import ark_sdk modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def run_tests():
    """Run all authentication tests."""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())
