from vispy import scene

from satplot.util import constants as c
from satplot.visualiser.assets.earth import Earth
from satplot.visualiser.assets.orbit import OrbitVisualiser
from satplot.visualiser.assets.sun import Sun
from satplot.visualiser.assets.moon import Moon
from satplot.visualiser.assets.spacecraft import SpacecraftVisualiser
from satplot.visualiser.assets.constellation import Constellation
from satplot.visualiser.assets.gizmo import ViewBoxGizmo

from satplot.visualiser.controls import console

canvas = scene.SceneCanvas()

class CanvasWrapper():
	def __init__(self, w=800, h=600, keys='interactive', bgcolor='white'):
		self.canvas = scene.SceneCanvas(size=(w,h),
								  		keys=keys,
										bgcolor=bgcolor,
										show=True)
		self.grid = self.canvas.central_widget.add_grid()
		self.view_box = self.canvas.central_widget.add_view()
		self.view_box.camera = scene.cameras.TurntableCamera(parent=self.view_box.scene,
													   		fov=60,
															name='Turntable')
		self.is_asset_instantiated = {}
		self.assets = {}
		self.initAssetInstantiatedFlags()
		self.buildScene()
		self.canvas.events.mouse_move.connect(self.onMouseMove)

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

	def setEarthSource(self):
		self.is_asset_instantiated['earth'] = True

	def setOrbitSource(self, orbit):
		self.assets['primary_orbit'].setSource(orbit)
		self.is_asset_instantiated['primary_orbit'] = True
		self.assets['spacecraft'].setSource(orbit)
		self.is_asset_instantiated['spacecraft'] = True


	def setSunSource(self, orbit):
		self.assets['sun'].setSource(orbit)
		self.is_asset_instantiated['sun'] = True

	def setMoonSource(self, orbit):
		self.assets['moon'].setSource(orbit)
		self.is_asset_instantiated['moon'] = True
	
	def setConstellationSource(self, orbits, beam_angle):
		self.assets['constellation'].setSource(orbits, beam_angle)
		self.is_asset_instantiated['constellation'] = True

	def initAssetInstantiatedFlags(self):
		self.is_asset_instantiated['primary_orbit'] = False
		self.is_asset_instantiated['sun'] = False
		self.is_asset_instantiated['moon'] = False
		self.is_asset_instantiated['constellation'] = False
		self.is_asset_instantiated['earth'] = False
		self.is_asset_instantiated['spacecraft'] = False
		self.is_asset_instantiated['ECI_gizmo'] = False

	def updateIndex(self, index, datetime):
		if self.is_asset_instantiated['primary_orbit']:
			self.assets['primary_orbit'].updateIndex(index)
		if self.is_asset_instantiated['earth']:
			self.assets['earth'].setCurrentECEFRotation(datetime)
		if self.is_asset_instantiated['moon']:
			self.assets['moon'].updateIndex(index)
		if self.is_asset_instantiated['constellation']:
			self.assets['constellation'].updateIndex(index)
		if self.is_asset_instantiated['spacecraft']:
			self.assets['spacecraft'].updateIndex(index)


		# Sun must be last so that umbra doesn't occlude objects
		if self.is_asset_instantiated['sun']:
			self.assets['sun'].updateIndex(index)

	def setMakeNewVisualsFlag(self):
		self.assets['constellation'].setFirstDraw()
		self.assets['sun'].setFirstDraw()

	def buildScene(self):
		
		self.assets['earth'] = Earth(canvas=self.canvas,
											parent=self.view_box.scene)
	
		self.assets['primary_orbit'] = OrbitVisualiser(canvas=self.canvas,
											parent=self.view_box.scene)
	
		self.assets['moon'] = Moon(canvas=self.canvas,
											parent=self.view_box.scene)
	
		self.assets['constellation'] = Constellation(canvas=self.canvas,
											parent=self.view_box.scene)	
	
		self.assets['spacecraft'] = SpacecraftVisualiser(canvas=self.canvas,
											parent=self.view_box.scene)

		self.assets['sun'] = Sun(canvas=self.canvas,
											parent=self.view_box.scene)


		# if self.is_asset_instantiated['ECI_gizmo']:
		# self.assets['ECI_gizmo'] = ViewBoxGizmo(canvas=self.canvas,
		# 				   					parent=self.view_box.scene,
		# 									translate=(c.R_EARTH,c.R_EARTH),
		# 									scale=(2*c.R_EARTH,2*c.R_EARTH,2*c.R_EARTH,1))
		self.setCameraZoom(5*c.R_EARTH)
		# self.assets['ECI_gizmo'].attachCamera(self.view_box.camera)

	@canvas.events.mouse_move.connect
	def onMouseMove(self, event):
		pass
		# console.send("captured event")
		# self.assets['ECI_gizmo'].onMouseMove(event)