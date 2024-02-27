from vispy import app, use
from satplot.visualiser import canvaswrapper
from satplot.visualiser import window

from PyQt5 import QtWidgets, QtCore

import numpy as np
import satplot.model.timespan as timespan
import satplot.model.orbit as orbit
import sys
import satplot.visualiser.controls.console as console

import warnings
warnings.filterwarnings("ignore", message="Optimal rotation is not uniquely or poorly defined for the given sets of vectors.")

use(gl='gl+')

class Application():
	def __init__(self) -> None:
		self.pyqt_app = app.use_app("pyqt5")
		self.pyqt_app.create()
		self.canvas_wrapper = canvaswrapper.CanvasWrapper()		
		self.window = window.MainWindow(self.canvas_wrapper, "Sat Plot")
		self._connectControls()
		self.load_data_worker = None
		self.worker_thread = None

	def run(self):
		self.window.show()
		self.pyqt_app.run()

	def _connectControls(self):
		self.window.orbit_controls.submit_button.clicked.connect(self._loadData)
		self.window._time_slider.add_connect(self._updateIndex)

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
		# Create worker
		print(f"worker thread: {self.worker_thread}")
		self.worker_thread = QtCore.QThread()
		print(f"worker thread: {self.worker_thread}")
		self.load_data_worker = self.LoadDataWorker(self.period_start, 
										 		self.period_end, 
												self.prim_orbit_TLE_path,
												c_index = self.c_index,
												c_file = self.c_file,
												c_name = self.c_name,
												file=sys.stdout)		
		# Move to new thread and setup signals
		self.load_data_worker.moveToThread(self.worker_thread)
		self.worker_thread.started.connect(self.load_data_worker.run)
		self.worker_thread.finished.connect(self.worker_thread.deleteLater)
		self.load_data_worker.finished.connect(self._cleanUpWorkerThread)
		self.load_data_worker.finished.connect(self._updateDataSources)
		self.load_data_worker.finished.connect(self.load_data_worker.deleteLater)
		
		# make load data button inactive
		self.window.orbit_controls.submit_button.setEnabled(False)
		self.worker_thread.start()	

	# attach to worker thread done
	def _updateDataSources(self, t, o, c_list):
		self.t = t
		self.o = o
		self.c_list = c_list
		self.window._time_slider.setRange(self.t.start, self.t.end, len(self.t))
		self.window._time_slider._curr_dt_picker.setDatetime(self.t.start)
		
		self.canvas_wrapper.setOrbitSource(self.o)
		self.canvas_wrapper.setSunSource(self.o)
		self.canvas_wrapper.setMoonSource(self.o)
		self.canvas_wrapper.setEarthSource()
		if self.c_index is not None:
			self.canvas_wrapper.setConstellationSource(self.c_list, self.c_beam_angle)
		self.canvas_wrapper.setMakeNewVisualsFlag()
		console.send(f"Drawing Assets...")
		curr_index = self.window._time_slider.slider.value()
		self._updateIndex(curr_index)
		self.window.orbit_controls.submit_button.setEnabled(True)

	def _updateIndex(self, index):
		self.canvas_wrapper.updateIndex(index, self.t.asSkyfield(index))

	def _cleanUpWorkerThread(self):
		self.worker_thread.quit()
		self.worker_thread.deleteLater()
		self.worker_thread = None

	class LoadDataWorker(QtCore.QObject):
		finished = QtCore.pyqtSignal(timespan.TimeSpan, orbit.Orbit, list)

		def __init__(self, period_start, period_end, prim_orbit_TLE_path,
			   		 c_index = None, c_file=None, c_name=None, file=None, *args, **kwargs):
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
			self.file = file

		def run(self):
			console.send("Started Load Data Worker thread")
			self.period_start.replace(microsecond=0)
			self. period_end.replace(microsecond=0)			
			# TODO: calculate time period from end
			# TODO: auto calculate step size
			time_period = int((self.period_end - self.period_start).total_seconds())
			sample_period = time_period/300
			console.send(f"Creating Timespan from {self.period_start} -> {self.period_end} ...")
			self.t = timespan.TimeSpan(self.period_start,
								timestep='30S',
								timeperiod='90M')
			# self.t = timespan.TimeSpan(self.period_start,
			# 					timestep=f'{sample_period}S',
			# 					timeperiod=f'{time_period}S')
			console.send(f"\tDuration: {self.t.time_period}")
			console.send(f"\tNumber of steps: {len(self.t)}")
			console.send(f"\tLength of timestep: {self.t.time_step}")


			console.send(f"Propagating orbit from {self.prim_orbit_TLE_path.split('/')[-1]} ...")
			self.o = orbit.Orbit.fromTLE(self.t, self.prim_orbit_TLE_path)
			console.send(f"\tNumber of steps in single orbit: {self.o.period_steps}")
			
			if self.c_index is not None:
				console.send(f"Propagating constellation orbits from {self.c_file.split('/')[-1]} ...")
				self.c_list = orbit.Orbit.multiFromTLE(self.t, self.c_file, console.consolefp)
				console.send(f"\tLoaded {len(self.c_list)} satellites from the {self.c_name} constellation.")
			
			console.send("Load Data Worker thread finished")
			self.finished.emit(self.t, self.o, self.c_list)

		def stop(self):
			self._is


if __name__ == '__main__':
	application = Application()
	# application.canvas_wrapper.canvas.measure_fps()
	application.run()



