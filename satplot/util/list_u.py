from bisect import bisect_left

import numpy as np

import satplot.util.exceptions as exceptions


def flatten(nested_list:list[list|tuple]|tuple) -> list:
	"""Flattens a list of lists into a single list
	
	Parameters
	----------
	nested_list : {list}
		list of lists
	
	Returns
	-------
	list
		flattened list
	"""
	out = []
	for item in nested_list:
		if isinstance(item, list|tuple):
			out.extend(flatten(item))
		else:
			out.append(item)
	return out


def contain_sublist(sub_list:list, search_list:list) -> bool:
	"""Determines if list `search_list` contains sub_list `sub_list
	
	Parameters
	----------
	sub_list : {list}
		list to search for
	search_list : {list}
		list to search through
	
	Returns
	-------
	bool
		True if contains sub_listist

	# TODO: This can be made faster by using a non-naive string search algorithm	
	"""
	
	if len(sub_list) > len(search_list):
		return False

	if sub_list == search_list:
		return True

	len_sub = len(sub_list)

	ext_l = search_list + search_list[:len_sub - 1]

	for ii in range(len(search_list)):		
		if ext_l[ii:ii + len(sub_list)] == sub_list:
			return True
	return False


def get_closest(myList:list, myNumber:float) -> tuple[int,int]:
	"""Finds the closest value in a list
	Assuming myList is a sorted list of floats. Returns closest value to myNumber.

	If two numbers are equally close, return the smallest number.
	
	Parameters
	----------
	myList : {list}
		sorted list to search through
	myNumber : {}
		value to find of type which can be compared with elements of myList
	
	Returns
	-------
	float, int
		closest value, index of closest value
		if index == -1 signifies that myNumber is greater than last value in list
	"""
	# Check list is 1D
	if isinstance(myList, np.ndarray):
		if len(myList.shape) > 1:
			raise exceptions.DimensionError("Can only find the closest value on a 1D array")

	pos = bisect_left(myList, myNumber)
	if pos == 0:
		return myList[0], 0
	if pos == len(myList):
		return myList[-1], -1
	before = myList[pos - 1]
	after = myList[pos]
	if after - myNumber < myNumber - before:
		return after, pos
	else:
		return before, pos - 1
