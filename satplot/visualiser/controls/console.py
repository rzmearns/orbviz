from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import string


consolefp = None
printable = string.ascii_letters + string.digits + string.punctuation + ' '


def send(str):
	print(str, file=consolefp)

def hex_escape(s):
    return ''.join(c if c in printable else r'\x{0:02x}'.format(ord(c)) for c in s)

class EmittingConsoleStream(QtCore.QObject):
	textWritten = QtCore.pyqtSignal(str)

	# called on print in send function above
	def write(self, text):
		# if "\n" in text:
		# 	print(f"newline is in text: {text}")
		# else:
		# 	print(f"newline is not in text: {text}")
		self.textWritten.emit(str(text))

class Console(QtWidgets.QWidget):

	def __init__(self, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)

		self.errCol = QtGui.QColor(255,0,0)
		self.stdCol = QtGui.QColor(51,255,0)
		self.overwriting = False
		layout = QtWidgets.QVBoxLayout()
		self.text_box = QtWidgets.QTextEdit()
		layout.addWidget(self.text_box)
		self.setLayout(layout)
		self.text_box.setObjectName('console')
		self.text_box.setStyleSheet('''
			QTextEdit#console {
			  	background-color: #000000}
							  ''')
		self.text_box.setReadOnly(False)

	def writeOutput(self, text):
		if text.isspace():
			return
		
		cursor = self.text_box.textCursor()
		self.text_box.setTextColor(self.stdCol)
		

		# hack to get colour to work for individual lines
		self.text_box.insertPlainText(' ')

		self.text_box.setTextCursor(cursor)
		
		if self.overwriting:
			cursor.movePosition(QtGui.QTextCursor.StartOfLine, cursor.KeepAnchor)
			cursor.movePosition(QtGui.QTextCursor.Up, cursor.KeepAnchor)
			cursor.insertText(' ')

		cursor.insertText(text+'\n')
		cursor.movePosition(QtGui.QTextCursor.End)
		if '\r\n' not in text and '\r' in text:
			self.setOverwriteMode(True)
		else:
			self.setOverwriteMode(False)

	def setOverwriteMode(self, state):
		self.overwriting = state
		self.text_box.setOverwriteMode(state)

	def writeErr(self, text):
		cursor = self.text_box.textCursor()
		self.text_box.setTextColor(self.errCol)
		# hack to get colour to work for individual lines
		self.text_box.insertPlainText(' ')
		
		if self.overwriting:
			self.setOverwriteMode(True)	
		cursor.insertText(text)

		cursor.movePosition(QtGui.QTextCursor.End)
		self.setOverwriteMode(False)
		self.text_box.setTextCursor(cursor)