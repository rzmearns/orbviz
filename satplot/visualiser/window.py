import sys
from PyQt5 import QtWidgets, QtCore
import satplot
from satplot.visualiser.controls import controls, widgets
from satplot.visualiser import canvaswrappers
from satplot.visualiser.contexts import (history3d, blank)
import satplot.visualiser.controls.console as console

class MainWindow(QtWidgets.QMainWindow):
	closing = QtCore.pyqtSignal()

	def __init__(self,	title="",
						*args, **kwargs):
		super().__init__(*args, **kwargs)
		main_widget = QtWidgets.QWidget()
		main_layout = QtWidgets.QVBoxLayout()
		console_vsplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
		console_vsplitter.setObjectName('window_vsplitter')
		console_vsplitter.setStyleSheet('''
					QSplitter#window_vsplitter::handle {
								background-color: #DCDCDC;
								padding: 2px;
							}
					QSplitter#window_vsplitter::handle:vertical {
								height: 1px;
								color: #ff0000;
							}								  
							''')

		self.toolbars = {}
		self.menubars = {}
		self.context_dict = {}
		self.context_tabs = QtWidgets.QTabWidget()
		

		# Build context panes
		self.context_dict['3d-history'] = history3d.History3DContext('3d-history', self)
		self.toolbars['3d-history'] = self.context_dict['3d-history'].controls.toolbar
		self.menubars['3d-history'] = self.context_dict['3d-history'].controls.menubar
		self.context_tabs.addTab(self.context_dict['3d-history'].widget, '3D History')

		self.context_dict['blank'] = blank.BlankContext('blank', self)
		self.toolbars['blank'] = self.context_dict['blank'].controls.toolbar
		self.menubars['blank'] = self.context_dict['blank'].controls.menubar
		self.context_tabs.addTab(self.context_dict['blank'].widget, 'Blank')

		# self.toolbars['blank'] = self.context_dict['blank'].controls.toolbar
		# self.menubars['blank'] = self.context_dict['blank'].controls.menubar
		# self.context_tabs.addTab(QtWidgets.QWidget(), 'Blank')

		# check toolbar/menubar indices are the same
		for ii, key in enumerate(self.toolbars.keys()):
			if list(self.menubars.keys())[ii] != key:
				raise ValueError('Toolbars and Menubars indices do not match')
				# Should probably exit here

		self.context_tabs.currentChanged.connect(self._changeToolbarsToContext)

		

		# Prep console area
		self._console = console.Console()
		console.consolefp = console.EmittingConsoleStream(textWritten=self._console.writeOutput)
		if not satplot.debug:
			sys.stderr = console.EmittingConsoleStream(textWritten=self._console.writeErr)

		# Build main layout
		'''
		# | ###
		- | ###
		# | ###
		#######
		-------
		#######
		'''
		console_vsplitter.addWidget(self.context_tabs)
		console_vsplitter.addWidget(self._console)

		main_layout.addWidget(console_vsplitter)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_widget.setLayout(main_layout)
		self.setCentralWidget(main_widget)


		self.setWindowTitle(title)
		self._changeToolbarsToContext(0)

	def _changeToolbarsToContext(self, new_context_index):
		new_context_key = list(self.toolbars.keys())[new_context_index]
		# process deselects first in order to clear parent pointer to menubar, otherwise menubar gets deleted (workaround for pyqt5)
		for context_key in self.toolbars.keys():
			if context_key != new_context_key:
				self.toolbars[context_key].setActiveState(False)
				self.menubars[context_key].setActiveState(False)
		
		for context_key in self.toolbars.keys():
			if context_key == new_context_key:
				self.toolbars[context_key].setActiveState(True)
				self.menubars[context_key].setActiveState(True)

	# def changeToMainContext(self):		
	# 	self._changeToolbarsToContext(1)

	# def changeTo3DHistoryContext(self):
	# 	self._changeToolbarsToContext(0)

	def printCol(self,val):
		print(val)

	def __del__(self):
		sys.stderr = sys.__stderr__

	def closeEvent(self, event):
		sys.stderr = sys.__stderr__
		self.closing.emit()
		return super().closeEvent(event)
	
