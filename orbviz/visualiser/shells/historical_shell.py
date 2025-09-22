import logging
import sys

from PyQt5 import QtWidgets

from orbviz.model.data_models import earth_raycast_data, history_data
from orbviz.visualiser.contexts import (
	history2d_context,
	history3d_context,
	history_configuration_context,
	sensor_views_context,
)
import orbviz.visualiser.interface.controls as controls
from orbviz.visualiser.shells import base_shell

logger = logging.getLogger(__name__)

class HistoricalShell(base_shell.BaseShell):
	def __init__(self, parent_window:QtWidgets.QMainWindow, toolbars:dict[str, controls.Toolbar],
															menubars:dict[str, controls.Menubar],
															global_earth_rdm:earth_raycast_data.EarthRayCastData|None=None):

		super().__init__(parent_window, toolbars, menubars, 'HISTORICAL')

		# Create empty data models
		self.data['history'] = history_data.HistoryData()
		self.data['history'].groundstationCollection = self.data['groundstations']
		if global_earth_rdm is None:
			self.data['earth_rdm'] = earth_raycast_data.EarthRayCastData()
		else:
			self.data['earth_rdm'] = global_earth_rdm

		# Build Data Pane
		for item in self.data['history'].datapane_data:
			self.datapane_model.appendData(item)
			self.data['history'].index_updated.connect(self.datapane_model.refresh)

		# Build context panes
		self._addContext('configuration-history', history_configuration_context.HistoryConfigurationContext('configuration-history',
																											self.window,
																											self.data['history']))
		self._addContext('3D-history', history3d_context.History3DContext('3D-history',
																			self.window,
																			self.data['history'],
																			self.data['groundstations']))
		self._addContext('2D-history', history2d_context.History2DContext('2D-history',
																			self.window,
																			self.data['history'],
																			self.data['groundstations'],
																			self.data['earth_rdm']))
		self._addContext('sensors-view-history', sensor_views_context.SensorViewsContext('sensors-view-history',
																							self.window,
																							self.data['history'],
																							self.data['groundstations'],
																							self.data['earth_rdm']))

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

		# shell specific connections
		self.data['history'].data_ready.connect(self._onDataReadySwapTabs)

		# build layout
		self._buildLayout()

		self.updateActiveContext(self.context_tab_stack.currentIndex(), 1)

	def _onDataReadySwapTabs(self) -> None:
		self.context_tab_stack.setCurrentIndex(1)
