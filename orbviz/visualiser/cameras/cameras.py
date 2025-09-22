

import numpy as np

from vispy.scene.cameras.arcball import ArcballCamera
from vispy.scene.cameras.perspective import Base3DRotationCamera
from vispy.util import transforms
from vispy.util.quaternion import Quaternion


class FixedCamera(Base3DRotationCamera):
	"""3D camera class that orbits around a center point while
	maintaining a view on a center point.

	For this camera, the ``scale_factor`` indicates the zoom level, and
	the ``center`` indicates the position to put at the center of the
	view.

	Parameters
	----------
	fov : float
		Field of view. Zero (default) means orthographic projection.
	distance : float | None
		The distance of the camera from the rotation point (only makes sense
		if fov > 0). If None (default) the distance is determined from the
		scale_factor and fov.
	translate_speed : float
		Scale factor on translation speed when moving the camera center point.
	**kwargs : dict
		Keyword arguments to pass to `BaseCamera`.

	Notes
	-----
	Interaction:

		* LMB: orbits the view around its center point.
		* RMB or scroll: change scale_factor (i.e. zoom level)
		* SHIFT + LMB: translate the center point
		* SHIFT + RMB: change FOV

	"""

	_state_props = Base3DRotationCamera._state_props + ('_quaternion',)

	def __init__(self, fov=45.0, distance=None, translate_speed=1.0, **kwargs):
		super().__init__(fov=fov, interactive=False, **kwargs)

		# Set camera attributes
		self._quaternion = Quaternion()
		self.distance = distance  # None means auto-distance
		self._camera_frame_quat = Quaternion(-0.5,0.5,0.5,0.5)


	def _update_rotation(self, event):
		pass

	def _get_rotation_tr(self):
		"""Return a rotation matrix based on camera parameters"""
		rot, x, y, z = self._quaternion.get_axis_angle()
		return transforms.rotate(180 * rot / np.pi, (x, y, z))

	def _get_dim_vectors(self):
		# Override vectors, camera has no sense of "up"
		return np.eye(3)[::-1]

	def _setQuat(self, quat:tuple[float,float,float,float], update=False):
		self._quaternion =  Quaternion(*quat) * self._camera_frame_quat
		if update:
			self._update_camera_pos()

	def setQuaternion(self, quat:tuple[float,float,float,float], scaler_first=True):
		if not scaler_first:
			sf_quat = (quat[3],quat[0],quat[1],quat[2])
		else:
			sf_quat = quat
		self._setQuat(sf_quat,update=True)

	def _setPos(self, pos:tuple[float,float,float], update=False):
		self.center = pos
		if update:
			self._update_camera_pos()

	def setPosition(self, pos:tuple[float,float,float]):
		self._setPos(pos,update=True)

	def setPose(self, pos:tuple[float,float,float], quat:tuple[float,float,float,float], scaler_first=True):
		if not scaler_first:
			sf_quat = (quat[3],quat[0],quat[1],quat[2])
		else:
			sf_quat = quat
		self._setPos(pos, update=False)
		self._setQuat(sf_quat, update=True)


class MovableFixedCamera(ArcballCamera):
	"""3D camera class that orbits around a center point while
	maintaining a view on a center point.

	For this camera, the ``scale_factor`` indicates the zoom level, and
	the ``center`` indicates the position to put at the center of the
	view.

	Parameters
	----------
	fov : float
		Field of view. Zero (default) means orthographic projection.
	distance : float | None
		The distance of the camera from the rotation point (only makes sense
		if fov > 0). If None (default) the distance is determined from the
		scale_factor and fov.
	translate_speed : float
		Scale factor on translation speed when moving the camera center point.
	**kwargs : dict
		Keyword arguments to pass to `BaseCamera`.

	Notes
	-----
	Interaction:

		* LMB: orbits the view around its center point.
		* RMB or scroll: change scale_factor (i.e. zoom level)
		* SHIFT + LMB: translate the center point
		* SHIFT + RMB: change FOV

	"""

	_state_props = Base3DRotationCamera._state_props + ('_quaternion',)

	def __init__(self, fov=45.0, distance=None, translate_speed=1.0, **kwargs):
		super().__init__(fov=fov, **kwargs)

		# Set camera attributes
		self._quaternion = Quaternion()
		self.distance = distance  # None means auto-distance
		self._camera_frame_quat = Quaternion(-0.5,0.5,0.5,0.5)


	def _get_rotation_tr(self):
		"""Return a rotation matrix based on camera parameters"""
		rot, x, y, z = self._quaternion.get_axis_angle()
		return transforms.rotate(180 * rot / np.pi, (x, y, z))

	def _setQuat(self, quat:tuple[float,float,float,float], update=False):
		self._quaternion =  Quaternion(*quat) * self._camera_frame_quat
		if update:
			self._update_camera_pos()

	def setQuaternion(self, quat:tuple[float,float,float,float], scaler_first=True):
		if not scaler_first:
			sf_quat = (quat[3],quat[0],quat[1],quat[2])
		else:
			sf_quat = quat
		self._setQuat(sf_quat,update=True)

	def _setPos(self, pos:tuple[float,float,float], update=False):
		self.center = pos
		if update:
			self._update_camera_pos()

	def setPosition(self, pos:tuple[float,float,float]):
		self._setPos(pos,update=True)

	def setPose(self, pos:tuple[float,float,float], quat:tuple[float,float,float,float], scaler_first=True):
		if not scaler_first:
			sf_quat = (quat[3],quat[0],quat[1],quat[2])
		else:
			sf_quat = quat
		self._setPos(pos, update=False)
		self._setQuat(sf_quat, update=True)