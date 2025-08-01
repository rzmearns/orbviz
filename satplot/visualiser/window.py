import logging
import sys
from typing import Any

from PyQt5 import QtWidgets, QtCore

import satplot
from satplot.visualiser.shells import (historical_shell,
										planning_shell)
from satplot.model.data_models import (earth_raycast_data)
import satplot.visualiser.interface.widgets as satplot_widgets
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.controls as controls

logger = logging.getLogger(__name__)

class MainWindow(QtWidgets.QMainWindow):
	closing = QtCore.pyqtSignal()

	def __init__(self,	title:str="",
						*args, **kwargs):
		super().__init__(*args, **kwargs)
		main_widget = QtWidgets.QWidget()
		main_layout = QtWidgets.QVBoxLayout()
		console_vsplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
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

		self.shell_dict: dict[str, Any] = {}
		self.active_shell_idx = None
		self.shell_tab_stack = satplot_widgets.StretchTabWidget()
		self.shell_tab_stack.tabBar().setDrawBase(False)

		self.toolbars: dict[str, controls.Toolbar] = {}
		self.menubars: dict[str, controls.Menubar] = {}

		global_earth_raycast_data = earth_raycast_data.EarthRayCastData()

		# Build shells
		self.shell_dict['history'] = historical_shell.HistoricalShell(self, self.toolbars, self.menubars, global_earth_rdm=global_earth_raycast_data)
		self.shell_tab_stack.addTab(self.shell_dict['history'].widget,'Historical')
		self.shell_dict['planning'] = planning_shell.PlanningShell(self, self.toolbars, self.menubars, global_earth_rdm=global_earth_raycast_data)
		self.shell_tab_stack.addTab(self.shell_dict['planning'].widget,'Planning')


		# Prep console
		self._console = console.Console()
		console.consolefp = console.EmittingConsoleStream(textWritten=self._console.writeOutput)
		if not satplot.debug:
			sys.stderr = console.EmittingConsoleStream(textWritten=self._console.writeErr)
		console.consoleErrfp = console.EmittingConsoleStream(textWritten=self._console.writeErr)

		# Build main layout
		'''
		#######
		#######
		#######
		#######
		-------
		#######
		'''
		console_vsplitter.addWidget(self.shell_tab_stack)
		console_vsplitter.addWidget(self._console)

		main_layout.addWidget(console_vsplitter)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_widget.setLayout(main_layout)
		self.setCentralWidget(main_widget)

		self.setWindowTitle(title)
		self.shell_tab_stack.currentChanged.connect(self._changeToolbarsToShell)
		self.shell_tab_stack.setCurrentIndex(0)
		self._changeToolbarsToShell(0)

	def _changeToolbarsToShell(self, new_shell_idx:int) -> None:
		new_shell = list(self.shell_dict.values())[new_shell_idx]
		logger.debug('Changing Shells to %s', new_shell.name)
		for shell in self.shell_dict.values():
			if shell != new_shell:
				shell.makeDormant()
				shell.updateActiveContext(None, None)
		new_shell.makeActive()
		new_shell.updateActiveContext(None, None)

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
	
