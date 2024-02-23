from vispy import scene
from vispy import app

from satplot.visualiser import canvaswrapper
from satplot.visualiser import window
from satplot.util import constants as c

from satplot.visualiser.assets.earth import Earth

import numpy as np

class Application():
	def __init__(self) -> None:
		self.pyqt_app = app.use_app("pyqt5")
		self.pyqt_app.create()
		self.canvas_wrapper = canvaswrapper.CanvasWrapper()
		self.buildScene()		
		self.window = window.MainWindow(self.canvas_wrapper, "Sat Plot")

	def buildScene(self):
		self.canvas_wrapper.assets['earth'] = Earth(canvas=self.canvas_wrapper.canvas,
									  		parent=self.canvas_wrapper.view_box.scene)
		self.canvas_wrapper.setCameraZoom(5*c.R_EARTH)

	def run(self):
		self.window.show()
		self.pyqt_app.run()

if __name__ == '__main__':
	application = Application()
	application.canvas_wrapper.canvas.measure_fps()
	application.run()
