import datetime as dt
import logging

import numpy as np

logger = logging.getLogger(__name__)

class TimeSeries:
	def __init__(self, label:str,
						timestamps:np.ndarray[tuple[int], np.dtype[np.datetime64]],
						vals:np.ndarray[tuple[int], np.dtype[np.datetime64]], units=''):
		self._label = label
		self._timestamps = timestamps

		# TODO: check vals is a numpy view, not a slice
		# if vals.base is None:
		# 	# see https://numpy.org/doc/stable/user/basics.copies.html#how-to-tell-if-the-array-is-a-view-or-a-copy
		# 	raise TypeError('TimeSeries vals attribute must be a view of the data, is likely a copy')
		self._vals = vals

		self._range = (self._vals.min(), self._vals.max())
		self._domain = (self._timestamps.min(), self._timestamps.max())
		self._units = units

		self._artist_handles = {}

	@property
	def ordinate(self) -> np.ndarray[tuple[int], np.dtype[np.datetime64]]:
		return self._vals

	@property
	def abscissa(self) -> np.ndarray[tuple[int], np.dtype[np.datetime64]]:
		return self._timestamps

	@property
	def label(self) -> str:
		return self._label

	@property
	def units(self) -> str:
		return self._units

	@property
	def range(self) -> tuple[float, float]:
		return self._range

	@property
	def domain(self) -> tuple[dt.datetime, dt.datetime]:
		return self._domain

	def addArtist(self, ax, handle) -> None:
		if ax not in self._artist_handles.keys():
			self._artist_handles[ax] = handle
		else:
			logger.error('TimeSeries %s already has an artist on axes: %s', self, ax)
			raise KeyError(f'TimeSeries {self} already has an artist on axes: {ax}')

	def popArtist(self, ax):
		if self.hasArtistForAxes(ax):
			handle = self._artist_handles[ax]
			del self._artist_handles[ax]
			return handle
		return None

	def hasArtistForAxes(self, ax) -> bool:
		if ax in self._artist_handles.keys():
			return True
		else:
			return False