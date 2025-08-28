

import numpy as np
import numpy.typing as nptyping
from scipy.interpolate import interp1d


def uniqueRows(arr:nptyping.NDArray, to_decimal:int=8) -> nptyping.NDArray:
	'''
	Find the unique rows in an array, rounding to the specified tolerance
	to avoid floating point errors.
	
	Parameters
	----------
	arr : (n,3) ndarray
	
	to_decimal: int
		Tolerance for floating point errors.

	Returns	
	-------
	(m,3) ndarray
		m<=n
	'''
	arr = np.ascontiguousarray(arr)
	unique_arr = np.unique(arr.round(decimals=to_decimal), axis=0)
	return unique_arr

def uniqueRowsOrdered(arr:nptyping.NDArray, to_decimal:int=8) -> nptyping.NDArray:
	'''
	Return the unique rows in an array, rounding to the specified tolerance
	to avoid floating point errors.
	But keep row order.

	Parameters
	----------
	arr : (n,3) ndarray

	to_decimal: int
		Tolerance for floating point errors.

	Returns
	-------
	(m,3) ndarray
		m<=n
	'''

	unique_idxs = np.unique(arr.round(decimals=to_decimal), axis=0, return_index=True)[1]
	sorted_unique_idxs = np.sort(unique_idxs)

	return arr[sorted_unique_idxs,:]

def interpNans(y, x=None):
	if x is None:
		x = np.arange(len(y))
	nans = np.isnan(y)

	interpolator = interp1d(
		x[~nans],
		y[~nans],
		kind="linear",
		fill_value="extrapolate",
		assume_sorted=True,
	)

	return interpolator(x)

def nonMonotonicInterpNans(x, y):
	out_y = y.copy()
	# check if assumptions are met
	if len(x) != len(out_y):
		raise ValueError('Length of x and y arrays must be equal')
	if np.isnan(x).any():
		raise ValueError('x array cannot have any nans')

	nans = np.where(np.isnan(y))[0]
	# handle if first or last elements are nan
	if 0 in nans:
		out_y[0] = out_y[1]
	if len(out_y)-1 in nans:
		out_y[-1] = out_y[-2]

	nans = np.where(np.isnan(out_y))[0]
	if len(nans) == 0:
		return out_y


	# linear interpolate using just the neighbours of the nan idxs
	ys = np.vstack((out_y[nans-1],np.vstack((out_y[nans],out_y[nans+1]))))
	xs = np.vstack((x[nans-1],np.vstack((x[nans],x[nans+1]))))
	new_ys = (ys[0,:]*(xs[2,:]-xs[1,:])+ys[2,:]*(xs[1,:]-xs[0,:]))/\
	            (xs[2,:]-xs[0,:])

	out_y[nans] = new_ys
	return out_y
