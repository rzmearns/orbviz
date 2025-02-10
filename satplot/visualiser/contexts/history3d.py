import satplot
import spherapy.timespan as timespan
import spherapy.orbit as orbit
from satplot.visualiser import canvaswrappers
from satplot.visualiser.contexts.base import (BaseContext, BaseDataWorker, BaseControls)
import satplot.visualiser.controls.console as console
from satplot.visualiser.controls import controls, widgets
import satplot.util.spacetrack as spacetrack
import satplot.util.celestrak as celestrak
import satplot.util.list_u as list_u
from progressbar import progressbar
import traceback

import sys
import numpy as np
import datetime as dt

from PyQt5 import QtWidgets, QtCore, QtGui

class History3DContext(BaseContext):
	def __init__(self, name, parent_window):
		super().__init__(name)
		self.window = parent_window
		self.data['timespan'] = None
		self.data['orbit'] = None
		self.data['period_start'] = None
		self.data['period_end'] = None
		self.data['sampling_period'] = None
		self.data['prim_orbit_TLE_path'] = None
		self.data['constellation_list'] = None
		self.data['constellation_index'] = None
		self.data['constellation_file'] = None
		self.data['constellation_name'] = None
		self.data['constellation_beam_angle'] = None
		self.data['pointing_file'] = None
		self.data['pointing'] = None

		self.controls = None
		self.canvas_wrapper = canvaswrappers.History3D()
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
		self.controls.orbit_controls.submit_button.clicked.connect(self._loadData)
		self.controls.time_slider.add_connect(self._updateIndex)
		self.controls.action_dict['center-earth']['callback'] = self._centerCameraEarth
		self.controls.action_dict['center-spacecraft']['callback'] = self._toggleCameraSpacecraft
		self.sccam_state = False

	def _loadData(self):
		console.send('Started Data Load')
		self.data['period_start'] = self.controls.orbit_controls.period_start.datetime
		self.data['period_end'] = self.controls.orbit_controls.period_end.datetime
		self.data['sampling_period'] = self.controls.orbit_controls.sampling_period.period
		prim_config = self.controls.orbit_controls.getConfig()
		self.data['prim_config'] = prim_config
		if self.controls.orbit_controls.suppl_constellation_selector.isEnabled():
			c_config = self.controls.orbit_controls.suppl_constellation_selector.getConstellationConfig()
			if c_config is None:
				print("Please select a constellation.", file=sys.stderr)
				return
			self.data['constellation_config'] = c_config
			self.data['constellation_name'] = c_config['name']
			self.data['constellation_beam_angle'] = c_config['beam_width']
		else:
			self.data['constellation_config'] = None
			self.data['constellation_name'] = None
			self.data['constellation_beam_angle'] = None

		self.data['pnt_defines_sampling'] = False
		if self.controls.orbit_controls.pointing_file_controls.isEnabled():
			self.data['pointing_file'] = self.controls.orbit_controls.pointing_file_controls._pointing_file_selector.path
			self.data['pointing_invert_transform'] = self.controls.orbit_controls.pointing_file_controls.pointing_file_inv_toggle.isChecked()
			if self.controls.orbit_controls.pointing_file_controls.pointingFileDefinesPeriod():
				self.data['pnt_defines_sampling'] = True
				pointing_dates,q = readPointingData(self.data['pointing_file'])
				self.data['period_start'] = pointing_dates[0]
				print(f'{pointing_dates[0]=}')
				print(f'{pointing_dates[-1]=}')
				self.data['period_end'] = pointing_dates[-1]
				self.data['sampling_period'] = 1
		else:
			self.data['pointing_file'] = None
			self.data['pointing_invert_transform'] = None
		
		# Create worker
		console.send(f'Constellation: {self.data["constellation_name"]}')
		console.send('Creating loadDataWorker')
		self.load_worker = self.LoadDataWorker(self.data['period_start'], 
										 		self.data['period_end'],
												self.data['sampling_period'],
												self.data['prim_config'],
												c_config = self.data['constellation_config'],
												p_file = self.data['pointing_file'],
												p_file_defines_sampling=self.data['pnt_defines_sampling'])

		try:
			self.controls.orbit_controls.submit_button.setEnabled(False)
			self._setUpLoadWorkerThread()
			console.send(f'Starting thread')
			self.load_worker_thread.start()
		except Exception as e:
			console.send(f"Error history3D ln 128: {e}", file=sys.stderr)
			self.controls.orbit_controls.submit_button.setEnabled(True)
			raise e

	def _updateControls(self, *args, **kwargs):
		self.controls.orbit_controls.period_start.setDatetime(self.data['period_start'])
		self.controls.orbit_controls.period_end.setDatetime(self.data['period_end'])
		self.controls.orbit_controls.submit_button.setEnabled(True)

	def _updateDataSources(self, t, o, c_list, pointing_q):
		self.data['timespan'] = t
		self.data['orbit'] = o		
		self.controls.time_slider.setRange(self.data['timespan'].start,
									  		self.data['timespan'].end,
											len(self.data['timespan']))
		self.controls.time_slider._curr_dt_picker.setDatetime(self.data['timespan'].start)
		
		if len(pointing_q) > 0:
			self.data['pointing']=pointing_q
		else:
			self.data['pointing'] = None
		
		if self.data['constellation_config'] is not None:
			self.data['constellation_list'] = c_list
		else:
			self.data['constellation_list'] = None

		if self.data['constellation_list'] is not None:
			console.send(f'Length Constellation list: {len(self.data["constellation_list"])}')
		else:
			console.send(f'Length Constellation list: {self.data["constellation_list"]}')
		console.send(f'Constellation beam_angle: {self.data["constellation_beam_angle"]}')

		self.canvas_wrapper.setSource(self.data['timespan'],
										self.data['orbit'],
										self.data['pointing'],
										self.data['pointing_invert_transform'],
										self.data['constellation_list'],
										self.data['constellation_beam_angle'])
		self.canvas_wrapper.setFirstDrawFlags()
		console.send(f"Drawing {self.data['name']} Assets...")
		curr_index = self.controls.time_slider.slider.value()
		self._updateIndex(curr_index)

	def _updateIndex(self, index):
		self.canvas_wrapper.updateIndex(index)
		console.send(self.data['timespan'][index])

	def loadState(self):
		pass

	def saveState(self):
		pass

	def deSerialise(self, state_dict):
		self.data = state_dict['data']
		self.canvas_wrapper.setSource(self.data['timespan'],
										self.data['orbit'],
										self.data['pointing'],
										self.data['pointing_invert_transform'],
										self.data['constellation_list'],
										self.data['constellation_beam_angle'])
		self.canvas_wrapper.setFirstDrawFlags()
		console.send(f"Drawing {self.data['name']} Assets...")
		self.controls.deSerialise(state_dict['controls'])
		self.canvas_wrapper.deSerialise(state_dict['camera'])

	def prepSerialisation(self):
		state = {}
		state['data'] = self.data
		state['controls'] = self.controls.prepSerialisation()
		state['camera'] = self.canvas_wrapper.prepSerialisation()
		return state

	def _cleanUpErrorInLoadWorkerThread(self, err_str=None):
		self.controls.orbit_controls.submit_button.setEnabled(True)
		return super()._cleanUpErrorInLoadWorkerThread(err_str=err_str)

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

	class LoadDataWorker(BaseDataWorker):
		finished = QtCore.pyqtSignal(timespan.TimeSpan, orbit.Orbit, list, np.ndarray)
		error = QtCore.pyqtSignal(str)

		def __init__(self, period_start, period_end, sampling_period, prim_config,
			   			c_config=None, p_file=None, p_file_defines_sampling=False, *args, **kwargs):
			super().__init__(*args, **kwargs)
			self.period_start = period_start
			self.period_end = period_end
			self.timestep = sampling_period
			self.prim_config = prim_config
			self.t = None
			self.o = None
			self.c_config = c_config
			self.c_list = []
			self.p_file = p_file
			self.p_file_defines_sampling = p_file_defines_sampling
			self.pointing_q = None

		def run(self):
			try:
				console.send("Started Load Data Worker thread")
				# TIMESPAN

				if self.p_file is not None and self.p_file != '' and self.p_file_defines_sampling:
					console.send('Using pointing file to create timespan')
					pointing_dates, pointing_q = readPointingData(self.p_file)
					self.t = timespan.TimeSpan.fromDatetime(pointing_dates)
				else:
					self.period_start.replace(microsecond=0)
					self.period_end.replace(microsecond=0)
					time_period = int((self.period_end - self.period_start).total_seconds())
					console.send(f"Creating Timespan from {self.period_start} -> {self.period_end} ...")
					self.t = timespan.TimeSpan(self.period_start,
									timestep=f'{self.timestep}S',
									timeperiod=f'{time_period}S')
				console.send(f"\tDuration: {self.t.time_period}")
				console.send(f"\tNumber of steps: {len(self.t)}")
				console.send(f"\tLength of timestep: {self.t.time_step}")

				# PRIMARY ORBIT
				if spacetrack.doCredentialsExist():
					spacetrack.updateTLEs(self.prim_config)
					prim_orbit_TLE_path = spacetrack.getTLEFilePath(spacetrack.getSatIDs(self.prim_config)[0])
					use_temp = False
				else:
					celestrak.updateTLEs(self.prim_config)
					prim_orbit_TLE_path = celestrak.getTLEFilePath(spacetrack.getSatIDs(self.prim_config)[0])
					use_temp = True
				
				console.send(f"Propagating orbit from {prim_orbit_TLE_path.split('/')[-1]} ...")
				self.o = orbit.Orbit.fromTLE(self.t, prim_orbit_TLE_path)
				console.send(f"\tNumber of steps in single orbit: {self.o.period_steps}")

				# POINTING FILE
				self.pointing_q = np.array(())
				if self.p_file is not None and self.p_file != '':
					console.send(f"Loading pointing from {self.p_file.split('/')[-1]}")
					pointing_dates, pointing_q = readPointingData(self.p_file)

					# total_secs = lambda x: x.total_seconds()
					# total_secs = np.vectorize(total_secs)
					# sample_periods = total_secs(np.diff(pointing_dates))
					# different_sample_periods = np.where(sample_periods != sample_periods[0])[0]
					# if len(different_sample_periods) != 0:
					# 	print(f"WARNING: pointing samples are not taken at regular intervals - {pointing_dates[different_sample_periods]}", file=sys.stderr)

					# if sample_periods[0] != self.timestep:
					# 	print(f"ERROR: pointing file sampling period do not match the selected visualiser sampling period", file=sys.stderr)
					# 	self.error.emit(f"ERROR: pointing file sampling period do not match the selected visualiser sampling period")
					# 	return
					
					# pointing_start_index = np.where(pointing_dates==self.period_start)[0]
					# if len(pointing_start_index) == 0:
					# 	print(f"ERROR: pointing file does not contain the selected start time {self.period_start}", file=sys.stderr)
					# 	self.error.emit("ERROR: pointing file does not contain the selected start time")
					# 	return
					# pointing_start_index = pointing_start_index[0]

					# if len(pointing_q)-pointing_start_index < len(self.t):
					# 	print(f"WARNING: pointing file does not contain sufficient samples for the selected time period", file=sys.stderr)
					# 	print(f"\tAppending NaN to fill missing samples.", file=sys.stderr)
					# 	padding = np.empty((len(self.t)-(len(pointing_q)-pointing_start_index),4))
					# 	padding[:] = np.nan
					# 	self.pointing_q = np.vstack((pointing_q[pointing_start_index:],padding))
					# else:
					# 	self.pointing_q = pointing_q[pointing_start_index:len(self.t)+pointing_start_index]

					self.pointing_q = pointing_q

				# CONSTELLATION
				if self.c_config is not None:
					self.c_list = []
					num_c_sats = len(spacetrack.getSatIDs(self.c_config))
					if not use_temp:
						spacetrack.updateTLEs(self.c_config)
					else:
						celestrak.updateTLEs(self.c_config)
					console.send(f"Propagating constellation orbits ...")
					ii = 0
					for sat_id in progressbar(spacetrack.getSatIDs(self.c_config)):
						pc = ii/num_c_sats*100
						bar_str = int(pc)*'='
						space_str = (100-int(pc))*'  '
						console.send(f'Loading {pc:.2f}% ({ii} of {num_c_sats}) |{bar_str}{space_str}|\r')
						
						if not use_temp:		
							c_path = spacetrack.getTLEFilePath(sat_id)
							
						else:
							c_path = celestrak.getTLEFilePath(sat_id)

						self.c_list.append(orbit.Orbit.fromTLE(self.t, c_path, astrobodies=False))
						ii += 1
					console.send(f"\tLoaded {len(self.c_list)} satellites from the {self.c_config['name']} constellation.")
				
				console.send("Load Data Worker thread finished")
				self.finished.emit(self.t, self.o, self.c_list, self.pointing_q)

			except Exception as e:
				traceback.print_tb(e.__traceback__,file=sys.stderr)
				self.error.emit(f'Load Data Worker Exception: {e} '
								f''
								f'')

		
	class Controls(BaseControls):
		def __init__(self, parent_context, canvas_wrapper):
			self.context = parent_context
			super().__init__(self.context.data['name'])
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
			self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.data['name'])
			self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.data['name'])

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

def readPointingData(p_file):
	pointing_q = np.array(())
	pointing_w = np.genfromtxt(p_file, delimiter=',', usecols=(1),skip_header=1).reshape(-1,1)
	pointing_x = np.genfromtxt(p_file, delimiter=',', usecols=(2),skip_header=1).reshape(-1,1)
	pointing_y = np.genfromtxt(p_file, delimiter=',', usecols=(3),skip_header=1).reshape(-1,1)
	pointing_z = np.genfromtxt(p_file, delimiter=',', usecols=(4),skip_header=1).reshape(-1,1)
	pointing_q = np.hstack((pointing_x,pointing_y,pointing_z,pointing_w))
	pointing_dates = np.genfromtxt(p_file, delimiter=',', usecols=(0),skip_header=1, converters={0:date_parser})

	return pointing_dates, pointing_q

def date_parser(d_bytes):
	d_bytes = d_bytes[:d_bytes.index(b'.')+4]
	s = d_bytes.decode('utf-8')
	d = dt.datetime.strptime(s,"%Y-%m-%d %H:%M:%S.%f")
	d = d.replace(tzinfo=dt.timezone.utc)
	return d.replace(microsecond=0)