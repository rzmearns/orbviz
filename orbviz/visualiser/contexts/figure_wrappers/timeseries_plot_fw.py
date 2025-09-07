import logging
import time

from typing import Any

from matplotlib.backends import backend_qtagg
from matplotlib.figure import Figure
import numpy as np

from orbviz.model.data_models.earth_raycast_data import EarthRayCastData
from orbviz.model.data_models.groundstation_data import GroundStationCollection
from orbviz.model.data_models.history_data import HistoryData
import orbviz.model.data_models.timeseries as timeseries_model
from orbviz.visualiser.contexts.figure_wrappers.base_fw import BaseFigureWrapper

logger = logging.getLogger(__name__)

create_time = time.monotonic()
MIN_MOVE_UPDATE_THRESHOLD = 1
MOUSEOVER_DIST_THRESHOLD = 5
last_mevnt_time = time.monotonic()
mouse_over_is_highlighting = False

class TimeSeriesPlotFigureWrapper(BaseFigureWrapper):
	def __init__(self, w:int=1200, h:int=600, bgcolor:str='white'):

		matplotlib_dpi = 100
		w_inch = w/matplotlib_dpi
		h_inch = h/matplotlib_dpi
		a = Figure(figsize=(w_inch,h_inch),facecolor=bgcolor)
		canvas = backend_qtagg.FigureCanvas(a)

		super().__init__(w,h,bgcolor, canvas)

		self.assets = {}

		self.buildWrapperWidget()

		# self.mouseOverTimer = QtCore.QTimer()
		# self.mouseOverTimer.timeout.connect(self._setMouseOverVisible)
		# self.mouseOverObject = None

	def _buildAssets(self) -> None:
		pass

	def getActiveAssets(self):
		active_assets = []
		for k,v in self.assets.items():
			if v.isActive():
				active_assets.append(k)
		return active_assets

	def addTimeSeries(self, axes_idx:int,
							ts:timeseries_model.TimeSeries):
		if self.axes is None:
			logger.error('Time Series Figure:%s does not have any axes yet.', self)
			raise ValueError(f'Time Series Figure:{self} does not have any axes yet.')



		# check if axes indexing makes sense
		if isinstance(self.axes, np.ndarray):
			row_idx, col_idx = np.unravel_index(axes_idx, (self.axes.shape[0], self.axes.shape[1]))
			if row_idx >= self.axes.shape[0] or col_idx >= self.axes.shape[1]:
				logger.error('Time Series Figure:%s does not have the specified axes:'\
								' has %s x %s axes, requested:%s',
								self, self.axes.shape[0], self.axes.shape[0], axes_idx)
				raise ValueError(f'Time Series Figure:{self} does not have the specified axes:'
									f' has {self.axes.shape[0]} x {self.axes.shape[1]} axes,'
									f' requeseted {axes_idx}')

		else:
			row_idx = 0
			col_idx = 0
			if axes_idx != 0:
				logger.error('Time Series Figure:%s does not have the specified axes:'\
								' has 1 x 1 axes, requested:%s',
								self, axes_idx)
				raise ValueError(f'Time Series Figure:{self} does not have the specified axes:'
									f' has 1 x 1 axes, requeseted {axes_idx}')

		if isinstance(self.axes, np.ndarray):
			handle = self.axes[row_idx, col_idx].plot(ts.abscissa, ts.ordinate, label=ts.label)
		else:
			handle = self.axes.plot(ts.absscissa, ts.ordinate, label=ts.label)

		self.figure.canvas.draw()

		return handle

	def removeTimeSeries(self, axes_idx:int, handle):
		if isinstance(handle, list):
			for el in handle:
				el.remove()
		self.figure.canvas.draw()

	def modelUpdated(self) -> None:
		m,n = self.axes.shape
		for ii in range(m):
			for jj in range(n):
				ax = self.axes[ii,jj]
				ax.relim()
				ax.autoscale()

	def updateIndex(self, index:int) -> None:
		for asset in self.assets.values():
			if asset.isActive():
				asset.updateIndex(index)

	def recomputeRedraw(self) -> None:
		for asset in self.assets.values():
			if asset.isActive():
				asset.recomputeRedraw()

	def setFirstDrawFlags(self) -> None:
		for asset in self.assets.values():
			asset.setFirstDrawFlagRecursive()

	def prepSerialisation(self) -> dict[str,Any]:
		pass

	def deSerialise(self, state:dict[str,Any]) -> None:
		pass

	def mapAssetPositionsToScreen(self) -> list:
		mo_infos = []
		return mo_infos

	def onMouseMove(self, event) -> None:
	# def onMouseMove(self, event:MouseEvent) -> None:
		pass

	# def onResize(self, event:ResizeEvent) -> None:
	def onResize(self, event) -> None:
		pass

	# def onMouseScroll(self, event:QtGui.QMouseEvent) -> None:
	def onMouseScroll(self, event) -> None:
		pass