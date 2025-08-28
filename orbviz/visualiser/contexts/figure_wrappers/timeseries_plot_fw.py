import logging
import time

from typing import Any

from matplotlib.backends import backend_qtagg
from matplotlib.figure import Figure
import numpy as np
from orbviz.model.data_models.earth_raycast_data import EarthRayCastData
from orbviz.model.data_models.groundstation_data import GroundStationCollection
from orbviz.model.data_models.history_data import HistoryData
from orbviz.visualiser.contexts.figure_wrappers.base_fw import BaseFigure

logger = logging.getLogger(__name__)

create_time = time.monotonic()
MIN_MOVE_UPDATE_THRESHOLD = 1
MOUSEOVER_DIST_THRESHOLD = 5
last_mevnt_time = time.monotonic()
mouse_over_is_highlighting = False

class TimeSeriesPlotFigureWrapper(BaseFigure):
	def __init__(self, w:int=1200, h:int=600, bgcolor:str='white'):
		matplotlib_dpi = 100
		w_inch = w/matplotlib_dpi
		h_inch = h/matplotlib_dpi
		self.canvas = backend_qtagg.FigureCanvas(Figure(figsize=(w_inch,h_inch),facecolor=bgcolor))

		self._static_ax = self.canvas.figure.subplots()
		t = np.linspace(0, 10, 501)
		self._static_ax.plot(t, np.tan(t), ".")
		self.data_models: dict[str,Any] = {}
		self.assets = {}
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

	def setModel(self, hist_data:HistoryData, gs_data:GroundStationCollection, earth_raycast_data:EarthRayCastData) -> None:
		self.data_models['history'] = hist_data
		self.data_models['groundstations'] = gs_data

	def modelUpdated(self) -> None:
		pass

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