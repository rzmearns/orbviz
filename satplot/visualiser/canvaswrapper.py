from vispy import scene

from satplot.util import constants as c
from satplot.visualiser.assets.earth import Earth


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


	def buildScene(self):
		self.assets['earth'] = Earth(canvas=self.canvas,
									  		parent=self.view_box.scene)
		self.setCameraZoom(5*c.R_EARTH)

