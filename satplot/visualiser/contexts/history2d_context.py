import logging
import sys
from typing import Any

from PyQt5 import QtWidgets, QtCore, QtGui

import satplot.model.data_models.data_types as data_types
from satplot.model.data_models.history_data import HistoryData

import satplot.visualiser.contexts.base_context as base
from satplot.visualiser.contexts.canvas_wrappers.base_cw import (BaseCanvas)
import satplot.visualiser.contexts.canvas_wrappers.history2d_cw as history2d_cw
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.controls as controls
import satplot.visualiser.interface.widgets as widgets

logger = logging.getLogger(__name__)

class History2DContext(base.BaseContext):
	data_type = data_types.DataType.HISTORY

	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow, data:HistoryData):
		super().__init__(name, data)
		self.window = parent_window
		self._validateDataType()
		self.data = data
		self.canvas_wrapper = history2d_cw.History2DCanvasWrapper()
		self.canvas_wrapper.setModel(self.data)
		self.controls = Controls(self, self.canvas_wrapper)

		disp_hsplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
		disp_hsplitter.setObjectName('disp_hsplitter')
		disp_hsplitter.setStyleSheet('''
					QSplitter#disp_hsplitter::handle {
								background-color: #DCDCDC;
							}
							''')
		content_widget = QtWidgets.QWidget()
		content_vlayout = QtWidgets.QVBoxLayout()
		
		# Build display area layout
		'''
		# | ###
		# | ###
		# | ###
		'''
		disp_hsplitter.addWidget(self.controls.config_tabs)
		disp_hsplitter.addWidget(self.canvas_wrapper.getCanvas().native)

		# Build area down to bottom of time slider
		'''
		# | ###
		# | ###
		# | ###
		#######
		'''
		content_vlayout.addWidget(disp_hsplitter)
		content_vlayout.addWidget(self.controls.time_slider)
		content_widget.setLayout(content_vlayout)

		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(content_widget)

	def connectControls(self) -> None:
		logger.info(f"Connecting controls of {self.config['name']}")
		self.controls.orbit_controls.submit_button.clicked.connect(self._configureData)
		self.controls.time_slider.add_connect(self._updateDisplayedIndex)
		self.controls.action_dict['center-earth']['callback'] = self._centerCameraEarth
		self.controls.action_dict['center-spacecraft']['callback'] = self._toggleCameraSpacecraft
		self.sccam_state = False
		if self.data is None:
			logger.warning(f'Context History3D: {self} does not have a data model.')
			raise AttributeError(f'Context History3D: {self} does not have a data model.')
		self.data.data_ready.connect(self._updateDataSources)
		self.data.data_ready.connect(self._updateControls)

	def _validateDataType(self) -> None:
		if self.data is not None and self.data.getType() != self.data_type:
			console.sendErr(f"Error: history3D context has wrong data type: {self.data.getType()}")
			console.sendErr(f"\t should be: {self.data_type}")

	def _configureData(self) -> None:
		logger.info(f'Setting up data configuration for context: {self}')
		console.send('Setting up data configuration')
		# Timespan configuration
		if self.data is None:
			logger.warning(f"model data is not set for context {self.config['name']}:{self}")
			raise ValueError(f"model data is not set for context {self.config['name']}:{self}")

		self.data.updateConfig('timespan_period_start', self.controls.orbit_controls.period_start.datetime)
		self.data.updateConfig('timespan_period_end', self.controls.orbit_controls.period_end.datetime)
		self.data.updateConfig('sampling_period', self.controls.orbit_controls.sampling_period.period)
		# Primary orbits configuration
		self.data.setPrimaryConfig(self.controls.orbit_controls.getConfig())

		# Supplemental configuration
		has_supplemental_constellation = self.controls.orbit_controls.suppl_constellation_selector.isEnabled()
		if has_supplemental_constellation:
			c_config = self.controls.orbit_controls.suppl_constellation_selector.getConstellationConfig()
			if c_config is None:
				console.sendErr("Supplementary constellation enabled: Please select a constellation.")
				return
			self.data.setSupplementalConstellation(c_config)
		else:
			self.data.clearSupplementalConstellation()

		# Historical pointing
		if self.controls.orbit_controls.pointing_file_controls.isEnabled():
			logger.info(f'Pointing defined. Setting pointing configuration for {self}')
			self.data.updateConfig('is_pointing_defined', True)
			pointing_file_path = self.controls.orbit_controls.pointing_file_controls._pointing_file_selector.path
			if pointing_file_path is None or \
				pointing_file_path == '':
				console.sendErr("Displaying spacecraft pointing requires a pointing file.")
				return
			self.data.updateConfig('pointing_defines_timespan', self.controls.orbit_controls.pointing_file_controls.pointingFileDefinesPeriod())
			self.data.updateConfig('pointing_file', pointing_file_path)
			self.data.updateConfig('pointing_invert_transform', self.controls.orbit_controls.pointing_file_controls.pointing_file_inv_toggle.isChecked())
		else:
			logger.info(f'Pointing not defined. Clearing pointing configuration for {self}')
			self.data.updateConfig('is_pointing_defined', False)
			self.data.updateConfig('pointing_defines_timespan', False)
			self.data.updateConfig('pointing_file', None)
			self.data.updateConfig('pointing_invert_transform', False)

		try:
			self.controls.orbit_controls.submit_button.setEnabled(False)
			self.data.process()
		except Exception as e:
			logger.warning(f"Error in configuring data for history3D: {e}")
			console.sendErr(f"Error in configuring data for history3D: {e}")
			self.controls.orbit_controls.submit_button.setEnabled(True)
			raise e

	def _updateControls(self, *args, **kwargs) -> None:

		self.controls.time_slider.setRange(self.data.getTimespan().start,
									  		self.data.getTimespan().end,
											len(self.data.getTimespan()))
		self.controls.orbit_controls.period_start.setDatetime(self.data.getConfigValue('timespan_period_start'))
		self.controls.orbit_controls.period_end.setDatetime(self.data.getConfigValue('timespan_period_end'))
		self.controls.time_slider._curr_dt_picker.setDatetime(self.data.getTimespan().start)
		self.controls.orbit_controls.submit_button.setEnabled(True)

	def _updateDataSources(self) -> None:
		self.canvas_wrapper.modelUpdated()
		self.controls.rebuildOptions()
		self.canvas_wrapper.setFirstDrawFlags()
		self._updateDisplayedIndex(self.controls.time_slider.slider.value())

	def _updateDisplayedIndex(self, index:int) -> None:
		if self.data is None:
			logger.warning(f"model data is not set for context {self.config['name']}:{self}")
			ValueError(f"model data is not set for context {self.config['name']}:{self}")
		self.canvas_wrapper.updateIndex(index)
		self.canvas_wrapper.recomputeRedraw()

	def loadState(self) -> None:
		pass

	def saveState(self) -> None:
		pass

	def deSerialise(self, state_dict: dict[str, Any]) -> None:
		self.data.deSerialise(state_dict['data'])
		self._updateDataSources()
		self.canvas_wrapper.deSerialise(state_dict['camera'])
		self.controls.deSerialise(state_dict['controls'])

		# self.data = state_dict['data']
		# self.canvas_wrapper.setSource(self.data['timespan'],
		# 								self.data['orbit'],
		# 								self.data['pointing'],
		# 								self.data['pointing_invert_transform'],
		# 								self.data['constellation_list'],
		# 								self.data['constellation_beam_angle'])
		# self.canvas_wrapper.setFirstDrawFlags()
		# console.send(f"Drawing {self.data['name']} Assets...")

		# self.canvas_wrapper.deSerialise(state_dict['camera'])

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['data'] = self.data.prepSerialisation()
		state['controls'] = self.controls.prepSerialisation()
		state['camera'] = self.canvas_wrapper.prepSerialisation()
		return state



	def _centerCameraEarth(self) -> None:
		if self.sccam_state and self.controls.toolbar.button_dict['center-spacecraft'].isChecked():
			# if center cam on sc is on, turn it off when selecting center cam on earth.
			self.controls.toolbar.button_dict['center-spacecraft'].setChecked(False)
		self.sccam_state = False
		self.canvas_wrapper.centerCameraEarth()	

	def _toggleCameraSpacecraft(self) -> None:
		self.sccam_state = not self.sccam_state

		if self.sccam_state:
			self.canvas_wrapper.centerCameraSpacecraft()
			# setting button to checkable in case camera set to center via menu
			self.controls.toolbar.button_dict['center-spacecraft'].setChecked(True)



		
class Controls(base.BaseControls):
	def __init__(self, parent_context:base.BaseContext, canvas_wrapper:BaseCanvas):
		self.context = parent_context
		self.cw = canvas_wrapper
		super().__init__(self.context.config['name'])
		# Prep config widgets
		self.orbit_controls = controls.OrbitConfigs()
		self.config_controls = controls.OptionConfigs(self.cw.assets)

		# Wrap config widgets in tabs
		self.config_tabs = QtWidgets.QTabWidget()
		self.config_tabs.addTab(self.orbit_controls, 'Orbit')
		self.config_tabs.addTab(self.config_controls, 'Visual Options')

		# Prep time slider
		self.time_slider = widgets.TimeSlider()
		self.time_slider.setFixedHeight(50)

		# Prep toolbars
		self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.config['name'])
		self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.config['name'])

		self.setHotkeys()
		self._connectSliderCamUpdate()

	def setHotkeys(self):
		self.shortcuts={}
		# self.shortcuts['PgDown'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgDown'), self.context.window)
		# self.shortcuts['PgDown'].activated.connect(self.time_slider.incrementValue)
		# self.shortcuts['PgDown'].activated.connect(self._updateCam)
		# self.shortcuts['PgUp'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgUp'), self.context.window)
		# self.shortcuts['PgUp'].activated.connect(self.time_slider.decrementValue)
		# self.shortcuts['PgUp'].activated.connect(self._updateCam)
		# self.shortcuts['Home'] = QtWidgets.QShortcut(QtGui.QKeySequence('Home'), self.context.window)
		# self.shortcuts['Home'].activated.connect(self.time_slider.setBeginning)
		# self.shortcuts['Home'].activated.connect(self._updateCam)
		# self.shortcuts['End'] = QtWidgets.QShortcut(QtGui.QKeySequence('End'), self.context.window)
		# self.shortcuts['End'].activated.connect(self.time_slider.setEnd)
		# self.shortcuts['End'].activated.connect(self._updateCam)

	def _connectSliderCamUpdate(self):
		self.time_slider.slider.valueChanged.connect(self._updateCam)

	def _updateCam(self):
		if self.context.sccam_state and self.context.canvas_wrapper is not None:
			self.context.canvas_wrapper.centerCameraSpacecraft(set_zoom=False)

	def prepSerialisation(self):
		state = {}
		state['orbit_controls'] = self.orbit_controls.prepSerialisation()
		state['config_controls'] = self.config_controls.prepSerialisation()
		state['time_slider'] = self.time_slider.prepSerialisation()
		return state

	def deSerialise(self, state):
		self.orbit_controls.deSerialise(state['orbit_controls'])
		self.time_slider.deSerialise(state['time_slider'])
		self.config_controls.deSerialise(state['config_controls'])


	def rebuildOptions(self):
		self.config_controls.rebuild()