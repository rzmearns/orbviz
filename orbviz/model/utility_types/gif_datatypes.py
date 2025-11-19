import pathlib

import spherapy.timespan

# add flag that camera adjustment should be used

class ThreeDimCameraAdjustment:
	_az_start: float
	_el_start: float
	_az_range: float
	_el_range: float
	_az_step: float
	_el_step: float

	def __init__(self, az_start=0, el_start=0, az_range=0, el_range=0) -> None:
		self._az_start = az_start
		self._el_start = el_start
		self._az_range = az_range
		self._el_range = el_range
		self._az_step = 0
		self._el_step = 0

	@property
	def az_start(self) -> float:
		return self._az_start

	@az_start.setter
	def az_start(self, val) -> None:
		if val >= -180 and val<180:
			self._az_start = val
		else:
			raise ValueError(f'Azimuth Start value must be in range -180<=val<180, is {val}')

	@property
	def el_start(self) -> float:
		return self._el_start

	@el_start.setter
	def el_start(self, val) -> None:
		if val >= -90 and val <= 90:
			self._el_start = val
		else:
			raise ValueError(f'Elevation Start value must be in range -90<=val<=90, is {val}')

	@property
	def az_range(self) -> float:
		return self._az_range

	@az_range.setter
	def az_range(self, val) -> None:
		self._az_range = val

	@property
	def el_range(self) -> float:
		return self._el_range

	@el_range.setter
	def el_range(self, val) -> None:
		self._el_range = val

	@property
	def az_step(self) -> float:
		return self._az_step

	@az_step.setter
	def az_step(self, val) -> None:
		self._az_step = val

	@property
	def el_step(self) -> float:
		return self._el_step

	@el_step.setter
	def el_step(self, val) -> None:
		self._el_step = val



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

	# context data
	_cam_type: str
	_cam_config: None|ThreeDimCameraAdjustment

	def __init__(self, timespan, cam_type, loop=True, cam_config=None):
		self._start_idx = 0
		self._end_idx = -1
		self._timespan = timespan
		self._loop = loop
		self._cam_type = cam_type
		self._cam_config = cam_config
		self._num_steps = 0

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
	def file_path(self) -> pathlib.Path:
		return self._file_path

	@file_path.setter
	def file_path(self, val:pathlib.Path) -> None:
		self._file_path = val

	@property
	def cam_type(self) -> str:
	    return self._cam_type

	@property
	def cam_config(self):
		return self._cam_config
