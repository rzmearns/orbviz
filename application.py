from vispy import app
from satplot.visualiser import canvaswrapper
from satplot.visualiser import window

import numpy as np
import satplot.model.timespan as timespan
import satplot.model.orbit as orbit

import satplot.visualiser.controls.console as console

t = None
o = None

class Application():
	def __init__(self) -> None:
		self.pyqt_app = app.use_app("pyqt5")
		self.pyqt_app.create()
		self.canvas_wrapper = canvaswrapper.CanvasWrapper()		
		self.window = window.MainWindow(self.canvas_wrapper, "Sat Plot")
		self._connectControls()

	def run(self):
		self.window.show()
		self.pyqt_app.run()

	def _connectControls(self):
		self.window.orbit_controls.submit_button.clicked.connect(self._loadData)
		self.window._time_slider.add_connect(self._updateIndex)

	def _loadData(self):
		global t
		global o
		period_start = self.window.orbit_controls.period_start.datetime
		period_start.replace(microsecond=0)
		period_end = self.window.orbit_controls.period_end.datetime
		period_end.replace(microsecond=0)
		prim_orbit_TLE_path = self.window.orbit_controls.prim_orbit_selector.path
		# TODO: calculate time period from end
		# TODO: auto calculate step size
		console.send(f"Creating Timespan from {period_start} -> {period_end} ...")
		t = timespan.TimeSpan(self.window.orbit_controls.period_start.datetime,
							timestep='30S',
							timeperiod='90M')
		console.send(f"\tDuration: {t.time_period}")
		console.send(f"\tNumber Steps: {len(t)}")
		console.send(f"\tLength of timestep: {t.time_step}")

		self.window._time_slider.setRange(t.start, t.end, len(t))
		self.window._time_slider._curr_dt_picker.setDatetime(t.start)

		# TODO: Update text in time slider
		console.send(f"Propagating orbit from {prim_orbit_TLE_path.split('/')[-1]} ...")
		o = orbit.Orbit.fromTLE(t, prim_orbit_TLE_path)
		console.send(f"\tNumber of steps in single orbit: {o.period_steps}")
		self.canvas_wrapper.setOrbitSource(o)
		self.canvas_wrapper.setSunSource(o)
		self.canvas_wrapper.setMoonSource(o)

		constellation_index = self.window.orbit_controls.getConstellationIndex()
		if  constellation_index is not None:
			constellation_file = self.window.orbit_controls.constellation_files[constellation_index]
			console.send(f"Propagating constellation orbits from {constellation_file.split('/')[-1]} ...")
			constellation_o = orbit.Orbit.multiFromTLE(t, constellation_file)
			console.send(f"Loaded {len(constellation_o)} satellites from the {self.window.orbit_controls.constellation_options[constellation_index]} constellation.")
			self.canvas_wrapper.setConstellationSource(constellation_o)

		console.send(f"Drawing Orbit...")
		curr_index = self.window._time_slider.slider.value()
		self._updateIndex(curr_index)
		
	def _updateIndex(self, index):
		self.canvas_wrapper.updateIndex(index, t.asSkyfield(index))

if __name__ == '__main__':
	application = Application()
	# application.canvas_wrapper.canvas.measure_fps()
	application.run()



