from vispy import scene

from satplot.util import constants as c
from satplot.visualiser.assets.earth import Earth
from satplot.visualiser.assets.orbit import OrbitVisualiser
from satplot.visualiser.assets.sun import Sun
from satplot.visualiser.assets.moon import Moon

class CanvasWrapper():
	def __init__(self, w=800, h=600, keys='interactive', bgcolor='white'):
		self.canvas = scene.SceneCanvas(size=(w,h),
								  		keys=keys,
										bgcolor=bgcolor,
										show=True)
		self.grid = self.canvas.central_widget.add_grid()
		self.view_box = self.canvas.central_widget.add_view()
		self.view_box.camera = 'turntable'
		self.assets = {}

	def setCameraMode(self, mode='turntable'):
		allowed_cam_modes = ['turntable',
					   		'arcball',
							'fly',
							'panzoom',
							'magnify',
							'perspective']
		if mode not in allowed_cam_modes:
			raise NameError
		
		self.view_box.camera = mode

	def setCameraZoom(self, zoom):
		self.view_box.camera.scale_factor = zoom

	def setOrbitSource(self, orbit):
		self.assets['primary_orbit'].setSource(orbit)

	def setSunSource(self, orbit):
		self.assets['sun'].setSource(orbit)

	def setMoonSource(self, orbit):
		self.assets['moon'].setSource(orbit)

	def updateIndex(self, index, datetime):
		self.assets['primary_orbit'].updateIndex(index)
		self.assets['earth'].setCurrentECEFRotation(datetime)
		self.assets['sun'].updateIndex(index)
		self.assets['moon'].updateIndex(index)

	def buildScene(self):
		self.assets['earth'] = Earth(canvas=self.canvas,
									  		parent=self.view_box.scene)
		self.assets['primary_orbit'] = OrbitVisualiser(canvas=self.canvas,
									  		parent=self.view_box.scene)
		self.assets['sun'] = Sun(canvas=self.canvas,
						   					parent=self.view_box.scene)
		self.assets['moon'] = Moon(canvas=self.canvas,
						   					parent=self.view_box.scene)		
		self.setCameraZoom(5*c.R_EARTH)