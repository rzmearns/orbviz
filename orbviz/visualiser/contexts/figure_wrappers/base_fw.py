from abc import abstractmethod
import logging

from typing import Any

from matplotlib.axes import Axes
from matplotlib.backends import backend_qtagg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.figure
import matplotlib.gridspec
import numpy as np

from PyQt5 import QtWidgets

logger = logging.getLogger(__name__)

class BaseFigureWrapper:
	def __init__(self, w:int=800, h:int=600, bgcolor:str='white', canvas=None):

		self.widget = QtWidgets.QWidget()
		self.canvas = canvas
		self.controls = FigureControls(self)

		if canvas is not None:
			self.figure = canvas.figure
		else:
			self.figure = None

		self.axes = None


	@abstractmethod
	def _buildAssets(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def getActiveAssets(self):
		raise NotImplementedError()

	@abstractmethod
	def setModel(self, *args, **kwargs) -> None:
		# Can accept any subclass of Base Data Model
		raise NotImplementedError()

	@abstractmethod
	def _modelUpdated(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def updateIndex(self, index:int) -> None:
		raise NotImplementedError()

	@abstractmethod
	def recomputeRedraw(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def setfirstDrawFlags(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def prepSerialisation(self) -> dict[str, Any]:
		raise NotImplementedError()

	@abstractmethod
	def deSerialise(self, state:dict[str, Any]) -> None:
		raise NotImplementedError()

	def buildWrapperWidget(self):
		vlayout = QtWidgets.QVBoxLayout()
		vlayout.addWidget(self.controls.navigation_controls)
		vlayout.addWidget(self.canvas)
		self.widget.setLayout(vlayout)

	def addAxes(self, nrows:int, ncols:int) -> None:
		if self.figure is None:
			logger.error('Figure wrapper:%s does not have a figure yet.', self)
			raise ValueError(f'Figure wrapper:{self} does not have a figure yet.')

		if self.axes is None:
			self.axes = np.empty((nrows,ncols), dtype=Axes)
			self.axes[0,0] = self.figure.subplots(nrows, ncols)
			return

		if isinstance(self.axes, np.ndarray):
			old_gs = self.axes[0,0].get_subplotspec().get_gridspec()
		else:
			old_gs = self.figure.axes.get_subplotspec().get_gridspec()

		new_gs = matplotlib.gridspec.GridSpec(nrows,ncols)

		old_nrows, old_ncols = old_gs.get_geometry()
		old_naxes = old_nrows * old_ncols
		new_naxes = nrows * ncols

		new_axes = np.empty((nrows,ncols), dtype=Axes)

		for ax_idx in range(len(self.figure.axes)-1,-1,-1):
			ax = self.figure.axes[ax_idx]
			if ax_idx <= (new_naxes-1):
				# axes still in new layout, just move
				new_ax_row_idx, new_ax_col_idx = np.unravel_index(ax_idx,(nrows, ncols))
				logger.debug('Moving axes %s to pos: (%s,%s)',ax_idx, new_ax_row_idx, new_ax_col_idx)
				ax.set_subplotspec(new_gs[new_ax_row_idx, new_ax_col_idx])
				new_axes[new_ax_row_idx, new_ax_col_idx] = ax
			else:
				logger.debug('Removing axes %s',ax_idx)
				ax.remove()

		# add any extra axes required
		if new_naxes > old_naxes:
			for ax_idx in range(old_naxes, new_naxes):
				new_ax_row_idx, new_ax_col_idx = np.unravel_index(ax_idx,(nrows, ncols))
				logger.debug('Adding axes %s at pos: (%s,%s)',ax_idx, new_ax_row_idx, new_ax_col_idx)
				self.figure.add_subplot(new_gs[new_ax_row_idx, new_ax_col_idx])
				new_axes[new_ax_row_idx, new_ax_col_idx] = ax

		self.axes = new_axes
		self.figure.tight_layout()
		self.figure.canvas.draw()

	def getFigure(self) -> matplotlib.figure.Figure:
		return self.getCanvas().figure

	def getCanvas(self) -> backend_qtagg.FigureCanvas:
		if self.canvas is None:
			logger.error('Canvas wrapper:%s does not have a canvas yet.', self)
			raise ValueError(f'Canvas wrapper:{self} does not have a canvas yet.')
		else:
			return self.canvas

class FigureControls:
	def __init__(self, parent_figure:BaseFigureWrapper):
		self.navigation_controls = NavigationToolbar(parent_figure.getCanvas(), None)