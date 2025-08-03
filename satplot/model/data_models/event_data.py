import logging
import pathlib

import typing

import numpy as np
from spherapy.orbit import Orbit
from spherapy.timespan import TimeSpan

from satplot.model.data_models.base_models import BaseDataModel
import satplot.util.conversion as satplot_conversions

logger = logging.getLogger(__name__)

class EventData(BaseDataModel):
	def __init__(self, e_file:pathlib.Path, timespan:TimeSpan, orbit:Orbit):
		super().__init__()
		self._source_timespan = timespan
		self._raw_timestamps, self._raw_descriptions = self._loadEventFile(e_file)
		self._timestamps = self._raw_timestamps[timespan.areTimesWithin(self._raw_timestamps)]
		self._descriptions = []
		idx_within = timespan.areTimesWithin(self._raw_timestamps)
		for ii in range(len(self._raw_timestamps)):
			if idx_within[ii]:
				self._descriptions.append(self._raw_descriptions[ii])
		self._eci_pos = self._interpPositions(self._timestamps, timespan, orbit.pos)
		self._eci_pos = self._eci_pos.astype(np.float64)
		self._latlon = self._interpPositions(self._timestamps, timespan, np.hstack((orbit.lat.reshape(-1,1),orbit.lon.reshape(-1,1))))

	def _loadEventFile(self, e_file: pathlib.Path) -> tuple[np.ndarray[tuple[int], np.dtype[np.datetime64]], np.ndarray[tuple[int,int],np.dtype[np.float64]]]:
		event_timestamps = np.genfromtxt(e_file, delimiter=',', usecols=[0],skip_header=1, converters={0:satplot_conversions.date_parser})
		event_descriptions = list(np.genfromtxt(e_file, delimiter=',', usecols=[1], skip_header=1, dtype=str))
		return event_timestamps, event_descriptions

	def _interpPositions(self, t_search:np.ndarray[tuple[int], np.dtype[np.datetime64]],
								source_timespan:TimeSpan,
								source_pos_array:np.ndarray[tuple[int,int], np.dtype[np.float64]])\
								-> np.ndarray[tuple[int,int], np.dtype[np.float64]]:

		# linear interpolation of source_pos_array
		fractional_idxs = source_timespan.getFractionalIndices(t_search)
		int_idxs = fractional_idxs.astype(int)
		fractional_part = fractional_idxs - int_idxs
		return source_pos_array[int_idxs] \
				+(source_pos_array[int_idxs+1] - source_pos_array[int_idxs])*fractional_part.reshape(-1,1)

	def sliceByTimespanIdx(self, timespan_idx:int) -> tuple[np.ndarray[tuple[int],np.dtype[bool]],
															np.ndarray[tuple[int],np.dtype[bool]]]:
		pre_truth = self._timestamps <= self._source_timespan.asDatetime(timespan_idx)
		post_truth = self._timestamps > self._source_timespan.asDatetime(timespan_idx)
		return pre_truth, post_truth

	def sliceECIData(self, timespan_idx:int) \
					-> tuple[np.ndarray[tuple[int,int],np.dtype[np.float64]],
							np.ndarray[tuple[int,int],np.dtype[np.float64]]]:

		pre_truth, post_truth = self._sliceByTimespanIdx(timespan_idx)
		return self._eci_pos[pre_truth], self._eci_pos[post_truth]

	def sliceLatLonData(self, timespan_idx:int) \
					-> tuple[np.ndarray[tuple[int,int],np.dtype[np.float64]],
							np.ndarray[tuple[int,int],np.dtype[np.float64]]]:

		pre_truth, post_truth = self._sliceByTimespanIdx(timespan_idx)
		return self._latlon[pre_truth], self._latlon[post_truth]

	@property
	def timestamps(self):
		return self._timestamps

	@property
	def descriptions(self):
		return self._descriptions

	@property
	def latlon(self):
		return self._latlon

	@property
	def eci_pos(self):
		return self._eci_pos


