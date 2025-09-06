import datetime as dt
import logging

import numpy as np

from satplot.model.data_models.base_models import BaseDataModel

logger = logging.getLogger(__name__)

class TimeSeries:
	def __init__(self, label:str,
						timestamps:np.ndarray[tuple[int], np.dtype[np.datetime64]],
						vals:np.ndarray[tuple[int], np.dtype[np.datetime64]], units=''):
		self._label = label
		self._timestamps = timestamps

		# TODO: check vals is a numpy view, not a slice
		if vals.base is None:
			# see https://numpy.org/doc/stable/user/basics.copies.html#how-to-tell-if-the-array-is-a-view-or-a-copy
			raise TypeError('TimeSeries vals attribute must be a view of the data, is likely a copy')
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

	def __del__(self):
		# before the timeseries is garbage collected, remove it from any axes
		for handle in self._artist_handles.values():
			if isinstance(handle, list):
				for el in handle:
					el.remove()
			else:
				handle.remove()


def createTimeSeriesFromDataModel(data_model:BaseDataModel, attr_key:str) -> dict[str,TimeSeries]:
	created_ts:dict[str,TimeSeries] = {}
	nested_attr_keys = attr_key.split('.')
	attr = getattr(data_model, nested_attr_keys[0])

	if isinstance(attr, dict):
		attr = list(attr.values())[0]

	if len(nested_attr_keys) > 1:
		ts_dct = createTimeSeriesFromDataModel(attr, '.'.join(nested_attr_keys[1:]))
		ks = ts_dct.keys()
		vs = ts_dct.values()
		new_ks = [f'{nested_attr_keys[0]}.{k}' for k in ks]
		return dict(zip(new_ks,vs))

	if isinstance(attr, np.ndarray):
		if len(attr.shape) == 1:
			created_ts[attr_key] = TimeSeries(attr_key, data_model.timespan[:], attr)
		elif len(attr.shape) == 2 and attr.shape[1] == 3:
			ts_key = f'{attr_key}_x'
			created_ts[ts_key] = TimeSeries(ts_key, data_model.timespan[:], attr[:,0])

			ts_key = f'{attr_key}_y'
			created_ts[ts_key] = TimeSeries(ts_key, data_model.timespan[:], attr[:,1])

			ts_key = f'{attr_key}_z'
			created_ts[ts_key] = TimeSeries(ts_key, data_model.timespan[:], attr[:,2])
		else:
			for dim in range(attr.shape[1]):
				ts_key = f'{attr_key}_dim'
				created_ts[ts_key] = TimeSeries(ts_key, data_model.timespan[:], attr[:,0])
	else:
		raise KeyError("Can't make a timeseries out of a non ndArray ")

	return created_ts