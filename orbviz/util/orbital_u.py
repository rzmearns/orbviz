

from astropy import SkyCoord
import numpy as np
import numpy.typing as nptyping

import orbviz.util.constants as consts


def ssoInc(alt:float, e:float=0) -> float:
	# TODO: update to calculate for different central bodies
	'''Generates required inclination for given altitude [km] to maintain Sun Syncrhonous orbit (default = circular)'''

	a = consts.R_EARTH + alt * 1e3
	# print(a)
	p = a * (1 - e**2)
	# print(p)
	period = 2 * np.pi * np.sqrt(a**3 / consts.GM_EARTH)
	# print(period)
	req_prec_rate = (2 * np.pi / 365.25) * (1 / 86400.)
	# print(req_prec_rate)
	req_prec_orb = req_prec_rate * period
	# print(req_prec_orb)

	cosi = (req_prec_orb * p**2) / (-3 * np.pi * consts.J2 * consts.R_EARTH**2)
	# print(cosi)

	inc = np.arccos(cosi)

	return np.rad2deg(inc)


def calcPeriod(a:float) -> float:
	"""Returns the period of an elliptical or circular orbit
	
	Parameters
	----------
	a : {float}
		semi-major axis in m

	Returns
	-------
	float
		Orbital period in s
	"""

	period = 2 * np.pi * np.sqrt(a**3 / consts.GM_EARTH)
	return period


def calcOrbitalVel(a:float, pos:nptyping.NDArray) -> nptyping.NDArray:
	"""Return the instantaneous velocity magnitude for an elliptical orbit of semi-major axis, a at position, pos.
	
	Parameters
	----------
	a : {float}
		semi-major axis in m
	pos : {ndarray}
		cartesian position, assuming the origin is at the central body.
	
	Returns
	-------
	float
		instantaneous velocity magnitude.
	"""
	r = np.linalg.norm(pos)

	v = np.sqrt(consts.GM_EARTH * (2 / r - 1 / a))

	return v


def calcMeanMotion(a: float) -> float:
	"""Returns mean motion [radians/s] for an elliptical or circular orbit with semi-major axis a
	
	Parameters
	----------
	a : {float}
		semi-major axis in m

	Returns
	-------
	float
		Orbital period in s
	"""

	return np.sqrt(consts.GM_EARTH / a**3)

def toNPArray(sky_coord:SkyCoord) -> nptyping.NDArray:
	"""Transform an astropy.SkyCoord object into a (3,) numpy array.
	
	Parameters
	----------
	sky_coord: {SkyCoord}
		astropy SkyCoord object
		
	Returns
	-------
	vector: {(3,) numpy array}
		Cartesian coordinates of sky_coord
	"""
	sky_coord.representation_type = 'cartesian'
	vector = np.array([sky_coord.x.value, sky_coord.y.value, sky_coord.z.value])
	return vector