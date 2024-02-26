from PyQt5 import QtWidgets, QtCore, QtGui
import html

consolefp = None

def send(str):
	print(str, file=consolefp)
	# consolefp.flush()

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
		cursor = self.text_box.textCursor()
		self.text_box.setTextColor(self.stdCol)
		self.text_box.insertPlainText(text)
		cursor.movePosition(QtGui.QTextCursor.End)
		self.text_box.setTextCursor(cursor)

	def writeErr(self, text):
		cursor = self.text_box.textCursor()
		self.text_box.setTextColor(self.errCol)
		self.text_box.insertPlainText(text)
		# TODO: add cursor to end
		cursor.movePosition(QtGui.QTextCursor.End)
		self.text_box.setTextCursor(cursor)