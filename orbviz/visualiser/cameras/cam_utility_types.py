from enum import Enum, auto


class CanvasCameraTypes(Enum):
	STATIC2D = auto()
	RESTRICTEDPANZOOM = auto()
	MATPLOTLIB = auto()
	TURNTABLE = auto()

class Static2DCameraAdjustment:
	_cam_type: str
	_cam_adjustment: bool

	def __init__(self) -> None:
		self._cam_type = CanvasCameraTypes.STATIC2D
		self._cam_adjustment = False

	@property
	def cam_type(self) -> str:
		return self._cam_type

	@property
	def cam_adjustment(self) -> bool:
		return self._cam_adjustment

class RestrictedPanZoomCameraAdjustment:
	_cam_type: str
	_cam_adjustment: bool

	def __init__(self) -> None:
		self._cam_type = CanvasCameraTypes.RESTRICTEDPANZOOM
		self._cam_adjustment = False

	@property
	def cam_type(self) -> str:
		return self._cam_type

	@property
	def cam_adjustment(self) -> bool:
		return self._cam_adjustment

class MatplotlibCameraAdjustment:
	_cam_type: str
	_cam_adjustment: bool

	def __init__(self) -> None:
		self._cam_type = CanvasCameraTypes.MATPLOTLIB
		self._cam_adjustment = False

	@property
	def cam_type(self) -> str:
		return self._cam_type

	@property
	def cam_adjustment(self) -> bool:
		return self._cam_adjustment



class TurntableCameraAdjustment:
	_az_start: float
	_el_start: float
	_az_range: float
	_el_range: float
	_az_step: float
	_el_step: float
	_cam_type: str
	_cam_adjustment: bool

	def __init__(self, az_start=0, el_start=0, az_range=0, el_range=0) -> None:
		self._az_start = az_start
		self._el_start = el_start
		self._az_range = az_range
		self._el_range = el_range
		self._az_step = 0
		self._el_step = 0
		self._cam_type = CanvasCameraTypes.TURNTABLE
		self._cam_adjustment = False

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

	@property
	def cam_type(self) -> str:
		return self._cam_type

	@property
	def cam_adjustment(self) -> bool:
		return self._cam_adjustment

	@cam_adjustment.setter
	def cam_adjustment(self, val:bool) -> None:
		self._cam_adjustment = val