import sys
from PyQt4 import QtCore, QtGui
from word import Kindle, Text, Input
from config import sources, auth
from service import Lingualeo
import sqlite3
import time
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
        
    def initUI(self):
        self.main_widget = QtGui.QWidget(self)
        self.main_layout = QtGui.QVBoxLayout()
        self.auth_layout = QtGui.QGridLayout()
        self.auth_label = QtGui.QLabel()
        self.email_label = QtGui.QLabel()
        self.email_edit = QtGui.QLineEdit()
        self.pass_label = QtGui.QLabel()
        self.pass_edit = QtGui.QLineEdit()
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
        
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
    
    def setSizeUI(self):
        self.input_word_edit.setFixedHeight(self.input_word_edit.sizeHint().height())
        
    def retranslateUI(self):
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
        self.truncate_push.setEnabled(kindle)
        
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
        lingualeo.auth()
        
        if kindle:
            handler = Kindle(self.file_name)
            handler.read()
            self.table = handler.get()
        elif text:
            handler = Text(sources.get('text'))
            handler.read()
            self.table = handler.get()
        else:
            word = self.input_word_edit
            context = self.input_context_edit
            self.table = [{'word':word, 'context': context}]
        
        words = len(self.table)
        p = ExportDialog(self.table, lingualeo)
        p.exec_()
    
    def truncate(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("DELETE FROM WORDS;")
            conn.execute("DELETE FROM LOOKUPS;")
            conn.execute("UPDATE METADATA SET sscnt = 0 WHERE id in ('WORDS', 'LOOKUPS');")
            conn.commit()

    def setKindlePath(self):
        self.file_name = QtGui.QFileDialog.getOpenFileName(self, "Select File", "",)
        self.kindle_path.setText(self.file_name)
        
    def initActions(self):
        self.input_radio.clicked.connect(self.getSource)
        self.text_radio.clicked.connect(self.getSource)
        self.kindle_radio.clicked.connect(self.getSource)
        self.export_push.clicked.connect(self.export)
        self.kindle_push.clicked.connect(self.setKindlePath)
        
class WorkThread(QtCore.QThread):
    
    punched = QtCore.pyqtSignal(int)
    
    def __init__(self, words):
        super(QtCore.QThread, self).__init__()
        self.words = words
        
    def __del__(self):
        self.wait()
    
    def run(self):
        for i in range(self.words):
            self.punched.emit(i)
            time.sleep(0.1)
            
class ExportDialog(QtGui.QDialog):
    
    def __init__(self, table, lingualeo):
        super(ExportDialog, self).__init__()
        self.table = table
        self.words = len(self.table)
        self.lingualeo = lingualeo
        self.initUI()
        self.startTask()
        
    def initUI(self):
        layout = QtGui.QVBoxLayout()
        self.label = QtGui.QLabel()
        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setRange(0, self.words)
        
        layout.addWidget(self.label)
        layout.addWidget(self.progressBar)
        self.setLayout(layout)
    
    def closeEvent(self, event):
        event.accept()
        self.task.terminate()
        
    def startTask(self):
        self.task = WorkThread(self.words+1)
        self.task.punched.connect(self.onProgress)
        self.task.start()
        
    def onProgress(self, i):
        try:
            row = self.table[i]
            word = row.get('word').lower()
            context = row.get('context', '')
            translate = self.lingualeo.get_translates(word)
            self.lingualeo.add_word(translate['word'], translate['tword'], context)
            if not translate['is_exist']:
                result = "Added word: "
            else:
                result = "Already exists: "
                
            result = result + word
            print(result)
        except:
            print("wrong")
        self.label.setText("{} words processes out of {}".format(i, self.words))
        self.progressBar.setValue(i)
        if self.progressBar.value() == self.progressBar.maximum():
            self.close()
            
'''     
QtGui.QProgressDialog("Copying", "Cancel", 0, 9)
class ExportDialog(QtGui.QProgressDialog):
    
    def __init__(self, title, cancel, low, high):
        super(QtGui.QProgressDialog, self).__init__(title, cancel, low, high)
'''         
class AreYouSure(QtGui.QWidget):
    
    def __init__(self):
        super(QtGui.QWidget, self)
        
class StatisticsWindow(QtGui.QWidget):
    
    def __init__(self):
        super(QtGui.QWidget, self)
        
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