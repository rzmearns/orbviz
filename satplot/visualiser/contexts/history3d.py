import satplot

import satplot.visualiser.contexts.canvas_wrappers.history3d as canvaswrapper
from satplot.visualiser.contexts.base import (BaseContext, BaseControls)
import satplot.visualiser.controls.console as console
from satplot.visualiser.controls import controls, widgets
import satplot.util.spacetrack as spacetrack
import satplot.util.celestrak as celestrak
import satplot.util.list_u as list_u
from satplot.model.data_models.data_types import DataType
from progressbar import progressbar
import traceback

import sys
import numpy as np
import datetime as dt

from PyQt5 import QtWidgets, QtCore, QtGui

class History3DContext(BaseContext):
	data_type = DataType.HISTORY

	def __init__(self, name, parent_window, data):
		super().__init__(name)
		self.window = parent_window
		self.data = data
		self._validateDataType()

		self.canvas_wrapper = canvaswrapper.History3DCanvas()
		self.canvas_wrapper.setModel(self.data)
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
		
		# Build display area layout
		'''
		# | ###
		# | ###
		# | ###
		'''
		disp_hsplitter.addWidget(self.controls.config_tabs)
		disp_hsplitter.addWidget(self.canvas_wrapper.canvas.native)

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

	def connectControls(self):
		print(f"Connecting controls of {self.config['name']}")
		self.controls.orbit_controls.submit_button.clicked.connect(self._configureData)
		self.controls.time_slider.add_connect(self._updateDisplayedIndex)
		self.controls.action_dict['center-earth']['callback'] = self._centerCameraEarth
		self.controls.action_dict['center-spacecraft']['callback'] = self._toggleCameraSpacecraft
		self.sccam_state = False
		self.data.data_ready.connect(self._updateDataSources)
		self.data.data_ready.connect(self._updateControls)

	def _validateDataType(self):
		if self.data.getType() != self.data_type:
			print(f"Error: history3D context has wrong data type: {self.data.getType()}", file=sys.stderr)
			print(f"\t should be: {self.data_type}", file=sys.stderr)

	def _configureData(self):
		console.send('Setting up data configuration')
		# Timespan configuration
		self.data.updateConfig('timespan_period_start', self.controls.orbit_controls.period_start.datetime)
		self.data.updateConfig('timespan_period_end', self.controls.orbit_controls.period_end.datetime)
		self.data.updateConfig('sampling_period', self.controls.orbit_controls.sampling_period.period)
		# Primary orbits configuration
		self.data.setPrimarySatellites(self.controls.orbit_controls.getConfig())

		# Supplemental configuration
		has_supplemental_constellation = self.controls.orbit_controls.suppl_constellation_selector.isEnabled()
		if has_supplemental_constellation:
			c_config = self.controls.orbit_controls.suppl_constellation_selector.getConstellationConfig()
			if c_config is None:
				print("Please select a constellation.", file=sys.stderr)
				return
			self.data.setSupplementalConstellation(c_config)
		else:
			self.data.clearSupplementalConstellation()

		# Historical pointing
		if self.controls.orbit_controls.pointing_file_controls.isEnabled():
			self.data.updateConfig('is_pointing_defined', True)
			pointing_file_path = self.controls.orbit_controls.pointing_file_controls._pointing_file_selector.path
			if pointing_file_path is None or \
				pointing_file_path == '':
				print("Displaying spacecraft pointing requires a pointing file.", file=sys.stderr)
				return
			self.data.updateConfig('pointing_defines_timespan', self.controls.orbit_controls.pointing_file_controls.pointingFileDefinesPeriod())
			self.data.updateConfig('pointing_file', pointing_file_path)
			self.data.updateConfig('pointing_invert_transform', self.controls.orbit_controls.pointing_file_controls.pointing_file_inv_toggle.isChecked())
		else:
			self.data.updateConfig('is_pointing_defined', False)
			self.data.updateConfig('pointing_defines_timespan', False)
			self.data.updateConfig('pointing_file', None)
			self.data.updateConfig('pointing_invert_transform', False)

		try:
			self.controls.orbit_controls.submit_button.setEnabled(False)
			self.data.process()
		except Exception as e:
			print(f"Error in configuring data for history3D: {e}", file=sys.stderr)
			self.controls.orbit_controls.submit_button.setEnabled(True)
			raise e

	def _updateControls(self, *args, **kwargs):
		self.controls.time_slider.setRange(self.data.timespan.start,
									  		self.data.timespan.end,
											len(self.data.timespan))
		self.controls.orbit_controls.period_start.setDatetime(self.data.getConfigValue('timespan_period_start'))
		self.controls.orbit_controls.period_end.setDatetime(self.data.getConfigValue('timespan_period_end'))
		self.controls.time_slider._curr_dt_picker.setDatetime(self.data.timespan.start)
		self.controls.orbit_controls.submit_button.setEnabled(True)

	def _updateDataSources(self):
		self.canvas_wrapper.modelUpdated()
		self.canvas_wrapper.setFirstDrawFlags()
		self._updateDisplayedIndex(self.controls.time_slider.slider.value())

	def _updateDisplayedIndex(self, index):
		self.canvas_wrapper.updateIndex(index)
		self.canvas_wrapper.recomputeRedraw()
		console.send(self.data.timespan[index])

	def loadState(self):
		pass

	def saveState(self):
		pass

	def deSerialise(self, state_dict):
		pass
		# self.data = state_dict['data']
		# self.canvas_wrapper.setSource(self.data['timespan'],
		# 								self.data['orbit'],
		# 								self.data['pointing'],
		# 								self.data['pointing_invert_transform'],
		# 								self.data['constellation_list'],
		# 								self.data['constellation_beam_angle'])
		# self.canvas_wrapper.setFirstDrawFlags()
		# console.send(f"Drawing {self.data['name']} Assets...")
		# self.controls.deSerialise(state_dict['controls'])
		# self.canvas_wrapper.deSerialise(state_dict['camera'])

	def prepSerialisation(self):
		pass
		# state = {}
		# state['data'] = self.data
		# state['controls'] = self.controls.prepSerialisation()
		# state['camera'] = self.canvas_wrapper.prepSerialisation()
		# return state



	def _centerCameraEarth(self):
		if self.sccam_state and self.controls.toolbar.button_dict['center-spacecraft'].isChecked():
			# if center cam on sc is on, turn it off when selecting center cam on earth.
			self.controls.toolbar.button_dict['center-spacecraft'].setChecked(False)
		self.sccam_state = False
		self.canvas_wrapper.centerCameraEarth()	

	def _toggleCameraSpacecraft(self):
		self.sccam_state = not self.sccam_state

		if self.sccam_state:
			self.canvas_wrapper.centerCameraSpacecraft()
			# setting button to checkable in case camera set to center via menu
			self.controls.toolbar.button_dict['center-spacecraft'].setChecked(True)



		
	class Controls(BaseControls):
		def __init__(self, parent_context, canvas_wrapper):
			self.context = parent_context
			super().__init__(self.context.config['name'])
			# Prep config widgets
			self.orbit_controls = controls.OrbitConfigs()
			self.config_controls = controls.OptionConfigs(canvas_wrapper.assets)
			
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

		def setHotkeys(self):
			self.shortcuts={}
			self.shortcuts['PgDown'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgDown'), self.context.window)
			self.shortcuts['PgDown'].activated.connect(self.time_slider.incrementValue)
			self.shortcuts['PgDown'].activated.connect(self._updateCam)
			self.shortcuts['PgUp'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgUp'), self.context.window)
			self.shortcuts['PgUp'].activated.connect(self.time_slider.decrementValue)
			self.shortcuts['PgUp'].activated.connect(self._updateCam)
			self.shortcuts['Home'] = QtWidgets.QShortcut(QtGui.QKeySequence('Home'), self.context.window)
			self.shortcuts['Home'].activated.connect(self.time_slider.setBeginning)
			self.shortcuts['Home'].activated.connect(self._updateCam)
			self.shortcuts['End'] = QtWidgets.QShortcut(QtGui.QKeySequence('End'), self.context.window)
			self.shortcuts['End'].activated.connect(self.time_slider.setEnd)
			self.shortcuts['End'].activated.connect(self._updateCam)

		def _updateCam(self):
			if self.context.sccam_state:
				self.context.canvas_wrapper.centerCameraSpacecraft(set_zoom=False)

		def prepSerialisation(self):
			state = {}
			# state['orbit_controls'] = self.orbit_controls.prepSerialisation()
			# state['config_controls'] = self.config_controls.prepSerialisation()
			state['time_slider'] = {}
			state['time_slider']['start_dt'] = self.time_slider.start_dt
			state['time_slider']['end_dt'] = self.time_slider.end_dt
			state['time_slider']['num_ticks'] = self.time_slider.num_ticks
			state['time_slider']['curr_index'] = self.time_slider.getValue()
			state['pointing'] = {}
			state['pointing']['pointing_invert_transform'] = self.orbit_controls.pointing_file_controls.pointing_file_inv_toggle.isChecked()
			return state

		def deSerialise(self, state):
			self.time_slider.setRange(state['time_slider']['start_dt'],
							 			state['time_slider']['end_dt'],
										state['time_slider']['num_ticks'])
			self.time_slider.setValue(state['time_slider']['curr_index'])

