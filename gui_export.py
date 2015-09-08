import sys
import os
from PyQt4 import QtCore, QtGui
from word import Kindle, Text, Input
from config import sources, auth
from service import Lingualeo
import sqlite3
import time

#CONSTANTS
DEFAULT_NAME = "src/src.ini"
TESTS_NAME = "tests/"

class MainWindow(QtGui.QMainWindow):
    
    def __init__(self, source='input'):
        super(MainWindow, self).__init__()
        self.source = source
        self.file_name = None
        self.initUI()
        self.setSizeUI()
        self.retranslateUI()
        self.centerUI()
        self.checkState()
        self.initActions()
        self.loadDefaults()
        
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
        self.text_push = QtGui.QPushButton()
        self.text_path = QtGui.QLineEdit()
        self.text_path.setReadOnly(True)
        self.text_layout = QtGui.QHBoxLayout()
        self.text_layout.addWidget(self.text_push)
        self.text_layout.addWidget(self.text_path)
        
        self.kindle_radio = QtGui.QRadioButton()
        self.kindle_push = QtGui.QPushButton()
        self.kindle_path = QtGui.QLineEdit()
        self.kindle_path.setReadOnly(True)
        self.kindle_layout = QtGui.QHBoxLayout()
        self.kindle_layout.addWidget(self.kindle_push)
        self.kindle_layout.addWidget(self.kindle_path)
        
        self.export_push = QtGui.QPushButton()
        self.truncate_push = QtGui.QPushButton()
        self.bottom_layout = QtGui.QHBoxLayout()
        self.bottom_layout.addWidget(self.export_push)
        self.bottom_layout.addWidget(self.truncate_push)
        
        self.main_layout.addLayout(self.auth_layout)
        self.main_layout.addWidget(self.main_label)
        self.main_layout.addWidget(self.input_radio)
        self.main_layout.addLayout(self.input_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.text_radio)
        self.main_layout.addLayout(self.text_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.kindle_radio)
        self.main_layout.addLayout(self.kindle_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(self.bottom_layout)
        self.status_bar = QtGui.QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
    
    def setSizeUI(self):
        self.input_word_edit.setFixedHeight(self.input_word_edit.sizeHint().height())
        
    def retranslateUI(self):
        self.setWindowTitle(self.tr("Export to Lingualeo"))
        self.email_label.setText("e-mail")
        self.pass_label.setText('password')
        self.main_label.setText(self.tr("<center>Choose the source</center>"))
        self.input_radio.setText(self.tr("Input"))
        self.input_word_label.setText(self.tr("word"))
        self.input_context_label.setText(self.tr("context"))
        
        self.text_radio.setText(self.tr("Text"))
        self.text_push.setText(self.tr("Path"))
        
        self.kindle_radio.setText(self.tr("Kindle"))
        self.kindle_push.setText(self.tr("Path"))
        
        self.export_push.setText(self.tr("Export"))
        self.truncate_push.setText(self.tr("Truncate"))
    
    def centerUI(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
       
    def checkState(self):
        input = self.input_radio.isChecked()
        text = self.text_radio.isChecked()
        kindle = self.kindle_radio.isChecked()
        
        self.input_word_edit.setEnabled(input)
        self.input_context_edit.setEnabled(input)
        self.input_word_label.setEnabled(input)
        self.input_context_label.setEnabled(input)
        self.text_push.setEnabled(text)
        self.text_path.setEnabled(text)
        self.kindle_push.setEnabled(kindle)
        self.kindle_path.setEnabled(kindle)
        
    def kindleEmpty(self):
        db = sqlite3.connect(self.file_name)
        cursor = db.cursor()
        data = cursor.execute("SELECT * FROM WORDS").fetchall()
        return len(data) == 0
    
    def kindleWrongDatabase(self):
        basename, ext = os.path.splitext(self.file_name)
        print(ext)
        if ext != ".db":
            return True
        conn = sqlite3.connect(self.file_name)
        try:
            conn.execute("SELECT * FROM WORDS")
        except:
            return True
                
    def getSource(self):
        source = self.sender().text().lower()
        print(self.sender().text().lower())
        self.source = source
        self.checkState()
    
    def export(self):   #Kindle/Input/Word
        kindle = self.kindle_radio.isChecked()
        text = self.text_radio.isChecked()
        email = self.email_edit.text().strip(" ")
        password = self.pass_edit.text().strip(" ")
        lingualeo = Lingualeo(email, password)
        response = lingualeo.auth()
        print(response)
        if response.get('error_code'):
            self.status_bar.showMessage(self.tr(response.get('error_msg')))
            return
        
        if kindle:
            if not self.kindle_path.text():
                self.status_bar.showMessage(self.tr("No file"))
                return
            if self.kindleWrongDatabase():
                self.status_bar.showMessage(self.tr("Not valid database"))
                return
            if self.kindleEmpty():
                self.status_bar.showMessage(self.tr("Base is empty"))
                return
            
            
            handler = Kindle(self.file_name)
            handler.read()
            self.table = handler.get()
            
        elif text:
            handler = Text(sources.get('text'))
            handler.read()
            self.table = handler.get()
        else:
            word = self.input_word_edit.text()
            context = self.input_context_edit.text()
            if not word:
                self.status_bar.showMessage(self.tr("No word"))
                return
            self.table = [{'word':word, 'context': context}]
        
        p = ExportDialog(self.table, lingualeo)
        p.exec_()
    
    def truncate(self):
        '''truncate Kindle database'''
        if self.kindleEmpty():
            self.status_bar.showMessage(self.tr("File is empty"))
            return
        reply = QtGui.QMessageBox.question(self, 'Message', 'Are you sure to truncate?', 
                                           QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, 
                                           QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            conn = sqlite3.connect(self.file_name)
            with conn:
                conn.execute("DELETE FROM WORDS;")
                conn.execute("DELETE FROM LOOKUPS;")
                conn.execute("UPDATE METADATA SET sscnt = 0 WHERE id in ('WORDS', 'LOOKUPS');")
                conn.commit()
            self.status_bar.showMessage("Kindle database is empty")
        else:
            return
    
    def setKindlePath(self):
        self.file_name = QtGui.QFileDialog.getOpenFileName(self, "Select File", "",)
        self.kindle_path.setText(self.file_name)
    
    def changeEditWidth(self):
        if 'email' in self.sender().objectName():
            width_e = self.email_edit.fontMetrics().boundingRect(self.email_edit.text()).width() + 10
            self.email_edit.setMinimumWidth(width_e)
        else:
            width_p = self.pass_edit.fontMetrics().boundingRect(self.pass_edit.text()).width() + 10
            self.pass_edit.setMinimumWidth(width_p)
        
    def initActions(self):
        self.input_radio.clicked.connect(self.getSource)
        self.text_radio.clicked.connect(self.getSource)
        self.kindle_radio.clicked.connect(self.getSource)
        self.export_push.clicked.connect(self.export)
        self.truncate_push.clicked.connect(self.truncate)
        self.kindle_push.clicked.connect(self.setKindlePath)
        self.email_edit.textChanged.connect(self.changeEditWidth)
        self.pass_edit.textChanged.connect(self.changeEditWidth)
        
    def closeEvent(self, event):
        self.saveDefaults()
        
    def saveDefaults(self):
        '''save default email and password'''
        self.settings = QtCore.QSettings("src.ini", QtCore.QSettings.IniFormat)
        self.settings.setValue("email", self.email_edit.text())
        self.settings.setValue("password", self.pass_edit.text())
        
    def loadDefaults(self):
        '''load default email and password'''
        try:
            self.settings = QtCore.QSettings("src.ini", QtCore.QSettings.IniFormat)
            email = self.settings.value("email")
            password = self.settings.value("password")
            self.email_edit.setText(email)
            self.pass_edit.setText(password)
        except:
            pass
        
class WorkThread(QtCore.QThread):
    
    punched = QtCore.pyqtSignal(dict)
    
    def __init__(self, table):
        super(QtCore.QThread, self).__init__()
        self.table = table
        
    def __del__(self):
        self.wait()
    
    def run(self):
        for i in self.table:
            self.punched.emit(i)
            time.sleep(0.5)
            
class ExportDialog(QtGui.QDialog):
    
    def __init__(self, table, lingualeo):
        super(ExportDialog, self).__init__()
        self.table = table
        self.stat = list()
        self.task = WorkThread(self.table)
        self.length = len(self.table)
        self.lingualeo = lingualeo
        self.initUI()
        self.retranslateUI()
        self.initActions()
        self.startTask()
        
        
    def initUI(self):
        layout = QtGui.QVBoxLayout()
        self.label = QtGui.QLabel()
        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setRange(0, self.length)
        self.button = QtGui.QPushButton()
        layout.addWidget(self.label)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.button)
        self.setLayout(layout)
    
    def retranslateUI(self):
        self.setWindowTitle(self.tr("Processing..."))
        self.button.setText(self.tr("Break"))
    
    def initActions(self):
        self.button.clicked.connect(self.task.terminate)
        self.button.clicked.connect(self.close)
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.task.terminate()
            self.close()
            
    def closeEvent(self, event):
        event.accept()
        self.task.terminate()
        s = StatisticsWindow(self.stat)
        s.exec_()
        
    def startTask(self):
        
        self.task.punched.connect(self.onProgress)
        self.task.start()
        
    def onProgress(self, i):
        try:
            row = i
            word = row.get('word').lower()
            context = row.get('context', '')
            translate = self.lingualeo.get_translates(word)
            self.lingualeo.add_word(translate['word'], translate['tword'], context)
            if not translate['is_exist']:
                result = "Added word: "
            else:
                result = "Already exists: "
                
            result = result + word
            self.stat.append({"word":word, "result":result})
        except:
            print("wrong")
        value = self.table.index(i)+1
        self.label.setText("{} words processed out of {}".format(value, self.length))
        self.progressBar.setValue(value)
        if self.progressBar.value() == self.progressBar.maximum():
            self.label.setText("Done")
                   
class AreYouSure(QtGui.QWidget):
    
    def __init__(self, email, pas):
        super(QtGui.QWidget, self)
        
        
class StatisticsWindow(QtGui.QDialog):
    
    def __init__(self, stat):
        super(QtGui.QDialog, self).__init__()
        self.stat = stat
        self.initUI()
        self.retranslateUI()
    
    def initUI(self):
        
        self.list_view= QtGui.QListWidget()
        for index, item in enumerate(self.stat):
            row = QtGui.QListWidgetItem()
            if "exist" in item.get("result"):
                brush = QtGui.QBrush(QtCore.Qt.red)
            else:
                brush = QtGui.QBrush(QtCore.Qt.green)
            row.setBackground(brush)
            row.setText(item.get("word"))
            self.list_view.addItem(row)
        a = len(self.stat)
        d = ["Add" in i.get("result") for i in self.stat].count(True)
        self.label = QtGui.QLabel("<center>{} added out of {}</center>".format(d, a))
        self.layout = QtGui.QVBoxLayout()
        self.tab = QtGui.QScrollArea()
        self.tab.setWidget(self.list_view)
        self.layout.addWidget(self.tab)
        self.setLayout(self.layout)
        
    def retranslateUI(self):
        self.setWindowTitle(self.tr("Statistics"))
        
def main():
    app = QtGui.QApplication(sys.argv)
    #app.setQuitOnLastWindowClosed(False)
    m = MainWindow()
    m.show()
    sys.exit(app.exec_())

def test():
    
        
    app = QtGui.QApplication(sys.argv)
 
    progress = QtGui.QProgressDialog("Copying...", "Cancel", 0, 9)
    progress.show()
    t = WorkThread()
    
    t.punched.connect(lambda: progress.setValue(progress.value()+1))
    t.punched.connect(lambda: progress.setLabelText("Exporting {} out of {}".format(progress.value()+1, 11)))
 
    t.start()
 
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    #test()