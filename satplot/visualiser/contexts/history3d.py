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

from PyQt5 import QtWidgets, QtCore

class History3DContext(BaseContext):
	def __init__(self, name):
		super().__init__(name)

		self.data['timespan'] = None
		self.data['orbit'] = None
		self.data['period_start'] = None
		self.data['period_end'] = None
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
		self.controls = self.Controls(self.canvas_wrapper)

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

	def _loadData(self):
		console.send('Started Data Load')
		self.data['period_start'] = self.controls.orbit_controls.period_start.datetime
		self.data['period_end'] = self.controls.orbit_controls.period_end.datetime
		self.data['prim_orbit_TLE_path'] = self.controls.orbit_controls.prim_orbit_selector.path
		self.data['constellation_index'] = self.controls.orbit_controls.getConstellationIndex()
		if self.data['constellation_index'] is not None:
			self.data['constellation_file'] = self.controls.orbit_controls.constellation_files[self.data['constellation_index']]
			self.data['constellation_name'] = self.controls.orbit_controls.constellation_options[self.data['constellation_index']]
			self.data['constellation_beam_angle'] = self.controls.orbit_controls.constellation_beam_angles[self.data['constellation_index']]
		else:
			self.data['constellation_file'] = None
			self.data['constellation_name'] = None
			self.data['constellation_beam_angle'] = None
		self.data['pointing_file'] = self.controls.orbit_controls.pointing_file_selector.path
		
		# Create worker
		console.send(f'Constellation index {self.data["constellation_index"]}')
		console.send('Creating loadDataWorker')
		self.load_worker = self.LoadDataWorker(self.data['period_start'], 
										 		self.data['period_end'], 
												self.data['prim_orbit_TLE_path'],
												c_index = self.data['constellation_index'],
												c_file = self.data['constellation_file'],
												c_name = self.data['constellation_name'],
												p_file = self.data['pointing_file'])

		self.controls.orbit_controls.submit_button.setEnabled(False)
		self.load_worker.finished.connect(self._updateDataSources)
		console.send(f'Calling super._loadData()')
		self._setUpLoadWorkerThread()
		console.send(f'Starting thread')
		self.load_worker_thread.start()

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

	def _cleanUpLoadWorkerThread(self):
		self.controls.orbit_controls.submit_button.setEnabled(True)
		return super()._cleanUpLoadWorkerThread()

	class LoadDataWorker(BaseDataWorker):
		finished = QtCore.pyqtSignal(timespan.TimeSpan, orbit.Orbit, list, np.ndarray)
		error = QtCore.pyqtSignal()

		def __init__(self, period_start, period_end, prim_orbit_TLE_path,
			   		 c_index = None, c_file=None, c_name=None, p_file=None, *args, **kwargs):
			super().__init__(*args, **kwargs)
			self.period_start = period_start
			self.period_end = period_end
			self.prim_orbit_TLE_path = prim_orbit_TLE_path
			self.t = None
			self.o = None
			self.c_index = c_index
			self.c_file = c_file
			self.c_name = c_name
			self.c_list = []
			self.p_file = p_file

		def run(self):
			console.send("Started Load Data Worker thread")
			self.period_start.replace(microsecond=0)
			self. period_end.replace(microsecond=0)			
			# TODO: calculate time period from end
			# TODO: auto calculate step size
			time_period = int((self.period_end - self.period_start).total_seconds())
			timestep=30
			console.send(f"Creating Timespan from {self.period_start} -> {self.period_end} ...")
			self.t = timespan.TimeSpan(self.period_start,
								timestep=f'{timestep}S',
								timeperiod='90M')
			# self.t = timespan.TimeSpan(self.period_start,
			# 					timestep=f'{timestep}S',
			# 					timeperiod=f'{time_period}S')
			console.send(f"\tDuration: {self.t.time_period}")
			console.send(f"\tNumber of steps: {len(self.t)}")
			console.send(f"\tLength of timestep: {self.t.time_step}")


			console.send(f"Propagating orbit from {self.prim_orbit_TLE_path.split('/')[-1]} ...")
			self.o = orbit.Orbit.fromTLE(self.t, self.prim_orbit_TLE_path)
			console.send(f"\tNumber of steps in single orbit: {self.o.period_steps}")
			
			self.pointing_q = np.array(())
			if self.p_file is not None and self.p_file != '':
				console.send(f"Loading pointing from {self.p_file.split('/')[-1]}")
				pointing_w = np.genfromtxt(self.p_file, delimiter=',', usecols=(1),skip_header=1).reshape(-1,1)
				pointing_x = np.genfromtxt(self.p_file, delimiter=',', usecols=(2),skip_header=1).reshape(-1,1)
				pointing_y = np.genfromtxt(self.p_file, delimiter=',', usecols=(3),skip_header=1).reshape(-1,1)
				pointing_z = np.genfromtxt(self.p_file, delimiter=',', usecols=(4),skip_header=1).reshape(-1,1)
				pointing_q = np.hstack((pointing_x,pointing_y,pointing_z,pointing_w))
				pointing_dates = np.genfromtxt(self.p_file, delimiter=',', usecols=(0),skip_header=1, converters={0:self.date_parser})

				total_secs = lambda x: x.total_seconds()
				total_secs = np.vectorize(total_secs)
				sample_periods = total_secs(np.diff(pointing_dates))
				different_sample_periods = np.where(sample_periods != sample_periods[0])[0]
				if len(different_sample_periods) != 0:
					print(f"WARNING: pointing samples are not taken at regular intervals - {pointing_dates[different_sample_periods]}", file=sys.stderr)

				if sample_periods[0] != timestep:
					print(f"ERROR: pointing file sampling period do not match the selected visualiser sampling period", file=sys.stderr)
					self.error.emit()
					return
				
				pointing_start_index = np.where(pointing_dates==self.period_start)[0]
				if len(pointing_start_index) == 0:
					print(f"ERROR: pointing file does not contain the selected start time", file=sys.stderr)
					self.error.emit()
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

		def date_parser(self, d_bytes):
			s = d_bytes.decode('utf-8')
			d = dt.datetime.strptime(s,"%Y-%m-%d %H:%M:%S.%f")
			return d.replace(microsecond=0)
		
	class Controls(BaseControls):
		def __init__(self, canvas_wrapper):
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