import numpy as np
import numpy.typing as nptyping
import time

from vispy import scene, color
from vispy.scene.widgets.viewbox import ViewBox
from vispy.visuals import transforms as vTransforms
from vispy.visuals.filters import FacePickingFilter


import satplot.model.geometry.polygons as polygons
import satplot.model.geometry.primgeom as pg
import satplot.model.geometry.transformations as transforms
import satplot.util.constants as c
import satplot.util.paths as satplot_paths
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.assets.axis_indicator as axisInd
import satplot.visualiser.colours as colours
import spherapy.timespan as timespan

throttle = time.monotonic()

class Sky3DAsset(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		# These callbacks need to be set after asset creation as the option dict is populated during draw()

		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Sky'

	def setSource(self, *args, **kwargs) -> None:
		pass

	def _instantiateAssets(self) -> None:
		pass

	def _createVisuals(self) -> None:
		# Earth Sphere
		self.visuals['sky_sphere'] = scene.visuals.Sphere(radius=1e4,
															method='latitude',
															parent=None,
							   								edge_color='red',
							   								color='black')
		self.face_picking_filter = FacePickingFilter()
		self.visuals['sky_sphere'].mesh.attach(self.face_picking_filter)
		self.num_faces = self.visuals['sky_sphere'].mesh._meshdata.n_faces

	# Use AbstractAsset.updateIndex()

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()
		if self.isStale():
			self._recomputeRedrawChildren(rotation=None)
			self._clearStaleFlag()


	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self.opts = self._dflt_opts.copy()



	def on_mouse_move(self, event, canvas):
		print(f'Inside sky on_mouse_move')

		# adjust the event position for hidpi screens
		render_size = tuple(d * canvas.pixel_scale for d in canvas.size)
		x_pos = event.pos[0] * canvas.pixel_scale
		y_pos = render_size[1] - (event.pos[1] * canvas.pixel_scale)

		# render a small patch around the mouse cursor
		restore_state = not self.face_picking_filter.enabled
		self.face_picking_filter.enabled = True
		self.visuals['sky_sphere'].mesh.update_gl_state(blend=False)
		picking_render = canvas.render(
			region=(x_pos - 1, y_pos - 1, 3, 3),
			size=(3, 3),
			bgcolor=(0, 0, 0, 0),
			alpha=True,
		)
		if restore_state:
			self.face_picking_filter.enabled = False
		self.visuals['sky_sphere'].mesh.update_gl_state(blend=not self.face_picking_filter.enabled)

		# unpack the face index from the color in the center pixel
		face_idx = (picking_render.view(np.uint32) - 1)[1, 1, 0]
		print(f'\tA:{face_idx=}')
		if face_idx > 0 and face_idx < self.num_faces:
			# this m ay be less safe, but it's faster than set_data
			print(f'\tB:{face_idx=}')
			# sphere2.mesh.mesh_data._face_colors_indexed_by_faces[face_idx] = (0, 1, 0, 1)
			# if face_idx == crit_face_idx:
			#     print(f'{getFaceCentroid(face_idx,sphere2.mesh._meshdata)=}')
			r,theta,phi = getRaDecECI(getFaceCentroid(face_idx,self.visuals['sky_sphere'].mesh._meshdata))
			print(f'{r,theta,phi}')
			self.visuals['sky_sphere'].mesh.mesh_data_changed()


	#----- OPTIONS CALLBACKS -----#

	#----- HELPER FUNCTIONS -----#
def getFaceCentroid(face_idx, meshdata):
	face_vertices_idx = meshdata.get_faces()[face_idx,:]
	face_vertices = meshdata.get_vertices()[face_vertices_idx,:]
	centroid = getCentroid(*face_vertices)
	return centroid

def getCentroid(p1,p2,p3):
	d = ((p2[0]+p3[0])/2,
		 (p2[1]+p3[1])/2,
		 (p2[2]+p3[2])/2)
	c = ((p1[0]+2*d[0])/3,
		 (p1[1]+2*d[1])/3,
		 (p1[2]+2*d[2])/3)
	return c

def getRaDecECI(p):
	r = np.linalg.norm(p)
	theta = np.arctan2(p[1],p[0])
	phi = np.pi/2 - np.arccos(p[2]/r)

	return (r,np.rad2deg(theta),np.rad2deg(phi))