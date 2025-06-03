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


def arrayOverlap(a:nptyping.NDArray, b:nptyping.NDArray) -> nptyping.NDArray:
	'''[summary]
	
	[description]
	
	Parameters
	----------
	a : {[type]}
		[description]
	b : {[type]}
		[description]
	'''
	return np.array([x for x in set(tuple(x) for x in a) & set(tuple(x) for x in b)])

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


def findRows(subarr:nptyping.NDArray, arr:nptyping.NDArray) -> list[int]:
	'''Finds indices in an array row-wise
	
	Finds indices of each row of `subarr` in `arr`
	
	Parameters
	----------
	subarr : {(n,3) ndarray}
		array to find indices of row-wise
	arr : {(n,3) ndarray}
		search array
	
	Returns
	-------
	[list]
		list of indices
	'''
	num_rows=len(subarr)
	indices=[]
	for row in subarr:
		indices.append(np.where((arr == row).all(axis=1))[0][0])

	return indices

def nonUnique(arr:nptyping.NDArray) -> list[nptyping.NDArray]:
	idx_sort=np.argsort(arr)
	sorted_arr=arr[idx_sort]
	vals,idx_start,count=np.unique(sorted_arr,return_counts=True,return_index=True)

	return np.split(idx_sort,idx_start[1:])