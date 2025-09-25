import datetime as dt
import logging

from collections.abc import Callable

import numpy as np

from orbviz.model.data_models.base_models import BaseDataModel

logger = logging.getLogger(__name__)

class TimeSeries:
	def __init__(self, label:str,
						timestamps:np.ndarray[tuple[int], np.dtype[np.datetime64]],
						vals:np.ndarray[tuple[int], np.dtype[np.datetime64]],
						units:str='',
						timespan_fetch:None|Callable=None,
						ordinate_fetch:None|Callable=None,
						ordinate_col_idx:None|int=None):
		self._label = label
		self._timestamps = timestamps
		self._timestamps_fetch = timespan_fetch

		self._vals = vals
		self._vals_fetch_func = ordinate_fetch
		self._vals_col_idx = ordinate_col_idx

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
		# TODO: figure out return types
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

	def _updateArtists(self) -> None:
		for handle in self._artist_handles.values():
			if isinstance(handle, list):
				for el in handle:
					el.set_xdata(self.abscissa)
					el.set_ydata(self.ordinate)
			else:
				handle.set_xdata(self.abscissa)
				handle.set_ydata(self.ordinate)

	def update(self) -> None:
		if self._vals_fetch_func is None and self._timestamps_fetch is None:
			logger.debug('Timeseries %s is static, not updating.', self._label)
			return

		if self._vals_fetch_func is None:
			raise ValueError(f'Cannot upate timeseries: {self._label} abscissa values without an update function pointer')

		if self._vals_fetch_func is None:
			raise ValueError(f'Cannot upate timeseries: {self._label} timestamp values without an update function pointer')

		vals = self._vals_fetch_func()
		self._timestamps = self._timestamps_fetch()[:]


		if not isinstance(vals, np.ndarray):
			raise TypeError(f"Can't update timeseries: {self._label} update function returns a non ndArray ")

		if self._vals_col_idx is None and len(vals.shape) != 1:
			raise IndexError(f"Can't update timeseries: {self._label}. Don't know how to index returned ndArray")

		if self._vals_col_idx is not None and len(vals.shape) == 2 and self._vals_col_idx >= vals.shape[1]:
			raise IndexError(f"Can't update timeseries: {self._label}. Abscissa col_index is outside range of abscissa columns.")

		if self._vals_col_idx is None:
			self._vals = vals[:]
		else:
			self._vals = vals[:, self._vals_col_idx]

		self._range = (self._vals.min(), self._vals.max())
		self._domain = (self._timestamps.min(), self._timestamps.max())

		self._updateArtists()

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

	ordinate_fetch_func = data_model.attrFetchFunctionGenerator(attr_key)

	ordinate = ordinate_fetch_func()

	if isinstance(ordinate, np.ndarray):
		if len(ordinate.shape) == 1:
			created_ts[attr_key] = TimeSeries(attr_key,
												data_model.timespan[:],
												ordinate[:],
												timespan_fetch=data_model.getTimespan,
												ordinate_fetch=ordinate_fetch_func)
		elif len(ordinate.shape) == 2 and ordinate.shape[1] == 3:
			ts_key = f'{attr_key}_x'
			created_ts[ts_key] = TimeSeries(attr_key,
												data_model.timespan[:],
												ordinate[:],
												timespan_fetch=data_model.getTimespan,
												ordinate_fetch=ordinate_fetch_func,
												ordinate_col_idx=0)

			ts_key = f'{attr_key}_y'
			created_ts[ts_key] = TimeSeries(attr_key,
												data_model.timespan[:],
												ordinate[:],
												timespan_fetch=data_model.getTimespan,
												ordinate_fetch=ordinate_fetch_func,
												ordinate_col_idx=1)

			ts_key = f'{attr_key}_z'
			created_ts[ts_key] = TimeSeries(attr_key,
												data_model.timespan[:],
												ordinate[:],
												timespan_fetch=data_model.getTimespan,
												ordinate_fetch=ordinate_fetch_func,
												ordinate_col_idx=2)
		else:
			for dim in range(ordinate.shape[1]):
				ts_key = f'{attr_key}_dim'
				created_ts[ts_key] = TimeSeries(attr_key,
												data_model.timespan[:],
												ordinate[:],
												timespan_fetch=data_model.getTimespan,
												ordinate_fetch=ordinate_fetch_func,
												ordinate_col_idx=dim)
	else:
		raise KeyError(f"Can't make a timeseries: {attr_key} out of a non ndArray ")

	return created_ts