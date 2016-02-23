# !/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=E1002, W0212
# E1002 - to avoid PyQt errors about old-style class
# W0212 - to avoid error on sys._excepthook
"""
===Description===
GUI version of lingualeo.export

===Usage===
python gui_export.py

"""

import sys
import os
import sqlite3
import time
import traceback
import json
import psutil
from PyQt4 import QtCore, QtGui
from requests.exceptions import ConnectionError as NoConnection, Timeout
from collections import Counter
from operator import itemgetter
from subprocess import check_call
from tendo import singleton

from handler import Kindle, Text
from service import Lingualeo
from log_conf import setLogger

# @FROZEN
# from pydub import AudioSegment
# from pydub.playback import play


def centerUI(self):
    """
    Place UI in the middle of the screen
    """
    qr = self.frameGeometry()
    cp = QtGui.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())


def createSeparator():
    """
    Function for creating separator in GUI
    """
    separator = QtGui.QFrame()
    separator.setFrameShape(QtGui.QFrame.HLine)
    separator.setFrameShadow(QtGui.QFrame.Sunken)
    return separator

#@FROZEN
#def playSound(name):
#    """sound notification"""
#    pass
#


class WinDialog(QtGui.QDialog):
    """
    Class for creating special dialogs for Windows
    - without maximize button
    - without help button
    """

    def __init__(self):
        super(WinDialog, self).__init__()
        windowFlags = self.windowFlags()
        windowFlags &= ~QtCore.Qt.WindowMaximizeButtonHint
        windowFlags &= ~QtCore.Qt.WindowMinMaxButtonsHint
        windowFlags &= ~QtCore.Qt.WindowContextHelpButtonHint
        windowFlags |= QtCore.Qt.WindowMinimizeButtonHint
        self.setWindowFlags(windowFlags)


class WinFullDialog(QtGui.QDialog):
    """
    Class for creating special dialogs for Windows
    - without help button
    """

    def __init__(self):
        super(WinFullDialog, self).__init__()
        windowFlags = self.windowFlags()
        windowFlags |= QtCore.Qt.WindowMaximizeButtonHint
        windowFlags |= QtCore.Qt.WindowMinMaxButtonsHint
        windowFlags &= ~QtCore.Qt.WindowContextHelpButtonHint
        windowFlags |= QtCore.Qt.WindowMinimizeButtonHint
        self.setWindowFlags(windowFlags)

# No Help/Maximize (or just no Help) for dialogs in Windows
if os.name == 'nt':
    CustomDialog = WinDialog
    CustomFullDialog = WinFullDialog
else:
    CustomDialog = QtGui.QDialog
    CustomFullDialog = QtGui.QDialog


class AboutDialog(CustomDialog):
    """
    About Dialog.
    Shows author, idea and version
    """
    ICON_FILE = os.path.join("src", "pics", "about.ico")
    ICON_LING_FILE = os.path.join("src", "pics", "lingualeo.ico")
    DATA_FILE = os.path.join("src", "data", "data.json")

    def __init__(self):
        """
        Initializing 'About' dialog
        """
        super(AboutDialog, self).__init__()
        self.initUI()
        self.retranslateUI()
        self.initActions()

    def initUI(self):
        """
        Construct 'About' dialog GUI
        """
        layout = QtGui.QVBoxLayout()
        self.icon_label = QtGui.QLabel()
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        self.version_label = QtGui.QLabel()
        self.version_label.setAlignment(QtCore.Qt.AlignCenter)
        self.about_label = QtGui.QLabel()
        self.email_label = QtGui.QLabel()
        self.email_label.setAlignment(QtCore.Qt.AlignCenter)

        self.ok_button = QtGui.QPushButton()
        layout.addWidget(self.icon_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.about_label)
        layout.addWidget(self.email_label)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def retranslateUI(self):
        """
        Set texts for buttons/labels of About dialog
        """

        with open(self.DATA_FILE) as f:
            data_info = json.loads(f.read())
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.setWindowTitle(self.tr("About"))
        self.icon_label.setPixmap(QtGui.QPixmap(self.ICON_LING_FILE))
        version_txt = "Kindleo {0}".format(data_info['version'])
        self.version_label.setText(version_txt)
        idea = data_info['idea']
        author = data_info['author']
        email = data_info['e-mail']
        self.about_label.setText(self.tr(
            """
            <span>
            <center>
            GUI version of script for exporting<br>
            words to Lingualeo from Input, Txt file or<br>
            Kindle vocabulary.<br>
            Specially for users of The-Ebook Amazon forum.
            <br><br>
            <b>Original idea</b><br>{0}<br><br>
            <b>GUI and some improvements:</b><br>
            {1}<br>
            </center>
            </span>
            """.format(idea, author)
            ))
        self.email_label.setText(
            self.tr("<a href='mailto:{0}'>Send E-mail</a>".format(email)))
        self.ok_button.setText(self.tr("OK"))

    @staticmethod
    def openEmail(link):
        """
        Write an e-mail to developer.
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))

    def initActions(self):
        """
        Actions for Ok and e-mail buttons.
        """
        self.ok_button.clicked.connect(self.close)
        self.email_label.linkActivated.connect(self.openEmail)


class AreYouSure(CustomDialog):
    """
    Exit prompt dialog
    Are you sure? Yes/No
    """
    ICON_FILE = os.path.join("src", "pics", "exit.ico")
    saved = QtCore.pyqtSignal(bool)

    def __init__(self):
        """
        Initializing AreYouSure.
        """
        super(AreYouSure, self).__init__()
        self.initUI()
        self.retranslateUI()
        self.initActions()

    def initUI(self):
        """
        Construct AreYouSure GUI
        """
        self.setWindowFlags(
            self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        layout = QtGui.QVBoxLayout()
        hor_lay = QtGui.QHBoxLayout()
        self.sure_label = QtGui.QLabel()
        self.check_item = QtGui.QCheckBox()
        self.yes_button = QtGui.QPushButton()
        self.no_button = QtGui.QPushButton()
        hor_lay.addWidget(self.yes_button)
        hor_lay.addWidget(self.no_button)
        layout.addWidget(self.check_item)
        layout.addWidget(self.sure_label)
        layout.addLayout(hor_lay)
        self.setLayout(layout)

    def retranslateUI(self):
        """
        Set texts for buttons/labels of AreYouSure
        """
        self.setWindowTitle(self.tr("Exit"))
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.sure_label.setText(self.tr("Are you sure to quit?"))
        self.yes_button.setText(self.tr("Yes"))
        self.no_button.setText(self.tr("No"))
        self.check_item.setText(self.tr("Save e-mail/password"))

    def exit(self):
        """handle correct exit"""
        save_email = self.check_item.isChecked()
        self.saved.emit(save_email)
        QtGui.QApplication.quit()

    def initActions(self):
        """
        Actions for Yes/No buttons
        Yes - save email/pass
        No - close AreYouSure
        """
        self.yes_button.clicked.connect(self.exit)
        self.no_button.clicked.connect(self.close)


class NotificationDialog(CustomDialog):
    """
    Dialog for notifications:
    - connection lost
    - another instance of program
    - do smth.
    """
    ICON_FILE = os.path.join("src", "pics", "warning.ico")

    def __init__(self, title, text):
        """
        Initializing NotificationDialog:
        -title.
        -text.
        """
        super(NotificationDialog, self).__init__()
        self.title = title
        self.text = text
        self.initUI()
        self.retranslateUI()
        self.initActions()

    def initUI(self):
        layout = QtGui.QVBoxLayout()
        self.text_label = QtGui.QLabel()
        self.text_label.setAlignment(QtCore.Qt.AlignCenter)
        self.ok_button = QtGui.QPushButton()
        layout.addWidget(self.text_label)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def retranslateUI(self):
        self.setWindowTitle(self.title)
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.text_label.setText(self.text)
        self.ok_button.setText("OK")

    def initActions(self):
        self.ok_button.clicked.connect(self.close)


class MainWindow(QtGui.QMainWindow):
    """
    Main Window
    3 blocks - Input/Text/Kindle
    """
    ICON_FILE = os.path.join("src", "pics", "lingualeo.ico")
    SRC = os.path.join("src", "src.ini")
    VOCAB_PATH = os.path.join("Kindle",
                              "system",
                              "vocabulary",
                              "vocab.db"
                              )
    # for repairing malformed database
    # 'posix' - linux
    # 'nt' - windows
    SQLITE_PATH = {
        'posix': os.path.join("src",
                              "sqlite_lin",
                              "sqlite3"),
        'nt': os.path.join("src",
                           "sqlite_win",
                           "sqlite3.exe")
        }

    def __init__(self):
        """
        Initializing MainWindow.
        -default language - English.
        -set logging of module.
        -centered on screen.
        -load default email/pass/lang if present.
        -ensure only 1/3 blocks enabled.
        -init actions
        -set validator for manual input's field

        """
        super(MainWindow, self).__init__()
        self.language = "en"
        self.file_name = None
        self.array = None
        self.lingualeo = None
        self.logger = setLogger(name='MainWindow')
        self.initUI()
        self.loadDefaults()
        self.loadTranslation()
        centerUI(self)
        self.checkState()
        self.initActions()
        self.setValidators()
        self.logger.debug("Inited MainWindow")

    def createMenuBar(self):
        """
        Create menubar for MainWindow.
        Has Language submenu - EN/RU/UA and Exit.
        """
        self.menu_bar = QtGui.QMenuBar()
        self.main_menu = QtGui.QMenu()
        self.language_menu = QtGui.QMenu()
        self.lang_action_group = QtGui.QActionGroup(self)
        for i in ("EN", "RU", "UA"):
            action = QtGui.QAction(i, self)
            action.setObjectName(i.lower())
            self.lang_action_group.addAction(action)
            self.language_menu.addAction(action)
        self.exit_action = QtGui.QAction(self)
        self.main_menu.addAction(self.language_menu.menuAction())
        self.main_menu.addAction(self.exit_action)

        self.help_menu = QtGui.QMenu(self.menu_bar)
        self.about_action = QtGui.QAction(self)
        self.help_menu.addAction(self.about_action)

        self.menu_bar.addAction(self.main_menu.menuAction())
        self.menu_bar.addAction(self.help_menu.menuAction())
        self.setMenuBar(self.menu_bar)

    def createAuthBlock(self):
        """
        Construct block for email/password
        """
        self.auth_label = QtGui.QLabel()
        self.email_label = QtGui.QLabel()
        self.email_edit = QtGui.QLineEdit()
        self.email_edit.setObjectName('email')
        self.pass_label = QtGui.QLabel()
        self.pass_edit = QtGui.QLineEdit()
        self.pass_edit.setEchoMode(QtGui.QLineEdit.PasswordEchoOnEdit)
        self.pass_edit.setObjectName('pass')

        auth_layout = QtGui.QGridLayout()
        auth_layout.addWidget(self.email_label, 0, 0, 1, 1)
        auth_layout.addWidget(self.email_edit, 0, 1, 1, 1)
        auth_layout.addWidget(self.pass_label, 1, 0, 1, 1)
        auth_layout.addWidget(self.pass_edit, 1, 1, 1, 1)

        return auth_layout

    def createInputBlock(self):
        """
        Init block for Input
        """
        self.input_radio = QtGui.QRadioButton()
        self.input_radio.setObjectName("input")
        self.input_radio.setChecked(True)
        self.input_word_label = QtGui.QLabel()
        self.input_context_label = QtGui.QLabel()
        self.input_word_edit = QtGui.QLineEdit()
        self.input_context_edit = QtGui.QLineEdit()

        input_layout = QtGui.QGridLayout()
        input_layout.addWidget(self.input_word_label, 0, 0, 1, 1)
        input_layout.addWidget(self.input_word_edit, 0, 1, 1, 1)
        input_layout.addWidget(self.input_context_label, 1, 0, 1, 1)
        input_layout.addWidget(self.input_context_edit, 1, 1, 1, 1)

        return input_layout

    def createTextBlock(self):
        """
        Construct block for Text
        """
        self.text_radio = QtGui.QRadioButton()
        self.text_radio.setObjectName("text")
        self.text_button = QtGui.QPushButton()
        self.text_path = QtGui.QLineEdit()
        self.text_path.setReadOnly(True)
        text_layout = QtGui.QHBoxLayout()
        text_layout.addWidget(self.text_button)
        text_layout.addWidget(self.text_path)

        return text_layout

    def createKindleBlock(self):
        """
        Construct block for Kindle
        """
        self.kindle_radio = QtGui.QRadioButton()
        self.kindle_radio.setObjectName("kindle")
        self.kindle_hint = QtGui.QLabel()
        self.kindle_button = QtGui.QPushButton()
        self.kindle_path = QtGui.QLineEdit()
        self.kindle_path.setReadOnly(True)
        self.kindle_words_layout = QtGui.QHBoxLayout()
        self.all_words_radio = QtGui.QRadioButton()
        self.all_words_radio.setChecked(True)
        self.new_words_radio = QtGui.QRadioButton()
        self.words_radio_group = QtGui.QButtonGroup()
        self.words_radio_group.addButton(self.all_words_radio)
        self.words_radio_group.addButton(self.new_words_radio)
        kindle_layout = QtGui.QGridLayout()
        kindle_layout.addWidget(self.kindle_button, 0, 0)
        kindle_layout.addWidget(self.kindle_path, 0, 1)
        kindle_layout.addWidget(self.all_words_radio, 1, 0, 1, 0)
        kindle_layout.addWidget(self.new_words_radio, 2, 0, 1, 0)

        return kindle_layout

    def initUI(self):
        """
        Construct GUI gor MainWindow
        """
        self.main_widget = QtGui.QWidget(self)
        self.main_layout = QtGui.QVBoxLayout()

        self.auth_layout = self.createAuthBlock()
        self.main_label = QtGui.QLabel()
        self.main_label.setAlignment(QtCore.Qt.AlignCenter)

        self.input_layout = self.createInputBlock()
        self.text_layout = self.createTextBlock()
        self.kindle_layout = self.createKindleBlock()

        self.export_button = QtGui.QPushButton()
        self.kindle_truncate_button = QtGui.QPushButton()
        self.kindle_truncate_button.setEnabled(False)
        self.repair_button = QtGui.QPushButton()
        self.repair_button.hide()
        self.bottom_layout = QtGui.QHBoxLayout()
        self.bottom_layout.addWidget(self.export_button)
        self.bottom_layout.addWidget(self.kindle_truncate_button)

        self.bottom_layout.addWidget(self.repair_button)

        self.source_group = QtGui.QButtonGroup()
        self.source_group.addButton(self.input_radio)
        self.source_group.addButton(self.text_radio)
        self.source_group.addButton(self.kindle_radio)

        # Create 4 separators for next usage
        h_lines = []
        for _ in range(4):
            h = createSeparator()
            h_lines.append(h)

        self.main_layout.addLayout(self.auth_layout)
        self.main_layout.addWidget(h_lines[0])
        self.main_layout.addWidget(self.main_label)
        self.main_layout.addWidget(self.input_radio)
        self.main_layout.addLayout(self.input_layout)
        self.main_layout.addWidget(h_lines[1])
        self.main_layout.addWidget(self.text_radio)
        self.main_layout.addLayout(self.text_layout)
        self.main_layout.addWidget(h_lines[2])
        self.main_layout.addWidget(self.kindle_radio)
        self.main_layout.addWidget(self.kindle_hint)
        self.main_layout.addLayout(self.kindle_layout)
        self.main_layout.addWidget(h_lines[3])
        self.main_layout.addLayout(self.bottom_layout)
        self.status_bar = QtGui.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        self.language_menu = QtGui.QMenu
        self.createMenuBar()

    def retranslateUI(self):
        """
        Set text for buttons/labels of MainWindow
        """
        self.setWindowTitle(self.tr("Kindleo"))
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.email_label.setText("e-mail")
        self.pass_label.setText("password")
        self.main_label.setText(self.tr("Choose the source"))
        self.input_radio.setText(self.tr("Input"))
        self.input_radio.setStyleSheet("font-weight:bold")
        self.input_word_label.setText(self.tr("word"))
        self.input_context_label.setText(self.tr("context"))

        self.text_radio.setText(self.tr("Text"))
        self.text_radio.setStyleSheet("font-weight:bold")
        self.text_button.setText(self.tr("Path"))

        self.kindle_radio.setText(self.tr("Kindle"))
        self.kindle_radio.setStyleSheet("font-weight:bold")

        self.kindle_hint.setText(self.tr(
            "Base is here:<br>{}".format(self.VOCAB_PATH)))
        self.all_words_radio.setText(self.tr("All words (recommended)"))
        self.new_words_radio.setText(self.tr("Only new"))
        self.new_words_radio.setToolTip(self.tr("Words, marked for learning"))
        self.kindle_button.setText(self.tr("Path"))

        self.export_button.setText(self.tr("Export"))
        self.kindle_truncate_button.setText(self.tr("Truncate"))
        self.repair_button.setText(self.tr("Repair"))

        # retranslate menu
        self.main_menu.setTitle(self.tr("Main menu"))
        self.language_menu.setTitle(self.tr("Language"))
        self.exit_action.setText(self.tr("Exit"))

        self.help_menu.setTitle(self.tr("Help"))
        self.about_action.setText(self.tr("About"))

        self.setFixedHeight(self.sizeHint().height())

    def setValidators(self):
        """
        Set validators to all input fields to
        prevent incorrect input value:
        -no non-English letters
        -no !@#$%^&*()
        """
        regexp = QtCore.QRegExp("^[a-zA-Z`'-]+(\s+[a-zA-Z`'-]+)*$")
        validator = QtGui.QRegExpValidator(regexp)
        self.input_word_edit.setValidator(validator)

    def checkState(self):
        """
        Every block (Input, Text, Kindle) should be enabled
        with the corresponding radio button when the other
        blocks should be disabled
        """
        input_state = self.input_radio.isChecked()
        text = self.text_radio.isChecked()
        kindle = self.kindle_radio.isChecked()

        self.input_word_edit.setEnabled(input_state)
        self.input_context_edit.setEnabled(input_state)
        self.input_word_label.setEnabled(input_state)
        self.input_context_label.setEnabled(input_state)
        self.text_button.setEnabled(text)
        self.text_path.setEnabled(text)
        self.kindle_hint.setEnabled(kindle)
        self.all_words_radio.setEnabled(kindle)
        self.new_words_radio.setEnabled(kindle)
        self.kindle_button.setEnabled(kindle)
        self.kindle_path.setEnabled(kindle)
        self.kindle_truncate_button.setEnabled(kindle)

    def lingualeoOk(self):
        """
        Check for Lingualeo - email/pass, connection
        """
        self.logger.debug("Checking lingualeo")
        try:
            self.lingualeo.auth()
        # handle no internet connection/no site connection
        except(NoConnection, Timeout):
            self.status_bar.showMessage(
                self.tr("No connection"))
            self.logger.debug(
                "Lingualeo: WRONG - No connection"
                )
            return False

        # handle wrong email/password
        except KeyError:
            self.status_bar.showMessage(
                self.tr("Email or password are incorrect"))
            self.logger.debug(
                "Lingualeo: WRONG email/pass incorrect")
            return False
        if self.lingualeo.meatballs == 0:
            self.status_bar.showMessage(
                self.tr("No meatballs"))
            self.logger.debug(
                "Lingualeo: WRONG - no meatballs")
            return False
        self.logger.debug("Lingualeo is OK")
        self.lingualeo.initUser()
        return True

    def inputOk(self):
        """
        Check for input presence
        """
        word = self.input_word_edit.text()
        if not word:
            self.status_bar.showMessage(self.tr("No input"))
            return False
        else:
            return True

    def textOk(self):
        """
        Check for correct txt file:
        - presence
        - extension
        - non-emptiness
        """
        path = self.text_path.text()
        self.logger.debug("Checking TXT - %s", path)
        _, ext = os.path.splitext(path)
        if not path:
            self.status_bar.showMessage(
                self.tr("No txt file"))
            self.logger.debug("%s - no path", path)
            return False
        if ext != '.txt':
            self.status_bar.showMessage(
                self.tr("Not txt file"))
            self.logger.debug("%s - is not TXT", path)
            return False
        if os.stat(path).st_size == 0:
            self.status_bar.showMessage(self.tr("Txt file is empty"))
            self.logger.debug("%s - TXT is empty", path)
            return False
        self.logger.debug("%s - TXT is OK", path)
        return True

    def kindleOk(self):
        """
        Check for correct Kindle database:
        - presence
        - extension (.db)
        - table WORDS exists
        - is not malformed
        """
        path = self.kindle_path.text()
        self.logger.debug("Checking Kindle - %s", path)
        # no path
        if not path:
            self.status_bar.showMessage(self.tr("No Kindle database"))
            self.logger.debug("%s - no path", path)
            return False

        # not valid database
        _, ext = os.path.splitext(path)
        if ext != '.db':
            self.status_bar.showMessage(
                self.tr("Not database"))
            self.logger.debug("%s - not '.db'", path)
            return False

        # check database
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        data = None
        try:
            data = cursor.execute("SELECT * FROM WORDS").fetchall()
        # no table WORDS
        except sqlite3.OperationalError:
            self.status_bar.showMessage(
                self.tr("Not valid database"))
            self.logger.debug("%s has no WORDS table", path)
            return False
        # database is malformed
        except sqlite3.DatabaseError:
            self.status_bar.showMessage(
                self.tr("Database is malformed. Click 'Repair'"))
            self.logger.debug("%s is malformed", path)
            self.repair_button.show()
            return False
        # database is empty
        if not data:
            self.status_bar.showMessage(
                self.tr("Kindle database is empty"))
            self.logger.debug("%s has WORDS but is empty", path)
            return False
        self.logger.debug("%s - DB is OK", path)
        return True

    def wordsOk(self):
        """
        Check for duplicates.
        The same word can appear with different context.
        """
        temp = []
        for row in self.array:
            # remove repeated words
            # list of occurences 5,4,3,2
            occur = Counter(i['word'] for i in temp)
            if not occur[row['word']]:
                temp.append(row)

        ok_count = len(temp)
        wrong_count = len(self.array) - len(temp)
        if ok_count == 0:
            self.status_bar.showMessage(
                self.tr("No English words"))
            self.logger.debug("No English words")
            return False
        if wrong_count > 0:
            self.logger.debug("%i words removed", wrong_count)
        self.array = temp[:]
        self.logger.debug("Words are OK")
        return True

    def kindleRepairDatabase(self):
        """
        Function for repairing malformed Kindle database
        Using portable sqlite (Lin or Windows),
        located in src/sqlite_win or src/sqlite_lin
        """
        old_name = self.file_name
        _, new_name = os.path.split(old_name)
        temp_sql = "temp.sql"

        i = 2
        temp_name = new_name
        # if vocab_new.db exists
        # give vocab_new2.db
        while os.path.exists(new_name):
            new_name = "{0}{1}.db".format(temp_name[:temp_name.index('.db')],
                                          i)
            i += 1
        # 'nt'
        sqlite_ex = self.SQLITE_PATH[os.name]

        check_call([sqlite_ex,
                    old_name,
                    ".mode insert",
                    ".output {}".format(temp_sql),
                    ".dump",
                    ".exit"])
        check_call([sqlite_ex,
                    new_name,
                    ".read {}".format(temp_sql),
                    ".exit"])
        # 1) remove temporary sql
        # 2) hide repair button
        # 3) set new file path
        os.remove(temp_sql)
        self.repair_button.hide()
        self.kindle_path.setText(new_name)
        self.status_bar.showMessage(self.tr(
            "Ready to export."))
        text = self.tr("""
            Repair was successful.<br>
            Some words are lost.<br>
            New base saved as <b>{}</b>
            Rename back to <b>vocab.db</b><br>
            and copy to Kindle.
            """.format(new_name))
        notif = NotificationDialog(title="Repair", text=text)
        notif.exec_()

    def clearMessage(self):
        """
        Clear status_bar
        """
        self.status_bar.showMessage("")

    def exportWords(self):
        """
        Preparing and exporting words
        """
        self.logger.debug("Starting export")
        email = self.email_edit.text().strip(" ")
        password = self.pass_edit.text().strip(" ")
        self.lingualeo = Lingualeo(email, password)

        # Input selected
        if self.input_radio.isChecked():
            if not self.inputOk():
                self.logger.debug("Export refused - Input")
                return
            self.status_bar.showMessage(self.tr("Input > Lingualeo"))
            word = self.input_word_edit.text().lower().strip()
            context = self.input_context_edit.text()
            self.array = [{'word': word, 'context': context}]
            before = 1
            self.logger.debug("Export Input - Ready!")

        # Text selected
        elif self.text_radio.isChecked():
            self.file_name = self.text_path.text()
            if not self.textOk():
                self.logger.debug("Export refused - Text")
                return
            self.status_bar.showMessage(self.tr("Txt > Lingualeo"))
            self.file_name = self.text_path.text()
            handler = Text(self.file_name)
            handler.read()
            self.array = handler.get()
            before = len(self.array)
            self.logger.debug("Export Text - Ready!")

        # Kindle selected
        elif self.kindle_radio.isChecked():
            self.file_name = self.kindle_path.text()
            if not self.kindleOk():
                self.logger.debug("Export refused - Kindle")
                return
            self.status_bar.showMessage(self.tr("Kindle > Lingualeo"))
            handler = Kindle(self.file_name)
            # @TEMPORARY
            # The main idea is that our user
            # wants to see the same count of words as
            # on Kindle. We don't use word but stem
            # so we temporary count distinct words.
            # Until nltk module is implemented,
            # this will be the temporary solution
            only_new_words = self.new_words_radio.isChecked()
            conn = sqlite3.connect(self.file_name)
            if only_new_words:
                command = "SELECT COUNT(DISTINCT word)\
                            FROM WORDS WHERE category = 0"
            else:
                command = "SELECT COUNT(DISTINCT word)\
                            FROM WORDS"
            cur = conn.execute(command)
            before = cur.fetchone()[0]
            handler.read(only_new_words)
            self.array = handler.get()
            self.logger.debug("Export Kindle - Ready!")
        self.logger.debug("%i words before checking", before)
        if not self.wordsOk():
            self.logger.debug("Export refused - Words")
            return
        if not self.lingualeoOk():
            self.logger.debug("Export refused - Lingualeo")
            return
        after = len(self.array)
        self.logger.debug("%i words after checking", after)
        total = before
        duplicates = before - after
        self.dialog = ExportDialog(self.array,
                                   total,
                                   duplicates,
                                   self.lingualeo)
        self.dialog.closed.connect(self.clearMessage)
        self.dialog.exec_()

    def kindleTruncate(self):
        """
        Truncate Kindle database
        Clear WORDS and LOOKUPS tables
        """
        self.file_name = self.kindle_path.text()
        if not self.file_name:
            self.status_bar.showMessage(self.tr("No Kindle database"))
            self.logger.debug("Truncate not OK - %s", self.file_name)
            return
        if not self.kindleOk():
            self.logger.debug("Truncate not OK - %s", self.file_name)
            return

        # Show warning dialog
        # @FROZEN - needs testing
        # title = self.tr("Warning")
        # text = self.tr("Before truncating turn Wi-Fi on your Kindle off.")
        # warning = NotificationDialog(title=title,
        #                             text=text)
        # warning.exec_()

        # Show additional prompt
        reply = QtGui.QMessageBox.question(
                    self, 'Message', 'Are you sure to truncate?',
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                    QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            conn = sqlite3.connect(self.file_name)
            with conn:
                conn.execute("DELETE FROM WORDS;")
                conn.execute("DELETE FROM LOOKUPS;")
                conn.execute("VACUUM;")
                # @FROZEN - for future tests
                # Seems, METADATA shouldn't be altered
                # conn.execute("UPDATE METADATA SET sscnt = 0\
                #     WHERE id in ('WORDS', 'LOOKUPS');")
                #
            self.status_bar.showMessage(self.tr("Kindle database is empty"))
            self.logger.debug("Truncate success - %s", self.file_name)
        else:
            self.logger.debug("Truncate cancelled")
            return

    def setPath(self):
        """
        Set path either for Kindle or Txt file
        """
        name = QtGui.QFileDialog.getOpenFileName(self, "Select File", "",)
        if self.kindle_radio.isChecked():
            self.kindle_path.setText(name)
        else:
            self.text_path.setText(name)
        if not self.repair_button.isHidden():
            self.repair_button.hide()
        self.clearMessage()
        self.logger.debug("Selected %s file", name)

    @staticmethod
    def showAbout():
        """
        Show dialog 'About'
        """
        about = AboutDialog()
        about.exec_()

    def initActions(self):
        """
        Init all clicks for MainWindow
        """
        self.input_radio.clicked.connect(self.checkState)
        self.text_radio.clicked.connect(self.checkState)
        self.kindle_radio.clicked.connect(self.checkState)
        self.export_button.clicked.connect(self.exportWords)
        self.kindle_truncate_button.clicked.connect(self.kindleTruncate)
        self.repair_button.clicked.connect(self.kindleRepairDatabase)
        self.kindle_button.clicked.connect(self.setPath)
        self.text_button.clicked.connect(self.setPath)
        # actions for menu
        for i in self.lang_action_group.actions():
            i.triggered.connect(self.loadTranslation)
        self.exit_action.triggered.connect(self.close)
        self.about_action.triggered.connect(self.showAbout)

    def loadTranslation(self):
        """
        Loading translation files
        """
        app = QtGui.QApplication.instance()
        self.language_translator = QtCore.QTranslator()

        if self.sender():
            self.language = self.sender().objectName()
        path = os.path.join("src", "lang", "qt_"+self.language)
        # it's important to use 'self' here - don't know why
        self.language_translator.load(path)
        app.installTranslator(self.language_translator)
        self.retranslateUI()

    def saveDefaults(self, save_email):
        """
        Save defauts:
        -email
        -password
        -language
        """
        self.settings = QtCore.QSettings(
            self.SRC, QtCore.QSettings.IniFormat
            )
        if save_email:
            self.settings.setValue("email", self.email_edit.text())
            self.settings.setValue("password", self.pass_edit.text())
        if self.language:
            self.settings.setValue("language", self.language)

    def loadDefaults(self):
        """
        Load defaults:
        -email
        -password
        -language
        """
        try:
            self.settings = QtCore.QSettings(
                self.SRC, QtCore.QSettings.IniFormat
                )
            email = self.settings.value("email")
            password = self.settings.value("password")
            language = self.settings.value("language")
            if language:
                self.language = language
            self.email_edit.setText(email)
            self.pass_edit.setText(password)
        # no ini file
        except Exception:
            self.logger.debug("Couldn't load defaults")

    def closeEvent(self, event):
        """
        Close MainWindow:
        - show Are you Sure
        - save defaults
        """
        a = AreYouSure()
        a.saved.connect(self.saveDefaults)
        a.exec_()
        event.ignore()


class Results(object):
    """
    Helper class for storing constants.
    """
    RESULTS = {'ad': "added",
               'no_ad': "not added",
               'no_tr': "no translation",
               'ex': "exists"}


class WorkThread(QtCore.QThread, Results):
    """
    Class for backgroung upload with progressbar updated
    GUI doesn't get stuck while uploading
    """
    punched = QtCore.pyqtSignal(dict)

    def __init__(self, lingualeo):
        super(WorkThread, self).__init__()
        self.lingualeo = lingualeo
        self.logger = setLogger(name='WorkThread')

    def __del__(self):
        """Delete thread"""
        self.wait()

    def run(self):
        """Run thread"""
        result = None
        row = None
        data = None
        for i in enumerate(self.array):
            try:
                word = i.get('word').lower()
                context = i.get('context', '')
                # Detect non-Unicode characters
                word.encode('ascii')
                response = self.lingualeo.get_translate(word)
                translate = response['tword']
                exist = response['is_exist']
                if exist:
                    result = self.RESULTS['ex']
                else:
                    if translate == '':
                        result = self.RESULTS['no_tr']
                    else:
                        # @TEMP solution - to detect mysterious latin
                        before = self.RESULTS['ad']
                        response = self.lingualeo.add_word(word,
                                                           translate,
                                                           context)
                        after = self.RESULTS['ad'] if \
                            response.json()['is_new'] \
                            else self.RESULTS['no_tr']
                        if before != after:
                            self.logger.debug("Mysterious - %s", word)
                        result = after

                row = {"word": word,
                       "result": result,
                       "tword": translate,
                       "context": context}
                data = {"sent": True,
                        "row": row}
            except (NoConnection, Timeout):
                data = {"sent": False,
                        "row": None}
                self.logger.debug("Couldn't upload words")
            except UnicodeEncodeError:
                row = {"word": word,
                       "result": self.RESULTS['no_tr'],
                       "tword": '',
                       "context": context}
                data = {"sent": True,
                        "row": row}
                self.logger.debug("% is not English", word)
            finally:
                self.punched.emit(data)
            time.sleep(0.1)

    def stop(self):
        """
        Stop upload - stop thread.
        """
        self.terminate()
        self.logger.debug("Stopped upload")

    def getData(self, array, index=0):
        """
        Get data from array of words.
        In case if thread was stopped, get words from
        position that is more than on previous stop
        """
        self.array = array[index:]
        self.logger.debug("Got array of %i words", len(self.array))


class ExportDialog(CustomDialog, Results):
    """
    Dialog for exporting words.
    Shows information about user.
    Shows count of words.
    Warns if meatballs < words.
    Progressbar and two buttons - Start/Stop and Break
    """

    ICON_FILE = os.path.join("src", "pics", "export.ico")
    closed = QtCore.pyqtSignal()

    def __init__(self, array, total, duplicates, lingualeo):
        """
        Initializing ExportDialog.
        Get the following values:
        -array of dictinaries:
            {
             "word":word,
             "context:context
            }
        -count of words before checking
        -count of duplicates
        -lingualeo API
        """
        super(ExportDialog, self).__init__()
        self.array = array
        self.total = total
        self.duplicates = duplicates
        self.stat = []
        self.value = 0
        self.task = WorkThread(lingualeo)
        self.task.getData(array)
        self.words_count = len(self.array)
        self.lingualeo = lingualeo
        self.logger = setLogger(name='Export')
        self.initUI()
        self.retranslateUI()
        self.initActions()
        self.logger.debug("Inited ExportDialog")

    def initUI(self):
        """
        Construct ExportDialog GUI
        """
        layout = QtGui.QVBoxLayout()

        info_layout = QtGui.QVBoxLayout()
        self.avatar_label = QtGui.QLabel()

        info_grid_layout = QtGui.QGridLayout()
        self.fname_title_label = QtGui.QLabel()
        self.fname_value_label = QtGui.QLabel()
        info_grid_layout.addWidget(self.fname_title_label, 0, 0)
        info_grid_layout.addWidget(self.fname_value_label, 0, 1)
        self.lvl_title_label = QtGui.QLabel()
        self.lvl_value_label = QtGui.QLabel()
        info_grid_layout.addWidget(self.lvl_title_label, 1, 0)
        info_grid_layout.addWidget(self.lvl_value_label, 1, 1)
        self.meatballs_title_label = QtGui.QLabel()
        self.meatballs_value_label = QtGui.QLabel()
        info_grid_layout.addWidget(self.meatballs_title_label, 2, 0)
        info_grid_layout.addWidget(self.meatballs_value_label, 2, 1)
        self.total_words_title_label = QtGui.QLabel()
        self.total_words_value_label = QtGui.QLabel()
        info_grid_layout.addWidget(self.total_words_title_label, 3, 0)
        info_grid_layout.addWidget(self.total_words_value_label, 3, 1)
        self.duplicate_words_title_label = QtGui.QLabel()
        self.duplicate_words_value_label = QtGui.QLabel()
        info_grid_layout.addWidget(self.duplicate_words_title_label, 4, 0)
        info_grid_layout.addWidget(self.duplicate_words_value_label, 4, 1)
        self.prepared_words_title_label = QtGui.QLabel()
        self.prepared_words_value_label = QtGui.QLabel()
        info_grid_layout.addWidget(self.prepared_words_title_label, 5, 0)
        info_grid_layout.addWidget(self.prepared_words_value_label, 5, 1)

        info_layout.addWidget(self.avatar_label)
        info_layout.addLayout(info_grid_layout)

        warning_layout = QtGui.QHBoxLayout()
        self.warning_info_label = QtGui.QLabel()
        self.warning_info_label.setAlignment(QtCore.Qt.AlignCenter)
        self.warning_info_label.setFrameShape(QtGui.QFrame.WinPanel)
        self.warning_info_label.setFrameShadow(QtGui.QFrame.Raised)
        self.warning_info_label.hide()
        warning_layout.addWidget(self.warning_info_label)

        progress_layout = QtGui.QVBoxLayout()
        hor_layout = QtGui.QHBoxLayout()
        self.progress_bar = QtGui.QProgressBar(self)
        self.progress_bar.setRange(0, self.words_count)
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)
        self.start_button = QtGui.QPushButton()
        self.start_button.setObjectName("start")
        self.break_button = QtGui.QPushButton()
        self.break_button.setObjectName("break")

        progress_layout.addWidget(self.progress_bar)
        hor_layout.addWidget(self.start_button)
        hor_layout.addWidget(self.break_button)
        progress_layout.addLayout(hor_layout)

        h_line = createSeparator()
        layout.addLayout(info_layout)
        layout.addLayout(warning_layout)
        layout.addWidget(h_line)
        layout.addLayout(progress_layout)

        self.setLayout(layout)
        self.break_button.hide()

    def retranslateUI(self):
        """
        Set texts for buttons/labels of ExportDialog
        """
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        avatar = QtGui.QPixmap()
        avatar.loadFromData(self.lingualeo.avatar)
        self.avatar_label.setPixmap(avatar)
        self.avatar_label.setAlignment(QtCore.Qt.AlignCenter)
        # self.avatar_label.setScaledContents(True)

        # INFO GRID
        self.fname_title_label.setText(
            self.tr("Name:"))
        self.fname_value_label.setText(
            self.lingualeo.fname)

        self.lvl_title_label.setText(
            self.tr("Lvl:"))
        self.lvl_value_label.setText(
            str(self.lingualeo.lvl))

        self.meatballs_title_label.setText(
            self.tr("Meatballs:"))
        self.meatballs_value_label.setText(
            str(self.lingualeo.meatballs))
        if not self.lingualeo.isEnoughMeatballs(self.words_count):
            self.warning_info_label.setText(
                self.tr("WARNING: Meatballs < words"))
            self.warning_info_label.setStyleSheet("color:red;font-weight:bold")
            self.warning_info_label.show()
        self.total_words_title_label.setText(
            self.tr("Total words:"))
        self.total_words_value_label.setText(
            str(self.total))
        self.duplicate_words_title_label.setText(
            self.tr("Duplicates removed:"))
        self.duplicate_words_value_label.setText(
            str(self.duplicates))
        self.prepared_words_title_label.setText(
            self.tr("Prepared to export:"))
        self.prepared_words_value_label.setText(
            str(self.words_count))
        self.setWindowTitle(
            self.tr("Preparing to export"))
        self.start_button.setText(
            self.tr("Start"))
        self.break_button.setText(
            self.tr("Break"))

    def initActions(self):
        """
        Initializing actions for ExportDialog
        Start button starts task.
        Break button stops task and closes the ExportDialog
        """
        self.start_button.clicked.connect(self.changeTask)
        self.break_button.clicked.connect(self.task.stop)
        self.break_button.clicked.connect(self.close)
        self.task.punched.connect(self.onProgress)

    def keyPressEvent(self, event):
        """
        Exit by Esc pressed.
        """
        if event.key() == QtCore.Qt.Key_Escape:
            self.task.stop()
            self.close()

    def closeEvent(self, event):
        """
        Close ExportDialog.
        -stop task.
        -show statistics.
        -close dialog.
        """
        event.accept()
        self.task.stop()
        s = StatisticsDialog(self.stat)
        s.exec_()
        self.closed.emit()

    def changeTask(self):
        """
        If Start button clicked:
        -set 'Stop'.
        -change title.
        -show 'Break'.
        -start task.
        If Stop button clicked:
        -stop task.
        -set 'Start'
        """
        if self.sender().objectName() == "start":
            self.start_button.setText(self.tr("Stop"))
            self.start_button.setObjectName("stop")
            self.break_button.show()
            self.setWindowTitle(self.tr("Processing..."))
            if self.value > 0:
                self.task.getData(self.array, self.value)
            self.task.start()
        else:
            self.task.stop()
            self.start_button.setText(self.tr("Start"))
            self.start_button.setObjectName("start")

    def finish(self):
        """
        Process finish:
        -set 'Finished' and 'Close'
        """
        self.progress_bar.setFormat(self.tr("Finished"))
        self.break_button.setText(self.tr("Close"))
        self.start_button.hide()

    def onProgress(self, data):
        """
        Process every word.
        """
        if data['sent']:
            row = data['row']
            if (row['result'] == self.RESULTS['ad'] and
                    not self.lingualeo.premium):

                self.lingualeo.meatballs -= 1
                self.meatballs_value_label.setText(
                    str(self.lingualeo.meatballs))
        else:
            self.start_button.click()
            warning = NotificationDialog(self.tr("Internet error"),
                                         self.tr("No Internet Connection"))
            warning.exec_()
            self.logger.debug("No connection")
            return

        self.stat.append(data['row'])
        self.value += 1
        self.progress_bar.setValue(self.value)
        self.progress_bar.setFormat(
            self.tr("{0} words processed "
                    "out of {1}").format(self.value,
                                         self.words_count))
        if self.lingualeo.meatballs == 0:
            self.task.stop()
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.warning_info_label.setText(
                self.tr("No meatballs. Upload stopped"))
            for i in self.array[self.value:]:
                self.stat.append({"word": i['word'],
                                  "result": self.RESULTS['no_ad'],
                                  "tword": "",
                                  "context": i['context']})
            self.logger.debug("0 meatballs. Upload stopped")
            self.finish()
            return

        # 100%
        if self.progress_bar.value() == self.progress_bar.maximum():
            self.logger.debug("%i words tried to upload", self.value)
            self.finish()


class StatisticsDialog(CustomFullDialog, Results):
    """
    Dialog for showing results of export.
    """
    ICON_FILE = os.path.join("src", "pics", "statistics.ico")

    def __init__(self, stat):
        """
        Initializing StatisticsDialog.
        Get list of dictionaries:
        {"word": word,
         "result": result,
         "tword": translate,
         "context": context}        
        """
        super(StatisticsDialog, self).__init__()
        self.logger = setLogger(name="Statistics")
        self.colors = []
        self.texts = []
        self.values = []
        self.stat = stat
        self.initUI()
        self.retranslateUI()
        self.logger.debug("Inited Statistics")

    def initUI(self):
        """Construct StatisticsDialog GUI"""
        self.list_view = QtGui.QListWidget()
        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(3)
        stat = sorted(self.stat, key=itemgetter('result'))
        for item in stat:
            if item.get("result") == self.RESULTS['ad']:
                brush = QtCore.Qt.green
            elif item.get("result") == self.RESULTS['no_tr']:
                brush = QtCore.Qt.yellow
            elif item.get("result") == self.RESULTS['no_ad']:
                brush = QtCore.Qt.white
            else:
                brush = QtCore.Qt.red
            word = QtGui.QTableWidgetItem(item.get("word"))
            translate = QtGui.QTableWidgetItem(item.get("tword"))
            context = QtGui.QTableWidgetItem(item.get('context'))
            word.setBackgroundColor(brush)
            translate.setBackgroundColor(brush)
            context.setBackgroundColor(brush)
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, word)
            self.table.setItem(row_position, 1, translate)
            self.table.setItem(row_position, 2, context)
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.table.resizeColumnsToContents()
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)

        self.grid = self.createGrid()
        self.layout = QtGui.QVBoxLayout()
        self.layout.addLayout(self.grid)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

    def createGrid(self):
        """Create grid for info about user/words/etc"""
        total = len(self.stat)
        result = Counter(i["result"] for i in self.stat)
        added = result[self.RESULTS['ad']]
        not_added = result[self.RESULTS['no_ad']]
        wrong = result[self.RESULTS['no_tr']]
        exist = len(self.stat) - (added+not_added) - wrong
        grid = QtGui.QGridLayout()

        data = [
                {"text": self.tr("Total"),
                 "value": total,
                 "color": ""},
                {"text": self.tr("Added"),
                 "value": added,
                 "color": "lime"},
                {"text": self.tr("Exist"),
                 "value": exist,
                 "color": "red"},
                {"text": self.tr("No translation"),
                 "value": wrong, "color": "yellow"},
                {"text": self.tr("Not added"),
                 "value": not_added,
                 "color": "white"}
               ]

        for index, i in enumerate(data):
            color_label = QtGui.QLabel()
            color_label.setStyleSheet(
                "background-color:{0}".format(i['color']))
            text_label = QtGui.QLabel()
            value_label = QtGui.QLabel()
            text_label.setText("{}".format(i['text']))
            value_label.setText("{}".format(i['value']))

            self.colors.append(color_label)
            self.texts.append(text_label)
            self.values.append(value_label)
            grid.addWidget(color_label, index, 0)
            grid.addWidget(text_label, index, 1)
            grid.addWidget(value_label, index, 2)

        return grid

    def resizeEvent(self, event):
        """
        Make table resize when user changes size of dialog.
        """
        self.table.resizeRowsToContents()
        event.accept()

    def retranslateUI(self):
        """
        Set icon and title.
        """
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.setWindowTitle(self.tr("Statistics"))


class ExceptionDialog(QtGui.QDialog):
    """
    Dialog for showing errors (exceptions) to user
    """
    ICON_FILE = os.path.join("src", "pics", "error.ico")
    EMAIL = "GriefMontana@gmail.com"

    def __init__(self, short_trace, full_trace):
        """
        Initializing ExceptionDialog.
        Get full exception message and exception name.
        """
        super(ExceptionDialog, self).__init__()
        self.full = full_trace+"\n\n" + short_trace
        self.initUI()
        self.retranslateUI()
        self.initActions()

    def initUI(self):
        """
        Construct ExceptionDialog GUI.
        """
        self.error_label = QtGui.QLabel()
        self.more_edit = QtGui.QTextEdit()
        self.more_edit.setReadOnly(True)
        self.more_edit.hide()
        self.show_hide_button = QtGui.QPushButton()
        self.show_hide_button.setIcon(QtGui.QIcon.fromTheme("go-down"))
        self.ok_button = QtGui.QPushButton()
        self.send_button = QtGui.QPushButton()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.error_label)
        layout.addWidget(self.show_hide_button)
        layout.addWidget(self.more_edit)
        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.send_button)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def retranslateUI(self):
        """
        Set texts for buttons/labels of ExceptionDialog.
        """
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.setWindowTitle(self.tr("Error"))
        short_text = self.tr("An error occured. Kindleo terminated.")
        self.error_label.setText(short_text)
        self.more_edit.setText(self.full)
        self.show_hide_button.setText(self.tr("Show details..."))
        self.ok_button.setText("OK")
        send_link = "mailto:{0}?subject="\
                    "Kindleo bug&body={1}".format(self.EMAIL, self.full)
        self.send_button.setText(self.tr("Send report"))
        self.send_button.setObjectName(send_link)

    def changeHider(self):
        """
        Show/hide exception message.
        """
        if self.more_edit.isHidden():
            icon = QtGui.QIcon.fromTheme("go-up")
            self.show_hide_button.setText(self.tr("Hide"))
            self.more_edit.show()
        else:
            icon = QtGui.QIcon.fromTheme("go-down")
            self.show_hide_button.setText(self.tr("Show details..."))
            self.more_edit.hide()
            for _ in range(0, 10):
                QtGui.QApplication.processEvents()
            self.resize(self.minimumSizeHint())
        self.show_hide_button.setIcon(icon)

    def sendEmail(self):
        """
        Send e-mail to developer.
        """
        link = self.sender().objectName()
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))

    def initActions(self):
        """
        Actions for Ok/Show/Send
        """
        self.ok_button.clicked.connect(self.close)
        self.send_button.clicked.connect(self.sendEmail)
        self.show_hide_button.clicked.connect(self.changeHider)


def exceptionHook(exctype, ex, tb):
    """
    Function for showing silenced exceptions
    Default behaviour for exceptions in PyQt4 is:
    -exception raises but the programm keeps running
    We don't need this, so new behaviour is:
    -exception raises - the programm closes
    """

    logger = setLogger(name='exception')
    sys._excepthook(exctype, ex, tb)
    full_trace = ''.join(traceback.format_tb(tb))
    short_trace = '{0}: {1}'.format(exctype, ex)
    logger.critical(full_trace)
    logger.critical(short_trace)
    exc_dialog = ExceptionDialog(short_trace, full_trace)
    exc_dialog.exec_()
    sys.exit(1)


def detectOtherVersions():
    """
    Function for prevening running different version of Kindleo,
    such as Kindleo_0.9.6, 0.9.7 and so on.
    """
    counter = 0
    for i in psutil.pids():
        try:
            if ('Kindleo' in psutil.Process(i).name() or
                    any('gui_export' in p for
                        p in psutil.Process(i).cmdline())):

                counter += 1
        except psutil.NoSuchProcess:
            continue
    if counter > 2:
        title = "Multiple instances"
        text = "The program is already running"
        notif = NotificationDialog(title, text)
        notif.exec_()
        sys.exit(1)


def main():

    # Let only one instance of program running
    # this version.
    # Pylint cares about 'defined but not used', so
    # we desable this check
    # also we add 'noqa' for pyflakes
    # pylint: disable=W0612
    single = singleton.SingleInstance()  # noqa
    # pylint: enable=W0612
    # other versions
    detectOtherVersions()

    app = QtGui.QApplication(sys.argv)
    # don't let closing the whole app after any dialog closed
    app.setQuitOnLastWindowClosed(False)
    logger = setLogger(name='main')

    # excepthook to show silenced exceptions
    sys._excepthook = sys.excepthook
    sys.excepthook = exceptionHook

    logger.debug("New session started")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
