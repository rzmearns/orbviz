import numpy as np
import numpy.typing as nptyping

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