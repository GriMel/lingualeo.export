import unittest
import logging
import sys
from PyQt4.QtTest import QTest
from PyQt4 import QtGui, QtCore
from gui_export import MainWindow


class TestMainWindow(unittest.TestCase):
    
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.app = QtGui.QApplication([])
        self.ui = MainWindow()

    def tearDown(self):
        """prevent gtk-Critical messages"""
        self.app.deleteLater()

    def test_only_input_checked(self):
        
        self.assertEqual(self.ui.input_radio.isChecked(), True)
        self.assertEqual(self.ui.text_radio.isChecked(), False)
        self.assertEqual(self.ui.kindle_radio.isChecked(), False)

    def test_kindle_radios_disabled(self):

        self.assertEqual(self.ui.all_words_radio.isEnabled(), False)
        self.assertEqual(self.ui.new_words_radio.isEnabled(), False)

    def test_kindle_radio_only_one_checked(self):

        self.ui.kindle_radio.setChecked(True)
        self.ui.new_words_radio.setChecked(True)
        self.assertEqual(self.ui.all_words_radio.isChecked(), False)

    def test_input_validator(self):

        validator = self.ui.input_word_edit.validator()
        text = "work раве"
        state, word, pos = validator.validate(text, 0)
        self.assertEqual(state==QtGui.QValidator.Acceptable, False)

if __name__ == "__main__":
    unittest.main()
