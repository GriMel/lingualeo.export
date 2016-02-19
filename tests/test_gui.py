#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===Description===
Module for tests

Recommended to run with nosetests as:
nosetests --exe --with-coverage --cover-erase --cover-html
"""

import unittest
import logging
import os
import json
import sqlite3
from PyQt4.QtTest import QTest
from PyQt4 import QtGui, QtCore
from gui_export import MainWindow, ExportDialog, StatisticsDialog,\
                       AboutDialog, NotificationDialog, ExceptionDialog,\
                       Results
from handler import Kindle
from service import Lingualeo

TEST_DB = 'test.db'
TEST_TXT = 'test.txt'


def leftMouseClick(widget):
    QTest.mouseClick(widget, QtCore.Qt.LeftButton)


def createTxtFile():
    with open(TEST_TXT, 'w') as f:
        f.write('bacon')
        f.write('simple')


def createSqlBase(malformed=False, empty=False, valid=True):
    """
    create test SQL base with name test.db
    """
    conn = sqlite3.connect('test.db')
    if valid:
        conn.execute("""
            CREATE TABLE WORDS
            (id TEXT PRIMARY KEY NOT NULL,
                word TEXT, stem TEXT, lang TEXT,
                category INTEGER DEFAULT 0,
                timestamp INTEGER DEFAULT 0,
                profileid TEXT);
             """)
    if valid and not empty:
        conn.execute("""
            INSERT INTO "WORDS"
            VALUES('en:intending',
                   'intending',
                   'intend',
                   'en',
                   0,1450067334997,
                   '')
        """)
    conn.commit()
    if malformed:
        with open(TEST_DB, 'wb') as f:
            f.write(b'tt')


def createLingualeoUser(premium=False):
    """return test Lingualeo user"""
    return {"premium_type": +premium,
            "fullname": "Bob Gubko",
            "meatballs": 1500,
            "avatar_mini": 'https://d144fqpiyasmrr'
                           '.cloudfront.net/uploads'
                           '/avatar/0s100.png',
            "xp_level": 34}


class BaseTest(unittest.TestCase):
    """
    Base class for tests
    """

    def setUp(self):
        """
        Construct QApplication
        """
        self.app = QtGui.QApplication([])

    def tearDown(self):
        """
        Prevent gtk-Critical messages.
        Remove app
        """
        self.app.quit()
        self.app.processEvents()
        self.app.sendPostedEvents(self.app, 0)
        self.app.flush()
        self.app.deleteLater()


class TestMainWindow(BaseTest):

    def setUp(self):
        """
        Turn off logger
        Set english language
        Set credentials from json file
        credentials.json structure:
        {
            "email":"example@gmail.com",
            "password":"123456789"
        }
        """
        super(TestMainWindow, self).setUp()
        logging.disable(logging.CRITICAL)
        with open('credentials.json') as f:
            credentials = json.loads(f.read())
        self.ui = MainWindow()
        self.ui.language = 'en'
        self.ui.loadTranslation()
        self.ui.email_edit.setText(credentials['email'])
        self.ui.pass_edit.setText(credentials['password'])

    def tearDown(self):
        """
        Prevent gtk-Critical messages
        Remove test.db in case if it's present
        """
        super(TestMainWindow, self).tearDown()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(TEST_TXT):
            os.remove(TEST_TXT)

    def test_only_input_checked(self):
        """
        Initial state of GUI: Only input_radio is checked
        """
        self.assertEqual(self.ui.input_radio.isChecked(), True)
        self.assertEqual(self.ui.text_radio.isChecked(), False)
        self.assertEqual(self.ui.kindle_radio.isChecked(), False)

    def test_kindle_radios_disabled(self):
        """
        All_words and new_words should be disabled
        """
        self.assertEqual(self.ui.all_words_radio.isEnabled(), False)
        self.assertEqual(self.ui.new_words_radio.isEnabled(), False)

    def test_kindle_radio_only_one_checked(self):
        """
        Checking new_words should uncheck all_words
        """
        self.ui.kindle_radio.setChecked(True)
        self.ui.new_words_radio.setChecked(True)
        self.assertEqual(self.ui.all_words_radio.isChecked(), False)

    def test_input_validator(self):
        """
        No non-Unicode is allowed in input
        """

        validator = self.ui.input_word_edit.validator()
        text = "work раве"
        state, word, pos = validator.validate(text, 0)
        self.assertEqual(state == QtGui.QValidator.Acceptable, False)

    def test_empty_login_pass(self):
        """
        No email/password is specified - show an error in statusbar.
        """
        self.ui.email_edit.setText("")
        self.ui.pass_edit.setText("")
        self.ui.input_word_edit.setText("test")
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Email or password are incorrect")

    def test_dialog_not_run(self):
        """
        Nothing is selected - ExportDialog shouldn't be constructed.
        """
        self.ui.email_edit.setText("")
        self.ui.pass_edit.setText("")
        leftMouseClick(self.ui.export_button)
        with self.assertRaises(AttributeError):
            self.ui.dialog

    def test_input_not_run(self):
        """
        No word in input - show an error in statusbar.
        """
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "No input")

    def test_text_no_file_not_run(self):
        """
        If no text file is selected - show an error in statusbar.
        """
        self.ui.text_radio.setChecked(True)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "No txt file")

    def test_kindle_no_base_not_run(self):
        """
        No Kindle database is selected - show an error in statusbar.
        """
        self.ui.kindle_radio.setChecked(True)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "No Kindle database")

    def test_kindle_wrong_format_not_run(self):
        """
        No '.db' in file extension for Kindle - show an error in statusbar.
        """
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_TXT)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Not database")

    def test_kindle_not_valid_base_not_run(self):
        """
        No WORDS in Kindle table - show an error in statusbar.
        """
        createSqlBase(valid=False)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Not valid database")

    def test_kindle_empty_base_not_run(self):
        """
        Table WORDS in Kindle database is empty - show an error in statusbar
        """
        createSqlBase(empty=True)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Kindle database is empty")

    def test_kindle_malformed_not_run(self):
        """
        Kindle database malformed - show 'Repair' and error in statusbar.
        """
        createSqlBase(malformed=True)
        self.ui.kindle_radio.setChecked(True)
        self.ui.kindle_path.setText(TEST_DB)
        leftMouseClick(self.ui.export_button)
        self.assertEqual(self.ui.repair_button.isHidden(), False)
        self.assertEqual(self.ui.status_bar.currentMessage(),
                         "Database is malformed. Click 'Repair'")

    def test_run_export(self):
        """
        Email/password set, set word in 'Input' - ExportDialog appears
        """


    def test_russian_translation(self):
        """
        Selecting RU from Language menu - russian translation is loaded
        """
        lang_item = self.ui.language_menu.actions()[1]
        lang_item.trigger()
        self.assertEqual(self.ui.export_button.text(), "Экспорт")


class TestExportDialog(BaseTest):
    """
    Class for testing ExportDialog
    """

    def setUp(self):
        """
        Set up initial condition:
        -special lingualeo user
        """
        super(TestExportDialog, self).setUp()
        self.lingualeo = Lingualeo("aaa@mail.com", "12345")

    def tearDown(self):
        """
        Prevent gtk-Critical messages.
        Remove test.db and test.txt in case if they're present.
        """
        super(TestExportDialog, self).tearDown()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(TEST_TXT):
            os.remove(TEST_TXT)

    def test_export_kindle_premium(self):
        """
        Test for unlimited sign if user is premium
        """
        createSqlBase()
        handler = Kindle(TEST_DB)
        array = handler.get()
        duplicates = 0
        total = len(array)
        self.lingualeo.auth_info = createLingualeoUser(premium=True)
        self.lingualeo.initUser()
        dialog = ExportDialog(array, total, duplicates, self.lingualeo)
        self.assertEqual("∞", dialog.meatballs_value_label.text())


class TestStatisticsDialog(BaseTest, Results):
    """
    Class for testing StatisticsDialog
    """

    def setUp(self):
        """
        Set up initial condition:
        -prepared list of dictionaries with results
        """
        self.array = []
        row = {}
        words = ["cat", "dog", "cockatoo", "smile"]
        contexts = ["I have a cat.",
                    "I have a dog.",
                    "",
                    "Let's smile."
                    ]
        translations = ["кот", "cобака", "какаду", "улыбка"]
        results = sorted(self.RESULTS.values())
        for index, (word, tword, context)\
                in enumerate(zip(words, translations, contexts)):
            row = {
                   "word": word,
                   "result": results[index],
                   "tword": tword,
                   "context": context
                }
            self.array.append(row)
        super(TestStatisticsDialog, self).setUp()
        self.stat_dialog = StatisticsDialog(self.array)

    def test_correct_counts(self):
        """
        Every label has its own count of words
        Total = 4
        Not added = 1
        Added = 1
        No translation = 1
        Exist = 1
        """
        self.assertEqual('4', self.stat_dialog.values[0].text())
        self.assertEqual('1', self.stat_dialog.values[1].text())
        self.assertEqual('1', self.stat_dialog.values[2].text())
        self.assertEqual('1', self.stat_dialog.values[3].text())
        self.assertEqual('1', self.stat_dialog.values[4].text())

    def test_correct_table_colors(self):
        """
        Every row in table has its own color
        1) added - green.
        2) exists - red.
        3) no translation - yellow.
        4) not added - white.
        """
        self.assertEqual(self.stat_dialog.table.item(0, 0).backgroundColor(),
                         QtCore.Qt.green)
        self.assertEqual(self.stat_dialog.table.item(1, 0).backgroundColor(),
                         QtCore.Qt.red)
        self.assertEqual(self.stat_dialog.table.item(2, 0).backgroundColor(),
                         QtCore.Qt.yellow)
        self.assertEqual(self.stat_dialog.table.item(3, 0).backgroundColor(),
                         QtCore.Qt.white)

    def test_correct_table_row_counts(self):
        """
        Table has four rows
        """
        self.assertEqual(self.stat_dialog.table.rowCount(), 4)


class TestAboutDialog(BaseTest):
    """
    Class for testing 'About' dialog.
    """
    JSON_FILE = os.path.join("src", "data", "data.json")

    def setUp(self):
        """
        Set up initial condition:
        -prepared json file
        -version, author, idea, email loaded
        """
        super(TestAboutDialog, self).setUp()
        with open(self.JSON_FILE) as f:
            data_info = json.loads(f.read())
        self.version = data_info['version']
        self.author = data_info['author']
        self.idea = data_info['idea']
        self.email = data_info['e-mail']
        self.about = AboutDialog()

    def test_version_present(self):
        """
        Data in json == data in 'About'
        """
        text = self.about.about_label.text()
        version_text = self.about.version_label.text()
        email_text = self.about.email_label.text()
        self.assertIn(self.author, text)
        self.assertIn(self.idea, text)
        self.assertIn(self.email, email_text)
        self.assertIn(self.version, version_text)

if __name__ == "__main__":
    unittest.main()
