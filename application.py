from vispy import app, use
from satplot.visualiser import canvaswrappers
from satplot.visualiser import window

from PyQt5 import QtWidgets, QtCore

import numpy as np
import satplot.model.timespan as timespan
import satplot.model.orbit as orbit
import sys
import argparse
import datetime as dt
import satplot.visualiser.controls.console as console
import satplot

import json

import warnings
warnings.filterwarnings("ignore", message="Optimal rotation is not uniquely or poorly defined for the given sets of vectors.")

use(gl='gl+')

class Application():
	def __init__(self) -> None:
		self.pyqt_app = app.use_app("pyqt5")
		self.pyqt_app.create()

		self._buildActionDict()

		self.canvas_wrapper = canvaswrappers.History3D()		
		self.window = window.MainWindow(self.canvas_wrapper, title="Sat Plot", action_dict=self.action_dict)

		self._connectControls()
		self.load_data_worker = None
		self.load_worker_thread = None
		self.save_worker = None
		self.save_worker_thread = None

	def run(self):
		self.window.show()
		self.pyqt_app.run()

	def _connectControls(self):
		self.window.history3D.orbit_controls.submit_button.clicked.connect(self._loadData)
		self.window.history3D._time_slider.add_connect(self._updateIndex)

		self.action_dict['save']['callback'] = self._saveState
		self.action_dict['load']['callback'] = self._loadState
		self.action_dict['center-earth']['callback'] = self.canvas_wrapper.centerCameraEarth
		self.action_dict['center-spacecraft']['callback'] = self.canvas_wrapper.centerCameraSpacecraft
		for toolbar in self.window.toolbars.values():
			toolbar.addButtons()
		for menubar in self.window.menubars.values():
			menubar.addMenuItems()

	def _saveState(self):
		console.send(f'Saving State')

	def _loadState(self):
		console.send(f"loading state")

	def _loadData(self):
		self.period_start = self.window.orbit_controls.period_start.datetime
		self.period_end = self.window.orbit_controls.period_end.datetime
		self.prim_orbit_TLE_path = self.window.orbit_controls.prim_orbit_selector.path
		self.c_index = self.window.orbit_controls.getConstellationIndex()
		if self.c_index is not None:
			self.c_file = self.window.orbit_controls.constellation_files[self.c_index]
			self.c_name = self.window.orbit_controls.constellation_options[self.c_index]
			self.c_beam_angle = self.window.orbit_controls.constellation_beam_angles[self.c_index]
		else:
			self.c_file = None
			self.c_name = None
			self.c_beam_angle = None
		self.pointing_file = self.window.orbit_controls.pointing_file_selector.path
		
		# Create worker
		self.load_worker_thread = QtCore.QThread()
		self.load_data_worker = self.LoadDataWorker(self.period_start, 
										 		self.period_end, 
												self.prim_orbit_TLE_path,
												c_index = self.c_index,
												c_file = self.c_file,
												c_name = self.c_name,
												p_file = self.pointing_file)	
		# Move to new thread and setup signals
		self.load_data_worker.moveToThread(self.load_worker_thread)
		self.load_worker_thread.started.connect(self.load_data_worker.run)
		self.load_worker_thread.finished.connect(self.load_worker_thread.deleteLater)
		self.load_data_worker.finished.connect(self._cleanUpLoadWorkerThread)
		self.load_data_worker.finished.connect(self._updateDataSources)
		self.load_data_worker.finished.connect(self.load_data_worker.deleteLater)
		self.load_data_worker.error.connect(self._cleanUpLoadWorkerThread)
		self.load_data_worker.error.connect(self.load_data_worker.deleteLater)


		# make load data button inactive
		self.window.orbit_controls.submit_button.setEnabled(False)
		self.load_worker_thread.start()	

	# attach to worker thread done
	def _updateDataSources(self, t, o, c_list, pointing_q):
		self.t = t
		self.o = o
		self.c_list = c_list
		self.window._time_slider.setRange(self.t.start, self.t.end, len(self.t))
		self.window._time_slider._curr_dt_picker.setDatetime(self.t.start)
		
		if len(pointing_q) > 0:
			pointing=pointing_q
		else:
			pointing = None
		
		if self.c_index is not None:
			c_list = self.c_list
			c_beam_angle = self.c_beam_angle
		else:
			c_list = None
			c_beam_angle = None
		
		self.canvas_wrapper.setSource(self.t,
										self.o,
										pointing,
										c_list,
										c_beam_angle)
		self.canvas_wrapper.setFirstDrawFlags()
		console.send(f"Drawing Assets...")
		curr_index = self.window._time_slider.slider.value()
		self._updateIndex(curr_index)

	def _updateIndex(self, index):
		self.canvas_wrapper.updateIndex(index)

	def _cleanUpLoadWorkerThread(self):
		self.load_worker_thread.quit()
		self.load_worker_thread.deleteLater()
		self.load_worker_thread = None
		self.window.orbit_controls.submit_button.setEnabled(True)

	def _cleanUpSaveWorkerThread(self):
		self.save_worker_thread.quit()
		self.save_worker_thread.deleteLater()
		self.save_worker_thread = None

	def _buildActionDict(self):
		with open('resources/actions/main-window.json','r') as fp:
			self.action_dict = json.load(fp)

	class LoadDataWorker(QtCore.QObject):
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

if __name__ == '__main__':

	parser = argparse.ArgumentParser(
						prog='SatPlot',
						description='Visualisation software for satellites; including orbits and pointing.')
	parser.add_argument('--nogl+', action='store_true', dest='nogl_plus')
	parser.add_argument('--debug', action='store_true', dest='debug')
	args = parser.parse_args()
	if args.nogl_plus:
		satplot.gl_plus = False
	else:
		satplot.gl_plus = True
	if args.debug:
		satplot.debug = True
	else:
		satplot.debug = False
	application = Application()
	application.run()



