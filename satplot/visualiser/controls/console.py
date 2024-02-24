from PyQt5 import QtWidgets, QtCore, QtGui
import html

consolefp = None

def send(str):
	print(str, file=consolefp)

class EmittingConsoleStream(QtCore.QObject):
	textWritten = QtCore.pyqtSignal(str)

	def write(self, text):
		self.textWritten.emit(str(text))

class Console(QtWidgets.QWidget):

	def __init__(self, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)

		self.errCol = QtGui.QColor(255,0,0)
		self.stdCol = QtGui.QColor(51,255,0)

		layout = QtWidgets.QVBoxLayout()
		self.text_box = QtWidgets.QTextEdit()
		layout.addWidget(self.text_box)
		self.setLayout(layout)
		self.text_box.setObjectName('console')
		self.text_box.setStyleSheet('''
			QTextEdit#console {
			  	background-color: #000000}
							  ''')
		self.text_box.setReadOnly(True)

	def writeOutput(self, text):
		self.text_box.setTextColor(self.stdCol)
		self.text_box.insertPlainText(text)

	def writeErr(self, text):
		self.text_box.setTextColor(self.errCol)
		self.text_box.insertPlainText(text)