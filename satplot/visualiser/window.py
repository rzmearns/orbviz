import logging
import sys
from typing import Any

from PyQt5 import QtWidgets, QtCore

import satplot
from satplot.model.data_models import (history_data)
from satplot.visualiser.contexts import (history3d_context, history2d_context, blank_context)
import satplot.visualiser.interface.console as console

logger = logging.getLogger(__name__)

class MainWindow(QtWidgets.QMainWindow):
	closing = QtCore.pyqtSignal()

	def __init__(self,	title:str="",
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
		self.contexts_dict = {}
		self.context_tabs = QtWidgets.QTabWidget()
		
		# Build data models
		history_data_model = history_data.HistoryData()

		# Build context panes
		self.contexts_dict['3d-history'] = history3d_context.History3DContext('3d-history', self, history_data_model)
		self.toolbars['3d-history'] = self.contexts_dict['3d-history'].controls.toolbar
		self.menubars['3d-history'] = self.contexts_dict['3d-history'].controls.menubar
		self.context_tabs.addTab(self.contexts_dict['3d-history'].widget, '3D History')

		self.contexts_dict['2d-history'] = history2d_context.History2DContext('2d-history', self, history_data_model)
		self.toolbars['2d-history'] = self.contexts_dict['2d-history'].controls.toolbar
		self.menubars['2d-history'] = self.contexts_dict['2d-history'].controls.menubar
		self.context_tabs.addTab(self.contexts_dict['2d-history'].widget, '2D History')

		self.contexts_dict['blank'] = blank_context.BlankContext('blank', self)
		self.toolbars['blank'] = self.contexts_dict['blank'].controls.toolbar
		self.menubars['blank'] = self.contexts_dict['blank'].controls.menubar
		self.context_tabs.addTab(self.contexts_dict['blank'].widget, 'Blank')



		# self.toolbars['blank'] = self.contexts_dict['blank'].controls.toolbar
		# self.menubars['blank'] = self.contexts_dict['blank'].controls.menubar
		# self.context_tabs.addTab(QtWidgets.QWidget(), 'Blank')

		# check toolbar/menubar indices are the same
		for ii, key in enumerate(self.toolbars.keys()):
			if list(self.menubars.keys())[ii] != key:
				logger.error(f'Context toolbars and menubar indices do not match for contexts')
				logger.error(f'Toolbars: {self.toolbars.keys()}')
				logger.error(f'Menubars: {self.menubars.keys()}')
				raise ValueError('Toolbars and Menubars indices do not match')
				sys.exit()

		self.context_tabs.currentChanged.connect(self._changeToolbarsToContext)

		

		# Prep console area
		self._console = console.Console()
		console.consolefp = console.EmittingConsoleStream(textWritten=self._console.writeOutput)
		if not satplot.debug:
			sys.stderr = console.EmittingConsoleStream(textWritten=self._console.writeErr)
		console.consoleErrfp = console.EmittingConsoleStream(textWritten=self._console.writeErr)

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
		self.context_tabs.setCurrentIndex(1)
		self._changeToolbarsToContext(1)

	def _changeToolbarsToContext(self, new_context_index:int) -> None:
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

	def printCol(self,val:Any) -> None:
		print(val)

	def serialiseContexts(self) -> dict[str,Any]:
		state = {}
		for context_key, context in self.contexts_dict.items():
			state[context_key] = context.prepSerialisation()

		return state

	def deserialiseContexts(self, state:dict[str,Any]) -> None:
		for context_key, context_dict in state.items():
			self.contexts_dict[context_key].deSerialise(context_dict)

	def __del__(self) -> None:
		sys.stderr = sys.__stderr__

	def closeEvent(self, event:QtCore.QEvent) -> None:
		sys.stderr = sys.__stderr__

		if satplot.threadpool is not None:
			# Clear any waiting jobs
			satplot.threadpool.clear()
			# Stop active jobs
			satplot.threadpool.killAll()
		logger.info('Closing satplot window')
		return super().closeEvent(event)
	
