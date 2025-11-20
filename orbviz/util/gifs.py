import pathlib

import spherapy.timespan

import orbviz.visualiser.cameras.cam_utility_types as cam_utility_types


def isCamSupported(cam_type:cam_utility_types.CanvasCameraTypes) -> bool:

	if cam_type in [cam_utility_types.CanvasCameraTypes.TURNTABLE,
					cam_utility_types.CanvasCameraTypes.RESTRICTEDPANZOOM,
					cam_utility_types.CanvasCameraTypes.STATIC2D,
					cam_utility_types.CanvasCameraTypes.MATPLOTLIB]:
		return True
	else:
		return False

class GIFConfig:
	# timespan data
	_start_idx: int
	_end_idx: int
	_timespan: spherapy.timespan.TimeSpan
	_num_steps: int

	# GIF data
	_file_path: None|pathlib.Path
	_framerate: int
	_loop: bool

	# cam data
	_cam_config: None|cam_utility_types.TurntableCameraAdjustment| \
					cam_utility_types.RestrictedPanZoomCameraAdjustment| \
					cam_utility_types.Static2DCameraAdjustment| \
					cam_utility_types.MatplotlibCameraAdjustment

	def __init__(self,
					timespan:spherapy.timespan.TimeSpan,
					loop:bool=True,
					cam_config:None|cam_utility_types.TurntableCameraAdjustment|
									cam_utility_types.RestrictedPanZoomCameraAdjustment|
									cam_utility_types.Static2DCameraAdjustment|
									cam_utility_types.MatplotlibCameraAdjustment=None):
		self._start_idx = 0
		self._end_idx = -1
		self._timespan = timespan
		self._loop = loop
		self._cam_config = cam_config
		self._num_steps = 0
		self._file_path = None
		self._framerate = 0

	@property
	def start_idx(self) -> int:
		return self._start_idx

	@start_idx.setter
	def start_idx(self, val:int) -> None:
		self._start_idx = val

	@property
	def end_idx(self) -> int:
		return self._end_idx

	@end_idx.setter
	def end_idx(self, val:int) -> None:
		self._end_idx = val

	@property
	def num_steps(self) -> int:
		return self._num_steps

	@num_steps.setter
	def num_steps(self, val:int) -> None:
		self._num_steps = val

	@property
	def timespan(self) -> spherapy.timespan.TimeSpan:
		return self._timespan

	@timespan.setter
	def timespan(self, val:spherapy.timespan.TimeSpan) -> None:
		self._timespan = val

	@property
	def loop(self) -> bool:
		return self._loop

	@loop.setter
	def loop(self, val:bool) -> None:
		self._loop = val

	@property
	def file_path(self) -> None|pathlib.Path:
		return self._file_path

	@file_path.setter
	def file_path(self, val:pathlib.Path) -> None:
		self._file_path = val

	@property
	def cam_config(self):
		return self._cam_config
