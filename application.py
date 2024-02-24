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
		self.canvas_wrapper.buildScene()		
		self.window = window.MainWindow(self.canvas_wrapper, "Sat Plot")
		self.window.orbit_controls.submit_button.clicked.connect(self.loadData)

	def run(self):
		self.window.show()
		self.pyqt_app.run()

	def loadData(self):
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

		# TODO: Update text in time slider
		console.send(f"Propagating orbit from {prim_orbit_TLE_path.split('/')[-1]} ...")
		o = orbit.Orbit.fromTLE(t, prim_orbit_TLE_path)
		# TODO: Set source for orbit visualiser

		console.send(f"\tNumber of steps in single orbit: {o.period_steps}")

if __name__ == '__main__':
	application = Application()
	# application.canvas_wrapper.canvas.measure_fps()
	application.run()



