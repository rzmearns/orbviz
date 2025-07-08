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
											history_configuration_context,
											sensor_views_context)
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.controls as controls
import satplot.visualiser.interface.widgets as satplot_widgets

logger = logging.getLogger(__name__)

class HistoricalShell():
	def __init__(self, parent_window:QtWidgets.QMainWindow, toolbars:dict[str, controls.Toolbar],
															menubars:dict[str, controls.Menubar],
															global_earth_rdm:earth_raycast_data.EarthRayCastData|None=None):
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
		if global_earth_rdm is None:
			earth_raycast_data_model = earth_raycast_data.EarthRayCastData()
		else:
			earth_raycast_data_model = global_earth_rdm

		# Build context panes
		self.contexts_dict['configuration-history'] = history_configuration_context.HistoryConfigurationContext('configuration-history', self.window, history_data_model)
		self.contexts_dict['3D-history'] = history3d_context.History3DContext('3D-history', self.window, history_data_model)
		self.contexts_dict['2D-history'] = history2d_context.History2DContext('2D-history', self.window, history_data_model, earth_raycast_data_model)
		self.contexts_dict['sensors-view-history'] = sensor_views_context.SensorViewsContext('sensors-view-history', self.window, history_data_model, earth_raycast_data_model)

		# attach relevant toolbars, menubars, add context tabs
		for context_key in self.contexts_dict.keys():
			self.toolbars[context_key] = self.contexts_dict[context_key].controls.toolbar
			self.menubars[context_key] = self.contexts_dict[context_key].controls.menubar
			# self.toolbars[context_key].setActiveState(False)
			# self.menubars[context_key].setActiveState(False)
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

		self.context_tab_stack.tab_changed.connect(self.updateToolMenuBars)
		self.context_tab_stack.tab_changed.connect(self._propagateTimeSlider)

		self.layout.addWidget(self.context_tab_stack)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.widget.setLayout(self.layout)

		self.updateToolMenuBars(self.context_tab_stack.currentIndex(), 1)


	def _propagateTimeSlider(self, old_context_idx:int, new_context_idx:int) -> None:
		curr_context_idx = old_context_idx
		curr_context = list(self.contexts_dict.values())[curr_context_idx]
		new_context = list(self.contexts_dict.values())[new_context_idx]
		curr_slider_idx = curr_context.getIndex()
		if curr_slider_idx is not None:
			new_context.setIndex(curr_slider_idx)

	def updateToolMenuBars(self, curr_context_idx:int|None, new_context_idx:int|None) -> None:
		logger.debug(f'Changing toolbar and menu for {self.name} shell')
		logger.debug(f'{self.name}:{self.active=}')

		if curr_context_idx is None:
			curr_context_idx = self.context_tab_stack.currentIndex()
		curr_context_key = list(self.contexts_dict.keys())[curr_context_idx]

		if new_context_idx is None:
			new_context_idx = self.context_tab_stack.currentIndex()
		new_context_key = list(self.contexts_dict.keys())[new_context_idx]

		# process deselects first in order to clear parent pointer to menubar, otherwise menubar gets deleted (workaround for pyqt5)
		for context_key in self.contexts_dict.keys():
			logger.debug(f'Deactivating bars for {self.name}:{context_key}')
			self.toolbars[context_key].setActiveState(False)
			self.menubars[context_key].setActiveState(False)

		if self.active and new_context_key is not None:
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