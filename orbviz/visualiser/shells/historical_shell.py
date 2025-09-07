import logging
import sys

from PyQt5 import QtWidgets

from orbviz.model.data_models import earth_raycast_data, history_data, timeseries
from orbviz.visualiser.contexts import (
	history2d_context,
	history3d_context,
	history_configuration_context,
	sensor_views_context,
	timeseries_plot_context,
)
import orbviz.visualiser.interface.controls as console
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
		self._generic_timeseries_created = False
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
		self._addContext('timeseries-history', timeseries_plot_context.TimeSeriesContext('timeseries-history',
																							self.window,
																							self.timeseries_data))

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
		self.data['history'].data_ready.connect(self._onDataReady)

		# build layout
		self._buildLayout()

		self.updateActiveContext(self.context_tab_stack.currentIndex(), 1)

	def _onDataReady(self) -> None:
		if not self._generic_timeseries_created:
			self._createGenericTS()
		for context in self.contexts_dict.values():
			context._procDataUpdated()
		# swap context tab to 3D
		self.context_tab_stack.setCurrentIndex(1)

	def _createGenericTS(self) -> None:
		console.send('Building Timeseries from History Data Model')
		for key in ['sun', 'moon','orbits.pos', 'orbits.pos_ecef','orbits.vel','orbits.vel_ecef','orbits.lat','orbits.lon','orbits.alt','orbits.eclipse']:
			for ts_key, ts in timeseries.createTimeSeriesFromDataModel(self.data['history'], key).items():
				self.timeseries_data[ts_key] = ts
		self._generic_timeseries_created = True

		self.contexts_dict['timeseries-history'].canvas_wrapper.modelUpdated()