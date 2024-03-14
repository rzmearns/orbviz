import satplot
import satplot.model.timespan as timespan
import satplot.model.orbit as orbit
from satplot.visualiser import canvaswrappers
from satplot.visualiser.contexts.base import (BaseContext, BaseDataWorker, BaseControls)
import satplot.visualiser.controls.console as console
from satplot.visualiser.controls import controls, widgets

import sys
import numpy as np
import datetime as dt

from PyQt5 import QtWidgets, QtCore

class BlankContext(BaseContext):
	def __init__(self, name, parent_window):
		super().__init__(name)
		self.window = parent_window

		self.canvas_wrapper = None
		self.controls = self.Controls(self, self.canvas_wrapper)

		disp_hsplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		disp_hsplitter.setObjectName('disp_hsplitter')
		disp_hsplitter.setStyleSheet('''
					QSplitter#disp_hsplitter::handle {
								background-color: #DCDCDC;
							}
							''')
		content_widget = QtWidgets.QWidget()
		content_vlayout = QtWidgets.QVBoxLayout()

	def connectControls(self):
		pass

	def _loadData(self):
		pass

	def loadState(self):
		pass

	def saveState(self):
		pass

	def _cleanUpLoadWorkerThread(self):
		return super()._cleanUpLoadWorkerThread()

	class LoadDataWorker(BaseDataWorker):
		finished = QtCore.pyqtSignal()
		error = QtCore.pyqtSignal()

		def __init__(self, *args, **kwargs):
			super().__init__(*args, **kwargs)

		def run(self):
			self.finished.emit()
		
	class Controls(BaseControls):
		def __init__(self, parent_context, canvas_wrapper):
			self.context = parent_context
			super().__init__(self.context.data['name'])

			# Prep config widgets
			
			# Wrap config widgets in tabs

			# Prep time slider

			# Prep toolbars
			self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.data['name'])
			self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.data['name'])