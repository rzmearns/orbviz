import datetime as dt
import logging

import typing

import numpy as np
import pymap3d
import pymap3d.sidereal


def eci2radec(eci:np.ndarray) -> tuple[np.ndarray, np.ndarray]:
	# TODO: check eci is (N,3)
	hxy = np.hypot(eci[:,0], eci[:,1])
	r = np.hypot(hxy, eci[:,2]) 		# noqa: F841
	el = np.arctan2(eci[:,2], hxy)
	az = np.arctan2(eci[:,1], eci[:,0])
	az = az%2*np.pi
	return np.rad2deg(az), np.rad2deg(el)

def decimal2hhmmss(decimal_arr:np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:

	HH = int(decimal_arr/15)
	MM = int(((decimal_arr/15)-HH)*60)
	SS = ((((decimal_arr/15)-HH)*60)-MM)*60
	return HH, MM, SS

def decimal2degmmss(decimal_arr:np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
	deg = int(decimal_arr)
	MM = abs(int((decimal_arr-deg)*60))
	SS = (abs((decimal_arr-deg)*60)-MM)*60

	return deg, MM, SS

def eci2ecef(eci:np.ndarray, time: dt.datetime, high_precision=True) -> tuple:
	"""
	Observer => Point  ECI  =>  ECEF

	J2000 frame

	Parameters
	----------
	eci : np.ndarray [n,3]
		ECI x-location [meters]
	time : datetime.datetime
		time of obsevation (UTC)

	Results
	-------
	ecf: np.ndarray [n,3]
		ECEF coordinates
	"""

	if high_precision:
		# will use astropy GCRS.transform_to(ITRS(obstime=time))
		# this is slightly slower than rotatin the eci vector by sidereal time, but produces a slightly more accurate result
		# direct pymap3d rotation (which uses astropy do to conversion) ~ 27ms per call (32400 coordinates)
		# sidereal rotation ~ 0.8ms per call (32400 coordinates)
		return np.array(pymap3d.eci2ecef(eci[:,0],eci[:,1],eci[:,2],time)).T
	else:
		gst = pymap3d.sidereal.greenwichsrt(pymap3d.sidereal.juliandate(time))
		R = R3(gst)

		ecef = np.empty(eci.shape)
		ecef = R.dot(eci.T).T

	return ecef

def R3(x: float):
	"""Rotation matrix for ECI"""
	return np.array([[np.cos(x), np.sin(x), 0], [-np.sin(x), np.cos(x), 0], [0, 0, 1]])


def date_parser(d_bytes) -> dt.datetime:
	d_bytes = d_bytes[:d_bytes.index(b'.')+4]
	s = d_bytes.decode('utf-8')
	d = dt.datetime.strptime(s,"%Y-%m-%d %H:%M:%S.%f")
	d = d.replace(tzinfo=dt.timezone.utc)
	return d.replace(microsecond=0)