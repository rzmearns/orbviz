import logging
import sys
from typing import Any

from PyQt5 import QtWidgets, QtCore, QtGui

import satplot
from satplot.model.data_models import (history_data,
										earth_raycast_data)
from satplot.visualiser.contexts import (base_context,
											blank_context,
											history2d_context,
											history3d_context,
											sensor_views_context)
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.controls as controls
import satplot.visualiser.interface.widgets as satplot_widgets

logger = logging.getLogger(__name__)

class HistoricalShell():
	def __init__(self, parent_window:QtWidgets.QMainWindow, toolbars:dict[str, controls.Toolbar], menubars:dict[str, controls.Menubar]):
		self.name = 'HISTORICAL'
		self.window = parent_window
		self.widget = QtWidgets.QWidget()
		self.layout = QtWidgets.QVBoxLayout()
		self.toolbars = toolbars
		self.menubars = menubars
		self.active = False

		self.data: dict[str, Any] = {}
		self.contexts_dict: dict[str, base_context.BaseContext] = {}
		self.context_tab_stack = satplot_widgets.ColumnarStackedTabWidget()
		self.context_tab_stack.setTabPosition(QtWidgets.QTabWidget.West)

		# Create empty data models
		history_data_model = history_data.HistoryData()
		earth_raycast_data_model = earth_raycast_data.EarthRayCastData()

		# Build context panes
		self.contexts_dict['3D-history'] = history3d_context.History3DContext('3D-history', self.window, history_data_model)
		self.contexts_dict['2D-history'] = history2d_context.History2DContext('2D-history', self.window, history_data_model, earth_raycast_data_model)
		self.contexts_dict['sensors-view-history'] = sensor_views_context.SensorViewsContext('sensors-view-history', self.window, history_data_model, earth_raycast_data_model)

		# attach relevant toolbars, menubars, add context tabs
		for context_key in self.contexts_dict.keys():
			self.toolbars[context_key] = self.contexts_dict[context_key].controls.toolbar
			self.menubars[context_key] = self.contexts_dict[context_key].controls.menubar
			tab_label = ' '.join(context_key.split('-')[:-1]).title()
			self.context_tab_stack.addTab(self.contexts_dict[context_key].widget, tab_label)


		# check toolbar/menubar indices are the same
		for ii, key in enumerate(self.toolbars.keys()):
			if list(self.menubars.keys())[ii] != key:
				logger.error(f'Context toolbars and menubar indices do not match for contexts')
				logger.error(f'Toolbars: {self.toolbars.keys()}')
				logger.error(f'Menubars: {self.menubars.keys()}')
				raise ValueError('Toolbars and Menubars indices do not match')
				sys.exit()

		self.context_tab_stack.currentChanged.connect(self._changeToolbarsToContext)

		self.layout.addWidget(self.context_tab_stack)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.widget.setLayout(self.layout)

		self._changeToolbarsToContext(1)

	def updateToolbar(self):
		logger.debug(f'Updating toolbar and menu for {self.name} shell')
		curr_context_idx = self.context_tab_stack.currentIndex()
		curr_context_key = list(self.contexts_dict.keys())[curr_context_idx]
		for context_key, context in self.contexts_dict.items():
			if self.active and context_key == curr_context_key:
				# if shell is active, don't deactivate curr context
				continue
			else:
				logger.debug(f'Deactivating bars for {self.name}:{context_key}')
				self.toolbars[context_key].setActiveState(False)
				self.menubars[context_key].setActiveState(False)

		if self.active:
			logger.debug(f'Activating bars for {self.name}:{curr_context_key}')
			self.toolbars[curr_context_key].setActiveState(True)
			self.menubars[curr_context_key].setActiveState(True)

	def _changeToolbarsToContext(self, new_context_index:int) -> None:
		logger.debug(f'Changing toolbar and menu for {self.name} shell')
		new_context_key = list(self.toolbars.keys())[new_context_index]
		# process deselects first in order to clear parent pointer to menubar, otherwise menubar gets deleted (workaround for pyqt5)
		for context_key in self.toolbars.keys():
			if context_key != new_context_key:
				logger.debug(f'Deactivating bars for {self.name}:{context_key}')
				self.toolbars[context_key].setActiveState(False)
				self.menubars[context_key].setActiveState(False)

		logger.debug(f'Activating bars for {self.name}:{new_context_key}')
		self.toolbars[new_context_key].setActiveState(True)
		self.menubars[new_context_key].setActiveState(True)

	def serialiseContexts(self) -> dict[str,Any]:
		state = {}
		for context_key, context in self.contexts_dict.items():
			state[context_key] = context.prepSerialisation()

		return state

	def deserialiseContexts(self, state:dict[str,Any]) -> None:
		for context_key, context_dict in state.items():
			self.contexts_dict[context_key].deSerialise(context_dict)