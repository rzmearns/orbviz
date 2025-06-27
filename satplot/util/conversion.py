import numpy as np

def eci2radec(eci:np.ndarray) -> tuple[np.ndarray, np.ndarray]:
	# TODO: check eci is (N,3)
	hxy = np.hypot(eci[:,0], eci[:,1])
	r = np.hypot(hxy, eci[:,2])
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
