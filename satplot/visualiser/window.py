import sys
from PyQt5 import QtWidgets, QtCore
import satplot
from satplot.visualiser.controls import controls, widgets
from satplot.visualiser import canvaswrappers
from satplot.visualiser.contexts import (history3d)
import satplot.visualiser.controls.console as console

class MainWindow(QtWidgets.QMainWindow):
	closing = QtCore.pyqtSignal()

	def __init__(self,	title="",
			  			action_dict=None,
						*args, **kwargs):
		super().__init__(*args, **kwargs)
		print(f"{action_dict=}")
		main_widget = QtWidgets.QWidget()
		main_layout = QtWidgets.QVBoxLayout()
		self.toolbars = {}
		self.menubars = {}
		self.context_dict = {}
		self.context_tabs = QtWidgets.QTabWidget()
		

		self.toolbars['3d-history'] = controls.Toolbar(self, action_dict, context='3d-history')
		self.menubars['3d-history'] = controls.Menubar(self, action_dict, context='3d-history')
		self.context_dict['3d-history'] = history3d.History3DContext('3d-history')
		self.context_tabs.addTab(self.context_dict['3d-history'].widget, '3D History')

		self.toolbars['blank'] = controls.Toolbar(self, action_dict, context='blank')
		self.menubars['blank'] = controls.Menubar(self, action_dict, context='blank')
		self.context_tabs.addTab(QtWidgets.QWidget(), 'Blank')

		# check toolbar/menubar indices are the same
		for ii, key in enumerate(self.toolbars.keys()):
			if list(self.menubars.keys())[ii] != key:
				raise ValueError('Toolbars and Menubars indices do not match')
				# Should probably exit here

		self.context_tabs.currentChanged.connect(self._changeToolbarsToContext)

		self.setWindowTitle(title)

		main_layout.addWidget(self.context_tabs)
		main_widget.setLayout(main_layout)
		self.setCentralWidget(main_widget)

		self._changeToolbarsToContext(0)

	def _changeToolbarsToContext(self, new_context_index):
		new_context_key = list(self.toolbars.keys())[new_context_index]
		console.send(f'Changing context to {new_context_key}')
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
	
