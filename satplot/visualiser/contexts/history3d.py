import satplot
import satplot.model.timespan as timespan
import satplot.model.orbit as orbit
from satplot.visualiser import canvaswrappers
from satplot.visualiser.contexts.base import (BaseContext, BaseDataWorker, BaseControls)
import satplot.visualiser.controls.console as console
from satplot.visualiser.controls import controls, widgets

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
		self.data['prim_orbit_TLE_path'] = self.controls.orbit_controls.prim_orbit_selector.path
		if self.controls.orbit_controls.suppl_constellation_selector.isEnabled():
			self.data['constellation_index'] = self.controls.orbit_controls.getConstellationIndex()			
			self.data['constellation_file'] = self.controls.orbit_controls.constellation_files[self.data['constellation_index']]
			self.data['constellation_name'] = self.controls.orbit_controls.constellation_options[self.data['constellation_index']]
			self.data['constellation_beam_angle'] = self.controls.orbit_controls.constellation_beam_angles[self.data['constellation_index']]
		else:
			self.data['constellation_index'] = None
			self.data['constellation_file'] = None
			self.data['constellation_name'] = None
			self.data['constellation_beam_angle'] = None

		if self.controls.orbit_controls.pointing_file_controls.isEnabled():
			self.data['pointing_file'] = self.controls.orbit_controls.pointing_file_controls._pointing_file_selector.path
			self.data['pointing_invert_transform'] = self.controls.orbit_controls.pointing_file_controls.pointing_file_inv_toggle.isChecked()
			if self.controls.orbit_controls.pointing_file_controls.pointingFileDefinesPeriod():
				pointing_dates,q = readPointingData(self.data['pointing_file'])
				self.data['period_start'] = pointing_dates[0]
				self.data['period_end'] = pointing_dates[-1]
				self.data['sampling_period'] = (pointing_dates[1]-pointing_dates[0]).total_seconds()
		else:
			self.data['pointing_file'] = None
			self.data['pointing_invert_transform'] = None
		
		# Create worker
		console.send(f'Constellation index {self.data["constellation_index"]}')
		console.send('Creating loadDataWorker')
		self.load_worker = self.LoadDataWorker(self.data['period_start'], 
										 		self.data['period_end'],
												self.data['sampling_period'],
												self.data['prim_orbit_TLE_path'],
												c_index = self.data['constellation_index'],
												c_file = self.data['constellation_file'],
												c_name = self.data['constellation_name'],
												p_file = self.data['pointing_file'])

		try:
			self.controls.orbit_controls.submit_button.setEnabled(False)
			self.load_worker.finished.connect(self._updateDataSources)
			self.load_worker.finished.connect(self._updateControls)
			self.load_worker.error.connect(self._cleanUpLoadWorkerThread)
			console.send(f'Calling super._loadData()')
			self._setUpLoadWorkerThread()
			console.send(f'Starting thread')
			self.load_worker_thread.start()
		except Exception as e:
			self.controls.orbit_controls.submit_button.setEnabled(True)
			raise e

	def _updateControls(self, *args, **kwargs):
		self.controls.orbit_controls.period_start.setDatetime(self.data['period_start'])
		self.controls.orbit_controls.period_end.setDatetime(self.data['period_end'])

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
		
		if self.data['constellation_index'] is not None:
			self.data['constellation_list'] = c_list
		else:
			self.data['constellation_list'] = None

		console.send(f'Constellation index: {self.data["constellation_index"]}')
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

	def _cleanUpLoadWorkerThread(self, err_str=None):
		print(err_str, file=sys.stderr)
		self.controls.orbit_controls.submit_button.setEnabled(True)
		return super()._cleanUpLoadWorkerThread()

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

		def __init__(self, period_start, period_end, sampling_period, prim_orbit_TLE_path,
			   		 c_index = None, c_file=None, c_name=None, p_file=None, *args, **kwargs):
			super().__init__(*args, **kwargs)
			self.period_start = period_start
			self.period_end = period_end
			self.timestep = sampling_period
			self.prim_orbit_TLE_path = prim_orbit_TLE_path
			self.t = None
			self.o = None
			self.c_index = c_index
			self.c_file = c_file
			self.c_name = c_name
			self.c_list = []
			self.p_file = p_file
			self.pointing_q = None

		def run(self):
			try:
				console.send("Started Load Data Worker thread")
				self.period_start.replace(microsecond=0)
				self. period_end.replace(microsecond=0)			
				time_period = int((self.period_end - self.period_start).total_seconds())
				console.send(f"Creating Timespan from {self.period_start} -> {self.period_end} ...")
				self.t = timespan.TimeSpan(self.period_start,
									timestep=f'{self.timestep}S',
									timeperiod=f'{time_period}S')
				console.send(f"\tDuration: {self.t.time_period}")
				console.send(f"\tNumber of steps: {len(self.t)}")
				console.send(f"\tLength of timestep: {self.t.time_step}")


				console.send(f"Propagating orbit from {self.prim_orbit_TLE_path.split('/')[-1]} ...")
				self.o = orbit.Orbit.fromTLE(self.t, self.prim_orbit_TLE_path)
				console.send(f"\tNumber of steps in single orbit: {self.o.period_steps}")
				
				self.pointing_q = np.array(())
				if self.p_file is not None and self.p_file != '':
					console.send(f"Loading pointing from {self.p_file.split('/')[-1]}")
					pointing_dates, pointing_q = readPointingData(self.p_file)

					total_secs = lambda x: x.total_seconds()
					total_secs = np.vectorize(total_secs)
					sample_periods = total_secs(np.diff(pointing_dates))
					different_sample_periods = np.where(sample_periods != sample_periods[0])[0]
					if len(different_sample_periods) != 0:
						print(f"WARNING: pointing samples are not taken at regular intervals - {pointing_dates[different_sample_periods]}", file=sys.stderr)

					if sample_periods[0] != self.timestep:
						print(f"ERROR: pointing file sampling periods do not match the selected visualiser sampling period", file=sys.stderr)
						self.error.emit("ERROR: pointing file sampling period do not match the selected visualiser sampling period")
						return
					
					pointing_start_index = np.where(pointing_dates==self.period_start)[0]
					if len(pointing_start_index) == 0:
						print(f"ERROR: pointing file does not contain the selected start time {self.period_start}", file=sys.stderr)
						self.error.emit("ERROR: pointing file does not contain the selected start time")
						return
					pointing_start_index = pointing_start_index[0]


					if len(pointing_q)-pointing_start_index < len(self.t):
						print(f"WARNING: pointing file does not contain sufficient samples for the selected time period", file=sys.stderr)
						print(f"\tAppending NaN to fill missing samples.", file=sys.stderr)
						padding = np.empty((len(self.t)-(len(pointing_q)-pointing_start_index),4))
						padding[:] = np.nan
						self.pointing_q = np.vstack((pointing_q[pointing_start_index:],padding))
					else:
						self.pointing_q = pointing_q[pointing_start_index:len(self.t)+pointing_start_index]

				if self.c_index is not None:
					console.send(f"Propagating constellation orbits from {self.c_file.split('/')[-1]} ...")
					self.c_list = orbit.Orbit.multiFromTLE(self.t, self.c_file, console.consolefp)
					console.send(f"\tLoaded {len(self.c_list)} satellites from the {self.c_name} constellation.")
				
				console.send("Load Data Worker thread finished")
				self.finished.emit(self.t, self.o, self.c_list, self.pointing_q)
			except Exception as e:
				self.error.emit(str(e))
				
				


		
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
	print(d)
	return d.replace(microsecond=0)