# !/usr/bin/env python
"""
Usage: python gui_export.py

===GUI version of lingualeo.export===
"""

import sys
import os
import sqlite3
import time
from PyQt4 import QtCore, QtGui
from requests.exceptions import ConnectionError as NoConnection, Timeout

from collections import Counter
from operator import itemgetter
from word import Kindle, Text
from service import Lingualeo
from log_conf import setLogger
'''
@FROZEN
from pydub import AudioSegment
from pydub.playback import play
'''


def centerUI(self):
    """place UI in the middle of the screen"""
    qr = self.frameGeometry()
    cp = QtGui.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())

def createSeparator():
    separator = QtGui.QFrame()
    separator.setFrameShape(QtGui.QFrame.HLine)
    separator.setFrameShadow(QtGui.QFrame.Sunken)
    return separator

'''
@FROZEN
def playSound(name):
    """left for future sound notifications"""
    pass
'''


class WinDialog(QtGui.QDialog):

    def __init__(self):
        super(WinDialog, self).__init__()
        windowFlags = self.windowFlags()
        windowFlags &= ~QtCore.Qt.WindowMaximizeButtonHint
        windowFlags &= ~QtCore.Qt.WindowMinMaxButtonsHint
        windowFlags &= ~QtCore.Qt.WindowContextHelpButtonHint
        windowFlags |= QtCore.Qt.WindowMinimizeButtonHint
        self.setWindowFlags(windowFlags)

if os.name == 'nt':
    CustomDialog = WinDialog
else:
    CustomDialog = QtGui.QDialog


class AboutDialog(CustomDialog):
    """about authors etc"""
    ICON_FILE = os.path.join("src", "pics", "about.ico")
    ICON_LING_FILE = os.path.join("src", "pics", "lingualeo.ico")

    def __init__(self):
        super(AboutDialog, self).__init__()
        self.initUI()
        self.retranslateUI()
        self.initActions()
        centerUI(self)

    def initUI(self):
        layout = QtGui.QVBoxLayout()
        self.icon_label = QtGui.QLabel()
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        self.version_label = QtGui.QLabel()
        self.version_label.setAlignment(QtCore.Qt.AlignCenter)
        self.about_label = QtGui.QLabel()

        self.ok_button = QtGui.QPushButton()
        layout.addWidget(self.icon_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.about_label)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def retranslateUI(self):
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.setWindowTitle(self.tr("About"))
        self.icon_label.setPixmap(QtGui.QPixmap(self.ICON_LING_FILE))
        self.version_label.setText("Kindleo 0.9.3 beta")
        self.about_label.setText(self.tr(
            """
            <span>
            <center>
            GUI version of script for exporting<br>
            words to Lingualeo from Input, Txt file or<br>
            Kindle vocabulary.<br>
            Specially for users of The-Ebook Amazon forum.
            <br><br>
            <b>Original idea</b><br>Ilya Isaev<br><br>
            <b>GUI and some improvements:</b><br> Grigoriy Melnichenko
            </center>
            </span>
            """
            ))
        self.ok_button.setText(self.tr("OK"))

    def initActions(self):
        self.ok_button.clicked.connect(self.close)


class AreYouSure(CustomDialog):
    """exit dialog"""
    ICON_FILE = os.path.join("src", "pics", "exit.ico")
    saved = QtCore.pyqtSignal(bool)

    def __init__(self):
        super(AreYouSure, self).__init__()
        self.initUI()
        self.retranslateUI()
        self.initActions()

    def initUI(self):
        self.setWindowFlags(self.windowFlags() \
            & ~QtCore.Qt.WindowContextHelpButtonHint)
        layout = QtGui.QVBoxLayout()
        hor_lay = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel()
        self.check_item = QtGui.QCheckBox()
        self.yes_button = QtGui.QPushButton()
        self.no_button = QtGui.QPushButton()
        hor_lay.addWidget(self.yes_button)
        hor_lay.addWidget(self.no_button)
        layout.addWidget(self.check_item)
        layout.addWidget(self.label)
        layout.addLayout(hor_lay)
        self.setLayout(layout)

    def retranslateUI(self):
        self.setWindowTitle(self.tr("Exit"))
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.label.setText(self.tr("Are you sure to quit?"))
        self.yes_button.setText(self.tr("Yes"))
        self.no_button.setText(self.tr("No"))
        self.check_item.setText(self.tr("Save e-mail/password"))

    def exit(self):
        """handle correct exit"""
        save_email = self.check_item.isChecked()
        self.saved.emit(save_email)
        QtGui.QApplication.quit()

    def initActions(self):
        self.yes_button.clicked.connect(self.exit)
        self.no_button.clicked.connect(self.close)


class NotificationDialog(CustomDialog):
    """dialog for notifications - 'Connection Lost' etc"""
    ICON_FILE = os.path.join("src", "pics", "warning.ico")

    def __init__(self, text):
        super(NotificationDialog, self).__init__()
        self.text = text
        self.initUI()
        self.retranslateUI()
        self.initActions()

    def initUI(self):
        layout = QtGui.QVBoxLayout()
        self.label = QtGui.QLabel()
        self.ok_button = QtGui.QPushButton()
        layout.addWidget(self.label)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def retranslateUI(self):
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.label.setText(self.text)
        self.ok_button.setText("OK")

    def initActions(self):
        self.ok_button.clicked.connect(self.close)


class MainWindow(QtGui.QMainWindow):
    """main window"""
    ICON_FILE = os.path.join("src", "pics", "lingualeo.ico")
    SRC = os.path.join("src", "src.ini")

    def __init__(self, source='input'):
        super(MainWindow, self).__init__()
        self.source = source
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
        self.logger.debug("Created MenuBar")

    def initUI(self):
        self.main_widget = QtGui.QWidget(self)
        self.main_layout = QtGui.QVBoxLayout()

        self.auth_layout = QtGui.QGridLayout()
        self.auth_label = QtGui.QLabel()
        self.email_label = QtGui.QLabel()
        self.email_edit = QtGui.QLineEdit()
        self.email_edit.setObjectName('email')
        self.pass_label = QtGui.QLabel()
        self.pass_edit = QtGui.QLineEdit()
        self.pass_edit.setObjectName('pass')
        self.auth_layout.addWidget(self.email_label, 0, 0, 1, 1)
        self.auth_layout.addWidget(self.email_edit, 0, 1, 1, 1)
        self.auth_layout.addWidget(self.pass_label, 1, 0, 1, 1)
        self.auth_layout.addWidget(self.pass_edit, 1, 1, 1, 1)

        self.main_label = QtGui.QLabel()

        self.input_radio = QtGui.QRadioButton()
        self.input_radio.setObjectName("input")
        self.input_radio.setChecked(True)
        self.input_word_label = QtGui.QLabel()
        self.input_context_label = QtGui.QLabel()
        self.input_word_edit = QtGui.QLineEdit()
        self.input_context_edit = QtGui.QLineEdit()
        self.input_layout = QtGui.QGridLayout()
        self.input_layout.addWidget(self.input_word_label, 0, 0, 1, 1)
        self.input_layout.addWidget(self.input_word_edit, 0, 1, 1, 1)
        self.input_layout.addWidget(self.input_context_label, 1, 0, 1, 1)
        self.input_layout.addWidget(self.input_context_edit, 1, 1, 1, 1)
        self.text_radio = QtGui.QRadioButton()
        self.text_radio.setObjectName("text")
        self.text_push = QtGui.QPushButton()
        self.text_path = QtGui.QLineEdit()
        self.text_path.setReadOnly(True)
        self.text_layout = QtGui.QHBoxLayout()
        self.text_layout.addWidget(self.text_push)
        self.text_layout.addWidget(self.text_path)

        self.kindle_radio = QtGui.QRadioButton()
        self.kindle_radio.setObjectName("kindle")
        self.kindle_hint = QtGui.QLabel()
        self.kindle_push = QtGui.QPushButton()
        self.kindle_path = QtGui.QLineEdit()
        self.kindle_path.setReadOnly(True)
        self.kindle_words_layout = QtGui.QHBoxLayout()
        self.all_words_radio = QtGui.QRadioButton()
        self.all_words_radio.setChecked(True)
        self.new_words_radio = QtGui.QRadioButton()
        self.words_radio_group = QtGui.QButtonGroup()
        self.words_radio_group.addButton(self.all_words_radio)
        self.words_radio_group.addButton(self.new_words_radio)
        self.kindle_layout = QtGui.QGridLayout()
        self.kindle_layout.addWidget(self.kindle_push, 0, 0)
        self.kindle_layout.addWidget(self.kindle_path, 0, 1)
        self.kindle_layout.addWidget(self.all_words_radio, 1, 0, 1, 0)
        self.kindle_layout.addWidget(self.new_words_radio, 2, 0, 1, 0)

        self.export_push = QtGui.QPushButton()
        self.truncate_push = QtGui.QPushButton()
        self.truncate_push.setEnabled(False)
        # @FROZEN
        # self.repair_push = QtGui.QPushButton()
        # self.repair_push.hide()
        self.bottom_layout = QtGui.QHBoxLayout()
        self.bottom_layout.addWidget(self.export_push)
        self.bottom_layout.addWidget(self.truncate_push)
        # @FROZEN
        # self.bottom_layout.addWidget(self.repair_push)

        self.source_group = QtGui.QButtonGroup()
        self.source_group.addButton(self.input_radio)
        self.source_group.addButton(self.text_radio)
        self.source_group.addButton(self.kindle_radio)

        h_lines = []
        for i in range(4):
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
        self.logger.debug("Constructed UI")

    def retranslateUI(self):
        self.setWindowTitle(self.tr("Export to Lingualeo"))
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.email_label.setText("e-mail")
        self.pass_label.setText("password")
        self.main_label.setText(self.tr("<center>Choose the source</center>"))
        self.input_radio.setText(self.tr("Input"))
        self.input_word_label.setText(self.tr("word"))
        self.input_context_label.setText(self.tr("context"))

        self.text_radio.setText(self.tr("Text"))
        self.text_push.setText(self.tr("Path"))

        self.kindle_radio.setText(self.tr("Kindle"))
        self.kindle_hint.setText(self.tr(
            "Base is here:<br>Kindle/system/vocabulary/vocab.db"))
        self.all_words_radio.setText(self.tr("All words (recommended)"))
        self.new_words_radio.setText(self.tr("Only new"))
        self.new_words_radio.setToolTip(self.tr("Words, marked for learning"))
        self.kindle_push.setText(self.tr("Path"))

        self.export_push.setText(self.tr("Export"))
        self.truncate_push.setText(self.tr("Truncate"))
        # @FROZEN
        # self.repair_push.setText(self.tr("Repair"))

        # retranslate menu
        self.main_menu.setTitle(self.tr("Main menu"))
        self.language_menu.setTitle(self.tr("Language"))
        self.exit_action.setText(self.tr("Exit"))

        self.help_menu.setTitle(self.tr("Help"))
        self.about_action.setText(self.tr("About"))

        self.setFixedHeight(self.sizeHint().height())
        self.logger.debug("Retranslated UI")

    def setValidators(self):
        """
        Set validators to all input fields to
        prevent incorrect input value
        """
        regexp = QtCore.QRegExp("^[a-zA-Z`'-]+(\s+[a-zA-Z`'-]+)*$")
        validator = QtGui.QRegExpValidator(regexp)
        self.input_word_edit.setValidator(validator)
        self.logger.debug("Set validators for input")

    def checkState(self):
        input_state = self.input_radio.isChecked()
        text = self.text_radio.isChecked()
        kindle = self.kindle_radio.isChecked()

        self.input_word_edit.setEnabled(input_state)
        self.input_context_edit.setEnabled(input_state)
        self.input_word_label.setEnabled(input_state)
        self.input_context_label.setEnabled(input_state)
        self.text_push.setEnabled(text)
        self.text_path.setEnabled(text)
        self.kindle_hint.setEnabled(kindle)
        self.all_words_radio.setEnabled(kindle)
        self.new_words_radio.setEnabled(kindle)
        self.kindle_push.setEnabled(kindle)
        self.kindle_path.setEnabled(kindle)
        self.logger.debug("Finished checkof elements state - Disabled/Enabled")

    def lingualeoOk(self):
        """check if lingualeo is suitable for export"""
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
        return True

    def textOk(self):
        """check if text is OK"""
        path = self.text_path.text()
        self.logger.debug("Checking TXT - {0}".self.logger.debug(path))
        _, ext = os.path.splitext(path)
        if ext != '.txt':
            self.status_bar.showMessage(
                self.tr("Not txt file"))
            self.logger.debug("{0} - is not TXT".format(path))
            return False
        if os.stat(path).st_size == 0:
            self.status_bar.showMessage(self.tr("Txt file is empty"))
            self.logger.debug("{0} - TXT is empty".format(path))
            return False
        self.logger.debug("{0} - TXT is OK".format(path))
        return True

    def kindleOk(self):
        """kindle handler"""

        path = self.kindle_path.text()
        self.logger.debug("Checking Kindle - {0}".format(path))
        # no path
        if not path:
            self.status_bar.showMessage(self.tr("No Kindle database"))
            self.logger.debug("{0} - no path")
            return False

        # not valid database
        _, ext = os.path.splitext(path)
        if ext != '.db':
            self.status_bar.showMessage(
                self.tr("Not valid file format"))
            self.logger.debug("{0} - not '.db'")
            return False

        # check database
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        data = None
        try:
            data = cursor.execute("SELECT * FROM WORDS")
        # no table WORDS
        except sqlite3.OperationalError:
            self.status_bar.showMessage(
                self.tr("Not valid database"))
            self.logger.debug("{0} - no WORDS table".format(path))
            return False
        # database is malformed
        except sqlite3.DatabaseError:
            self.status_bar.showMessage(
                self.tr("Kindle database is malformed"))
            self.logger.debug("{0} is malformed".format(path))
            return False
        # database is empty
        if not data:
            self.status_bar.showMessage(
                self.tr("Kindle database is empty"))
            self.logger.debug("{0} has WORDS but is empty".format(path))
            return False
        self.logger.debug("{0} - DB is OK".format(path))
        return True

    def wordsOk(self):
        """get rid of non-English words"""
        temp = []
        for row in self.array:
            # remove repeated words
            # list of occurences 5,4,3,2
            occur = Counter(i['word'] for i in temp)
            row['word'].encode('ascii')
            if not occur[row['word']]:
                temp.append(row)

        ok_count = len(temp)
        wrong_count = len(self.array) - len(temp)
        if ok_count == 0:
            self.status_bar.showMessage(
                self.tr("No English words"))
            self.logger.debug("{0} has no English".format(temp))
            return False
        if wrong_count > 0:
            self.logger.debug("{0} words removed".format(
                wrong_count))
        self.array = temp[:]
        self.logger.debug("Words are OK")
        return True
    '''
    @FROZEN
    def kindleRepairDatabase(self):
        """tool for repairing Kindle db"""

        old_name = self.file_name
        conn = sqlite3.connect(old_name)
        new_name = "{0}_new.db".format(
            old_name[:-old_name.rindex('.')])
        temp_sql = "temp.sql"
        i = 0
        while os.path.exists(new_name):
            new_name = "{0}{1}".format(
                new_name[:-new_name.rindex('.'), i])
            i += 1
        with conn:
            conn.execute(".output {0}".format(temp_sql))
            conn.execute(".dump")
        conn = sqlite3.connect(new_name)
        sql = None
        with open(temp_sql) as f:
            sql = f.read()
        conn.executescript(sql)
        conn.commit()
        os.remove(temp_sql)
        self.repair_push.hide()
        self.status_bar.showMessage(self.tr(
            "Base repaired. Try to export"))
    '''

    def getSource(self):

        source = self.sender().objectName()

        if 'kindle' not in source:
            self.truncate_push.setEnabled(False)
        else:
            self.truncate_push.setEnabled(True)
        self.source = source
        self.logger.debug("Selected {0}".format(source))
        self.checkState()

    def clearMessage(self):
        self.status_bar.showMessage("")
        self.logger.debug("Status bar cleared")

    def exportWords(self):
        """kidle/input/word"""
        self.logger.debug("Starting export")
        kindle = self.kindle_radio.isChecked()
        input_word = self.input_radio.isChecked()
        text = self.text_radio.isChecked()
        email = self.email_edit.text().strip(" ")
        password = self.pass_edit.text().strip(" ")
        self.lingualeo = Lingualeo(email, password)

        if not self.lingualeoOk():
            self.logger.debug("Export refused - Text")
            return

        if input_word:
            self.status_bar.showMessage(self.tr("Input > Lingualeo"))
            word = self.input_word_edit.text().lower().strip()
            context = self.input_context_edit.text()
            self.array = [{'word': word, 'context': context}]
            self.logger.debug("Export Input - Ready!")
        elif text:
            if not self.textOk():
                self.logger.debug("Export refused - Text")
                return
            self.file_name = self.text_path.text()
            self.status_bar.showMessage(self.tr("Txt > Lingualeo"))
            self.file_name = self.text_path.text()
            handler = Text(self.file_name)
            handler.read()
            self.array = handler.get()
            self.logger.debug("Export Text - Ready!")

        elif kindle:
            if not self.kindleOk():
                self.logger.debug("Export refused - Kindle")
                return
            self.file_name = self.kindle_path.text()
            self.status_bar.showMessage(self.tr("Kindle > Lingualeo"))
            handler = Kindle(self.file_name)
            handler.read(only_new_words=self.new_words_radio.isChecked())
            self.array = handler.get()
            self.logger.debug("Export Kindle - Ready!")
        before = len(self.array)
        self.logger.debug("{0} words before checking".format(before))
        if not self.wordsOk():
            self.logger.debug("Export refused - Words")
            return
        after = len(self.array)
        self.logger.debug("{0} words after checking".format(after))
        total = before
        duplicates = before - after
        try:
            dialog = ExportDialog(self.array, total, duplicates, self.lingualeo)
            dialog.closed.connect(self.clearMessage)
            dialog.exec_()
        except Exception:
            self.logger.exception("Dialog Exception")
            sys.exit()

    def kindleTruncate(self):
        """truncate kindle database"""
        self.file_name = self.kindle_path.text()
        if not self.file_name:
            self.status_bar.showMessage(self.tr("No Kindle database"))
            self.logger.debug("Truncate not OK - {0}".format(self.file_name))
            return
        if not self.kindleOk():
            self.logger.debug("Truncate not OK - {0}".format(self.file_name))
            return
        reply = QtGui.QMessageBox.question(
                    self, 'Message', 'Are you sure to truncate?',
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                    QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            conn = sqlite3.connect(self.file_name)
            with conn:
                conn.execute("DELETE FROM WORDS;")
                conn.execute("DELETE FROM LOOKUPS;")
                conn.execute("UPDATE METADATA SET sscnt = 0\
                                WHERE id in ('WORDS', 'LOOKUPS');")
                conn.execute("VACUUM;")
                conn.commit()
            self.status_bar.showMessage(self.tr("Kindle database is empty"))
            self.logger.debug("Truncate success - {0}".format(self.file_name))
        else:
            self.logger.debug("Truncate cancelled")
            return

    def setPath(self):

        name = QtGui.QFileDialog.getOpenFileName(self, "Select File", "",)
        if self.kindle_radio.isChecked():
            self.kindle_path.setText(name)
        else:
            self.text_path.setText(name)
        self.logger.debug("Selected {0} file".format(name))

    def showAbout(self):
        about = AboutDialog()
        about.exec_()

    def initActions(self):
        self.input_radio.clicked.connect(self.getSource)
        self.text_radio.clicked.connect(self.getSource)
        self.kindle_radio.clicked.connect(self.getSource)
        self.export_push.clicked.connect(self.exportWords)
        self.truncate_push.clicked.connect(self.kindleTruncate)
        # @FROZEN
        # self.repair_push.clicked.connect(self.kindleRepairDatabase)
        self.kindle_push.clicked.connect(self.setPath)
        self.text_push.clicked.connect(self.setPath)
        # actions for menu
        for i in self.lang_action_group.actions():
            i.triggered.connect(self.loadTranslation)
        self.exit_action.triggered.connect(self.close)
        self.about_action.triggered.connect(self.showAbout)
        self.logger.debug("Inited actions")

    def loadTranslation(self):
        app = QtGui.QApplication.instance()
        self.language_translator = QtCore.QTranslator()

        if self.sender():
            self.language = self.sender().objectName()
        path = os.path.join("src", "lang", "qt_"+self.language)
        # it's important to use 'self' here - don't know why
        self.language_translator.load(path)
        app.installTranslator(self.language_translator)
        self.retranslateUI()
        self.logger.debug("Loaded translation")

    def saveDefaults(self, save_email):
        '''save default email and password'''
        self.settings = QtCore.QSettings(
            self.SRC, QtCore.QSettings.IniFormat
            )
        if save_email:
            self.settings.setValue("email", self.email_edit.text())
            self.settings.setValue("password", self.pass_edit.text())
        if self.language:
            self.settings.setValue("language", self.language)
        self.logger.debug("Saved default email and password")

    def loadDefaults(self):
        '''load default email/password and language'''
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
        self.logger.debug("Loaded default email/pass/lang")

    def closeEvent(self, event):
        a = AreYouSure()
        a.saved.connect(self.saveDefaults)
        a.exec_()
        event.ignore()


class Results:
    RESULTS = {'ad': "added",
               'no_ad': "not added",
               'no_tr': "no translation",
               'ex': "exists"}


class WorkThread(QtCore.QThread, Results):

    punched = QtCore.pyqtSignal(dict)

    def __init__(self, lingualeo):
        super(WorkThread, self).__init__()
        self.lingualeo = lingualeo
        self.logger = setLogger(name='WorkThread')

    def __del__(self):
        self.wait()

    def run(self):
        result = None
        row = None
        data = None
        for index, i in enumerate(self.array):
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
                            self.logger.debug("Mysterious - {0}".format(word))
                        result = after

                row = {"word": word,
                       "result": result,
                       "tword": translate,
                       "context": context}
                data = {"sent": True,
                        "row": row,
                        "index": index+1}
            except (NoConnection, Timeout):
                data = {"sent": False,
                        "row": None,
                        "index": None}
                self.logger.debug("Couldn't upload words")
            except UnicodeEncodeError:
                row = {"word": word,
                       "result": self.RESULTS['no_tr'],
                       "tword": '',
                       "context": context}
                data = {"sent": True,
                        "row": row,
                        "index": index+1}
                self.logger.debug("{0} is not English".format(word))
            finally:
                self.punched.emit(data)
            time.sleep(0.1)

    def stop(self):
        self.terminate()
        self.logger.debug("Stopped upload")

    def getData(self, array, index=0):
        self.array = array[index:]
        self.logger.debug("Got array of {0} words".format(len(self.array)))


class ExportDialog(CustomDialog, Results):

    ICON_FILE = os.path.join("src", "pics", "export.ico")
    closed = QtCore.pyqtSignal()

    def __init__(self, array, total, duplicates, lingualeo):

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

    def initUI(self):
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
        self.logger.debug("Constructed UI")

    def retranslateUI(self):
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        avatar = QtGui.QPixmap()
        avatar.loadFromData(self.lingualeo.avatar)
        self.avatar_label.setPixmap(avatar)
        self.avatar_label.setAlignment(QtCore.Qt.AlignCenter)
        # self.avatar_label.setScaledContents(True)

        # INFO GRID
        self.fname_title_label.setText(self.tr("Name:"))
        self.fname_value_label.setText(self.lingualeo.fname)

        self.lvl_title_label.setText(self.tr("Lvl:"))
        self.lvl_value_label.setText(str(self.lingualeo.lvl))

        self.meatballs_title_label.setText(self.tr("Meatballs:"))
        self.meatballs_value_label.setText(str(self.lingualeo.meatballs))
        if not self.lingualeo.isEnoughMeatballs(self.words_count):
            self.warning_info_label.setText(
                self.tr("WARNING: Meatballs < words"))
            self.warning_info_label.setStyleSheet("color:red;font-weight:bold")
            self.warning_info_label.show()
        self.total_words_title_label.setText(self.tr("Total words:"))
        self.total_words_value_label.setText(str(self.total))
        self.duplicate_words_title_label.setText(self.tr("Duplicates removed:"))
        self.duplicate_words_value_label.setText(str(self.duplicates))
        self.prepared_words_title_label.setText(self.tr("Prepared to export:"))
        self.prepared_words_value_label.setText(str(self.words_count))
        self.setWindowTitle(self.tr("Preparing to export"))
        self.start_button.setText(self.tr("Start"))
        self.break_button.setText(self.tr("Break"))
        self.logger.debug("Retranslated UI")

    def initActions(self):
        self.start_button.clicked.connect(self.changeTask)
        self.break_button.clicked.connect(self.task.stop)
        self.break_button.clicked.connect(self.close)
        self.task.punched.connect(self.onProgress)
        self.logger.debug("Inited actions")

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.task.stop()
            self.close()

    def closeEvent(self, event):
        event.accept()
        self.task.stop()
        s = StatisticsWindow(self.stat)
        s.exec_()
        self.closed.emit()

    def changeTask(self):
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
            self.break_button.hide()
        self.logger.debug("{0} triggered".format(self.sender().objectName()))

    def finish(self):
        self.progress_bar.setFormat(self.tr("Finished"))
        self.break_button.setText(self.tr("Close"))
        self.start_button.hide()

    def onProgress(self, data):

        if data['sent']:
            row = data['row']
            if row['result'] == self.RESULTS['ad']:
                if not self.lingualeo.isPremium():
                    self.lingualeo.substractMeatballs()
                    self.meatballs_value_label.setText(
                        str(self.lingualeo.meatballs))
        else:
            self.start_button.click()
            warning = NotificationDialog(self.tr("No Internet Connection"))
            warning.exec_()
            self.logger.debug("No connection")
            return

        self.stat.append(data['row'])
        self.value += 1
        self.progress_bar.setValue(self.value)
        self.progress_bar.setFormat(
            "{0} words processed out of {1}".format(self.value,
                                                    self.words_count))
        if self.lingualeo.meatballs == 0:
            self.task.stop()
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.warning_info_label.setText(
                self.tr("No meatballs. Upload stopped"))
            self.finish()
            for i in self.array[self.value:]:
                self.stat.append({"word": i['word'],
                                  "result": self.RESULTS['no_ad'],
                                  "tword": "",
                                  "context": i['context']})
            self.logger.debug("0 meatballs. Upload stopped")
            return

        if self.progress_bar.value() == self.progress_bar.maximum():
            self.logger.debug("{0} words tried to upload".format(self.value))
            self.finish()


class StatisticsWindow(CustomDialog, Results):

    ICON_FILE = os.path.join("src", "pics", "statistics.ico")

    def __init__(self, stat):
        super(StatisticsWindow, self).__init__()
        self.logger = setLogger(name="Statistics")
        self.stat = stat
        self.initUI()
        self.retranslateUI()

    def initUI(self):
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
        self.table.resizeRowsToContents()
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)

        grid = self.createGrid()
        self.layout = QtGui.QVBoxLayout()
        self.layout.addLayout(grid)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)
        self.logger.debug("Created UI")

    def createGrid(self):

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
            color_label.setStyleSheet("background-color:{0}".format(i['color']))
            text_label = QtGui.QLabel()
            text_label.setText("{0}: {1}".format(i['text'], i['value']))

            grid.addWidget(color_label, index, 0)
            grid.addWidget(text_label, index, 1)

        self.logger.debug("Statistics GRID created")
        return grid

    def resizeEvent(self, event):
        self.table.resizeRowsToContents()
        event.accept()

    def retranslateUI(self):
        self.setWindowIcon(QtGui.QIcon(self.ICON_FILE))
        self.setWindowTitle(self.tr("Statistics"))
        self.logger.debug("Retranslated UI")


def main():
    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)
    sys.excepthook = exception_hook
    logger = setLogger(name='main')
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    logger.debug("New session started")
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception:
        logger.exception("MainWindow exception")

if __name__ == "__main__":
    main()
