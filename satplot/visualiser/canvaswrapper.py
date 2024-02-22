from vispy import scene

class CanvasWrapper():
	def __init__(self, w=800, h=600, keys='interactive', bgcolor='white'):
		# self.canvas = Canvas(size=(w,h),
		# 						  		keys=keys,
		# 								bgcolor=bgcolor,
		# 								show=True)
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