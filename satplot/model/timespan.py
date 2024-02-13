import datetime as dt
from dateutil.relativedelta import relativedelta
import logging
import numpy as np
from astropy.time import Time as astropyTime

import satplot.util.exceptions as exceptions

logger = logging.getLogger(__name__)


class TimeSpan(object):

	def __init__(self, t0, timestep='1S', timeperiod='10S', timezone='00:00'):
		"""
		Create a TimeSpan object, times are assumed to be in UTC
		
		An array of dates as datetimes is accessed with TimeSpan.as_datetime()
		An array of dates as astropy.time is accessed with TimeSpan.as_astropy()

		Does not handle leap seconds

		Parameters
		----------
		t0 : {datetime.datetime}
			datetime object defining the start of the TimeSpan
		num_steps: int
			Number of timesteps
		timestep : {str}, optional
			String describing the time step of the time span. The string is constructed 
			as an integer or float, followed by a time unit: (d)ays,
			(H)ours, (M)inutes, (S)econds, (mS) milliseconds, (uS) microseconds
			(the default is '1S, which is one second.)
		timeperiod : {str}, optional
			String describing the time period of the time span. The string is constructed 
			as an integer or float, followed by a time unit: (y)ears, (m)onths, (W)eeks, (d)ays,
			(H)ours, (M)inutes, (S)econds, (mS) milliseconds, (uS) microseconds
			(the default is '1d', which is one day.)
		timezone : {datetime.timezone}, optional
			Timezone to be implicitly assumed for the timespan. Methods can check against 
			TimeSpan.timezone for instances.

		Raises
		------
		ValueError
		"""

		self.start = t0
		self.init_timezone_str = timezone
		self.timezone, self.timezone_str = self._parseTimezone(timezone)
		self.init_timestep_str = timestep
		self.init_timeperiod_str = timeperiod
		self.time_step = self._parseTimedelta(timestep)
		# Check if integer value of timestep
		self.end = self._parseTimeperiod(t0, timeperiod)
		self.time_period = self.end - self.start	

		logger.info("Creating TimeSpan between {} and {} with {} seconds timestep"
					.format(self.start, self.end, self.time_step.total_seconds()))

		# Convert any timezones to UTC, and strip timezone information
		# Numpy doesn't like timezones as of 1.11
		self.start = self.start.replace(tzinfo=self.timezone)
		self.end = self.end.replace(tzinfo=self.timezone)
		self.start = self.start.astimezone(tz=dt.timezone.utc)
		self.end = self.end.astimezone(tz=dt.timezone.utc)
		self.start = self.start.replace(tzinfo=None)
		self.end = self.end.replace(tzinfo=None)

		if self.start >= self.end:
			logger.error("Timeperiod: {} results in an end date earlier than the start date".
							format(timeperiod))
			raise ValueError("Invalid timeperiod value: {}".format(timeperiod))

		if self.time_period < self.time_step:
			logger.error("Timeperiod: {} is smaller than the timestep {}.".
							format(timeperiod, timestep))
			raise ValueError("Invalid timeperiod value, too small: {}".format(timeperiod))

		# Calculate step numbers and correct for non integer steps.
		self.num_steps = int(np.floor(self.time_period / self.time_step))
		if self.num_steps != self.time_period / self.time_step:
			logger.info("Rounding to previous integer number of timesteps")
			self.end = self.num_steps * self.time_step + self.start
			self.time_period = self.end - self.start
			
			logger.info("Adjusting TimeSpan to {} -> {} with {} seconds timestep".
						format(self.start, self.end, self.time_step.total_seconds()))

			logger.info("TimeSpan has {} timesteps".format(self.num_steps))

		self._timearr = np.arange(self.start, self.end, self.time_step).astype(dt.datetime)

	def __eq__(self, other):
		if not isinstance(other, TimeSpan):
			return NotImplemented

		return np.all(self.asDatetime() == other.asDatetime())

	def __add__(self, other):
		self_copy = TimeSpan(self.start)

		self_copy.start = self.start
		self_copy.init_timestep_str = ''
		self_copy.init_timezone_str = ''
		self_copy.init_timeperiod_str = ''
		self_copy.time_step = None

		self_copy.end = other.end
		self_copy.num_steps = self.num_steps + other.num_steps
		self_copy.time_period = other.end - self_copy.start
		
		self_copy._timearr = np.hstack((self._timearr, other._timearr))

		return self_copy

	def asAstropy(self, *args, scale='utc'):
		"""
		Return ndarray of TimeSpan as astropy.time objects
		
		Returns
		-------
		ndarray
		"""
		# scale = kwargs.get('scale')
		if len(args) == 1 and isinstance(args[0], int):
			return astropyTime(self._timearr, scale=scale)[args[0]]
		else:
			return astropyTime(self._timearr, scale=scale)

	def asDatetime(self, *args):
		"""
		Return ndarray of TimeSpan as datetime objects	
		
		Returns
		-------
		ndarray
		"""
		if len(args) == 1 and isinstance(args[0], int):
			return self._timearr[args[0]]
		else:
			return self._timearr
			
	def secondsSinceStart(self):
		'''
		Return ndarray with the seconds of all timesteps since the beginning.
		'''
		diff = self._timearr - self.start
		days = np.vectorize(lambda x: x.days)(diff)
		secs = np.vectorize(lambda x: x.seconds)(diff)
		usecs = np.vectorize(lambda x: x.microseconds)(diff)
		return days * 86400 + secs + usecs * 1e-6

	def getClosest(self, t_search):
		"""Find the closest time in a TimeSpan
				
		Parameters
		----------
		t_search : {datetime}
			time to find
		
		Returns
		-------
		datetime, int
			Closest datetime in TimeSpan, index of closest date in TimeSpan
		"""
		diff = self._timearr - t_search
		out = np.abs(np.vectorize(lambda x: x.total_seconds())(diff))
		res_index = int(np.argmin(out))
		return self.asDatetime(res_index), res_index

	def _parseTimeperiod(self, t0, timeperiod):
		for index, letter in enumerate(timeperiod):
			if not (letter.isdigit() or letter == '.'):
				break

		val = float(timeperiod[0:index])
		unit = timeperiod[index:]
		values = np.zeros(9)
		if unit == 'y':
			values[8] = val
		elif unit == 'm':
			values[7] = val
		elif unit == 'W':
			values[6] = val
		elif unit == 'd':
			values[5] = val
		elif unit == 'H':
			values[4] = val
		elif unit == 'M':
			values[3] = val
		elif unit == 'S':
			values[2] = val
		elif unit == 'mS':
			values[0] = 1000 * val
		elif unit == 'uS':
			values[0] = val
		else:
			logger.error("Invalid timeperiod unit: Valid units are (y)ears, (m)onths, (W)eeks,"
						+ " (d)ays, (H)ours, (M)inutes, (S)econds, (mS) milliseconds, (uS) microseconds")
			raise ValueError("Invalid timeperiod unit:{}".format(unit))

		return t0 + relativedelta(years=values[8], months=values[7], weeks=values[6],
								days=values[5], hours=values[4], minutes=values[3], 
								seconds=values[2], microseconds=values[0])	# noqa: E126

	def _parseTimedelta(self, timestep):
		for index, letter in enumerate(timestep):
			if not (letter.isdigit() or letter == '.'):
				break

		val = float(timestep[0:index])
		unit = timestep[index:]
		values = np.zeros(6)		
		if unit == 'd':
			values[5] = val
		elif unit == 'H':
			values[4] = val
		elif unit == 'M':
			values[3] = val
		elif unit == 'S':
			values[2] = val
		elif unit == 'mS':
			values[1] = val
		elif unit == 'uS':
			values[0] = val
		else:
			logger.error("Invalid timestep unit: Valid units are (d)ays, (H)ours,"
						+ "(M)inutes, (S)econds, (mS) milliseconds, (uS) microseconds")
			raise ValueError("Invalid timestep unit:{}".format(unit))

		return dt.timedelta(days=values[5], seconds=values[2], 
							microseconds=values[0], milliseconds=values[1],
							minutes=values[3], hours=values[4])

	def _parseTimezone(self, in_str):
		if in_str[0] == '-':
			sign = -1
		else:
			sign = 1
		res = in_str.split(':')
		if len(res) == 1:
			minutes = float(res[0]) * 60
		else:
			hours = int(res[0])
			minutes = (int(res[1]) + abs(hours) * 60) * sign

		delta = dt.timedelta(minutes=minutes)

		if delta > dt.timedelta(hours=24) or delta < dt.timedelta(hours=-24):
			logger.error("Timespan timezone should be between -24:00 and +24:00")
			raise exceptions.OutOfRange("Timespan timezone should be between -24:00 and +24:00")

		h = int(minutes / 60)
		m = int(abs(minutes - (h * 60)))
		tz_str = '{:+03}:{:02}'.format(h, m)

		return dt.timezone(delta), tz_str

	def __len__(self):
		return self.num_steps
