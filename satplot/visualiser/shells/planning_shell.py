import logging
import sys

import typing

from PyQt5 import QtWidgets

from satplot.model.data_models import earth_raycast_data, history_data
from satplot.visualiser.contexts import (
	history2d_context,
	history3d_context,
	history_configuration_context,
	sensor_views_context,
)
import satplot.visualiser.interface.controls as controls
from satplot.visualiser.shells import base_shell

logger = logging.getLogger(__name__)

class PlanningShell(base_shell.BaseShell):
	def __init__(self, parent_window:QtWidgets.QMainWindow, toolbars:dict[str, controls.Toolbar],
															menubars:dict[str, controls.Menubar],
															global_earth_rdm:earth_raycast_data.EarthRayCastData|None=None):
		super().__init__(parent_window, toolbars, menubars, 'PLANNING')

		# Create empty data models
		self.data['history_data_model'] = history_data.HistoryData()
		if global_earth_rdm is None:
			self.data['earth_raycast_data_model'] = earth_raycast_data.EarthRayCastData()
		else:
			self.data['earth_raycast_data_model'] = global_earth_rdm

		# Build Data Pane
		for item in self.data['history_data_model'].datapane_data:
			self.datapane_model.appendData(item)
			self.data['history_data_model'].index_updated.connect(self.datapane_model.refresh)

		# Build context panes
		self._addContext('configuration-history', history_configuration_context.HistoryConfigurationContext('configuration-history',
																												self.window,
																												self.data['history_data_model']))
		self._addContext('3D-planning', history3d_context.History3DContext('3D-planning',
																			self.window,
																			self.data['history_data_model'],
																			self.data['groundstations']))
		self._addContext('2D-planning', history2d_context.History2DContext('2D-planning',
																			self.window,
																			self.data['history_data_model'],
																			self.data['groundstations'],
																			self.data['earth_raycast_data_model']))
		self._addContext('sensors-view',sensor_views_context.SensorViewsContext('sensors-view-planning',
																					self.window,
																					self.data['history_data_model'],
																					self.data['groundstations'],
																					self.data['earth_raycast_data_model']))

		# check toolbar/menubar indices are the same
		for ii, key in enumerate(self.toolbars.keys()):
			if list(self.menubars.keys())[ii] != key:
				logger.error('Context toolbars and menubar indices do not match for contexts')
				logger.error('Toolbars: %s', self.toolbars.keys())
				logger.error('Menubars: %s', self.menubars.keys())
				raise ValueError('Toolbars and Menubars indices do not match')
				sys.exit()

		# generic shell connections
		self._connectGenericTabSignals()

		# build layout
		self._buildLayout()

		self.updateActiveContext(self.context_tab_stack.currentIndex(), 1)
