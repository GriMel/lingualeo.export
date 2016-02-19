"""
===Description===
Module for testing all modules, except gui_export
-service - to test Lingualeo API for changes
-handler - to test handlers for correct work
-
"""
import unittest
from handler import Kindle, Text, Input
from service import Lingualeo


class TestLingualeo(unittest.TestCase):
    """
    Ensure that Lingualeo API is still the same
    """


class TestHandler(unittest.TestCase):
    """
    Ensure that all handlers return expected result
    """