import logging
import sys
from typing import Any

from PyQt5 import QtWidgets, QtCore, QtGui

import satplot
from satplot.model.data_models import (history_data,
										earth_raycast_data)
from satplot.model.data_models import datapane as datapane_model
from satplot.visualiser.contexts import (base_context,
											blank_context,
											history2d_context,
											history3d_context,
											history_configuration_context,
											sensor_views_context)
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.controls as controls
import satplot.visualiser.interface.datapane as datapane
import satplot.visualiser.interface.widgets as satplot_widgets

logger = logging.getLogger(__name__)

class PlanningShell():
	def __init__(self, parent_window:QtWidgets.QMainWindow, toolbars:dict[str, controls.Toolbar],
															menubars:dict[str, controls.Menubar],
															global_earth_rdm:earth_raycast_data.EarthRayCastData|None=None):
		self.name = 'PLANNING'
		self.window = parent_window
		self.widget = QtWidgets.QWidget()
		self.layout = QtWidgets.QVBoxLayout()
		self.toolbars = toolbars
		self.menubars = menubars
		self.active = False
		self.active_context = None

		datapane_hsplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
		datapane_hsplitter.setObjectName('window_hsplitter')
		datapane_hsplitter.setStyleSheet('''
					QSplitter#window_hsplitter::handle {
								background-color: #DCDCDC;
								padding: 2px;
							}
					QSplitter#window_hsplitter::handle:horizontal {
								height: 1px;
								color: #ff0000;
							}
							''')


		self.data: dict[str, Any] = {}
		self.toolbars: dict[str, controls.Toolbar] = {}
		self.menubars: dict[str, controls.Menubar] = {}
		self.contexts_dict: dict[str, base_context.BaseContext] = {}
		self.context_tab_stack = satplot_widgets.ColumnarStackedTabWidget()
		self.context_tab_stack.setTabPosition(QtWidgets.QTabWidget.West)
		self.datapane_model = datapane_model.DataPaneModel()
		self.datapane = datapane.DataPaneWidget(self.datapane_model)

		# Create empty data models
		history_data_model = history_data.HistoryData()
		if global_earth_rdm is None:
			earth_raycast_data_model = earth_raycast_data.EarthRayCastData()
		else:
			earth_raycast_data_model = global_earth_rdm

		# Build Data Pane
		for item in history_data_model.datapane_data:
			self.datapane_model.appendData(item)
			# self.shell_dict['history'].history_data_model.data_ready
			history_data_model.index_updated.connect(self.datapane_model.refresh)

		# Build context panes
		self._addContext('configuration-history', history_configuration_context.HistoryConfigurationContext('configuration-history', self.window, history_data_model))
		self._addContext('3D-planning', history3d_context.History3DContext('3D-planning', self.window, history_data_model))
		self._addContext('2D-planning', history2d_context.History2DContext('2D-planning', self.window, history_data_model, earth_raycast_data_model))
		self._addContext('sensors-view',sensor_views_context.SensorViewsContext('sensors-view-planning', self.window, history_data_model, earth_raycast_data_model))

		# check toolbar/menubar indices are the same
		for ii, key in enumerate(self.toolbars.keys()):
			if list(self.menubars.keys())[ii] != key:
				logger.error(f'Context toolbars and menubar indices do not match for contexts')
				logger.error(f'Toolbars: {self.toolbars.keys()}')
				logger.error(f'Menubars: {self.menubars.keys()}')
				raise ValueError('Toolbars and Menubars indices do not match')
				sys.exit()

		self.context_tab_stack.tab_changed.connect(self.updateActiveContext)
		self.context_tab_stack.tab_changed.connect(self._propagateTimeSlider)

		datapane_hsplitter.addWidget(self.context_tab_stack)
		datapane_hsplitter.addWidget(self.datapane)

		self.layout.addWidget(datapane_hsplitter)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.widget.setLayout(self.layout)

		self.updateActiveContext(self.context_tab_stack.currentIndex(), 1)

	def _propagateTimeSlider(self, old_context_idx:int, new_context_idx:int) -> None:
		curr_context_idx = old_context_idx
		curr_context = list(self.contexts_dict.values())[curr_context_idx]
		new_context = list(self.contexts_dict.values())[new_context_idx]
		curr_slider_idx = curr_context.getIndex()
		if curr_slider_idx is not None:
			new_context.setIndex(curr_slider_idx)

	def _addContext(self, context_name:str, context:base_context.BaseContext) -> None:
		# TODO: add to abstracted shell
		# Keep track of context reference
		self.contexts_dict[context_name] = context

		# Keep track of toolbar references
		if context.controls is not None and context.controls.toolbar is not None:
			self.toolbars[context_name] = context.controls.toolbar
		else:
			logger.warning('Context: %s:%s, does not have a toolbar', context_name, context)\

		# Keep track of menubar references
		if context.controls is not None and context.controls.menubar is not None:
			self.menubars[context_name] = context.controls.menubar
		else:
			logger.warning('Context: %s:%s, does not have a menubar', context_name, context)

		# add tab to shell context stack
		tab_label = ' '.join(context_name.split('-')[:-1]).title()
		self.context_tab_stack.addTab(context.widget, tab_label)
		if hasattr(context,'canvas_wrapper') and context.canvas_wrapper is not None:
			if hasattr(context.canvas_wrapper, 'mouseOverText') and context.canvas_wrapper.mouseOverText is not None:
				context.canvas_wrapper.mouseOverText.notifier.text_updated.connect(self.datapane.setMouseText)

	def updateActiveContext(self, curr_context_idx:int|None, new_context_idx:int|None) -> None:
		logger.debug(f'Changing toolbar and menu for {self.name} shell')
		logger.debug(f'{self.name}:{self.active=}')

		if curr_context_idx is None:
			curr_context_idx = self.context_tab_stack.currentIndex()
		curr_context_key = list(self.contexts_dict.keys())[curr_context_idx]

		if new_context_idx is None:
			new_context_idx = self.context_tab_stack.currentIndex()
		new_context_key = list(self.contexts_dict.keys())[new_context_idx]
		self.active_context = self.contexts_dict[new_context_key]

		# process deselects first in order to clear parent pointer to menubar, otherwise menubar gets deleted (workaround for pyqt5)
		for context_key in self.contexts_dict.keys():
			logger.debug(f'Deactivating bars for {self.name}:{context_key}')
			self.toolbars[context_key].setActiveState(False)
			self.menubars[context_key].setActiveState(False)

		if self.active and new_context_key is not None:
			logger.debug(f'Activating bars for {self.name}:{new_context_key}')
			self.toolbars[new_context_key].setActiveState(True)
			self.menubars[new_context_key].setActiveState(True)

		self.contexts_dict[curr_context_key].makeDormant()
		self.contexts_dict[new_context_key].makeActive()

	def serialiseContexts(self) -> dict[str,Any]:
		state = {}
		for context_key, context in self.contexts_dict.items():
			state[context_key] = context.prepSerialisation()

		return state

	def deserialiseContexts(self, state:dict[str,Any]) -> None:
		for context_key, context_dict in state.items():
			self.contexts_dict[context_key].deSerialise(context_dict)

	def makeActive(self) -> None:
		self.active = True

	def makeDormant(self) -> None:
		self.active = False
