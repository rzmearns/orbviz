import datetime as dt
import numpy as np

GMST_epoch = dt.datetime(2000,1,1,12,0,0)

def epoch2datetime(string):
	"""Converts a fractional epoch string to a datetime object.
	
	[description]
	
	Parameters
	----------
	string : {str}
		fractional year epoch
	
	Returns
	-------
	datetime
	"""
	if not isinstance(string, str):
		string = str(string)

	year = int(string[:2])
	fractional_DoY = float(string[2:])

	base = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
	date = base + dt.timedelta(days=fractional_DoY) - dt.timedelta(days=1)

	return date


def datetime2TLEepoch(date):
	"""Converts a datetime to a TLE epoch
	
	Parameters
	----------
	date : {datetime}
		Datetime object
	
	Returns
	-------
	str
		TLE epoch, with fractional seconds
	"""
	tzinfo = date.tzinfo
	year_str = str(date.year)[-2:]
	day_str = str(date.timetuple().tm_yday).zfill(3)
	fraction_str = str((date - dt.datetime(date.year, date.month, date.day, tzinfo=tzinfo)).total_seconds() / dt.timedelta(days=1).total_seconds())[1:]

	return year_str + day_str + fraction_str


def datetime2sgp4epoch(date):
	"""Converts a datetime to an sgp4 epoch
	
	Parameters
	----------
	date : {datetime}
		Datetime object
	
	Returns
	-------
	float
		SGP4 epoch, with fractional seconds
	"""
	tzinfo = date.tzinfo
	sgp4start = dt.datetime(1949, 12, 31, 0, 0, 0, tzinfo=tzinfo)
	delta = date - sgp4start
	return delta.days + delta.seconds / 86400
