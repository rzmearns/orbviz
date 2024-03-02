from abc import ABC, abstractmethod


class BaseAsset(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, v_parent=None):
		# dict storing vispy visuals to be drawn as part of this asset
		self.visuals = {}
		# dict storing satplot sub assets
		self.assets = {}
		# dict storing crucial data for this asset
		self.data = {}
		self.data['v_parent'] = v_parent
		self.data['curr_index'] = None


		# Flag to indicate that this is the first drawing since the asset 
		# has been re-instantiated. This generally means that any visuals 
		# must be re-created
		self.first_draw = True
		# Flag to indicate that the underlying data of the asset has changed
		# (likely due to a new timestep being displayed), and as such, the 
		# positions and transforms of sub-assets and visuals must be recomputed
		self.requires_recompute = False
	
	def attachToParentView(self):
		'''Sets all nested vispy visuals to use the stored parent'''
		for asset in self.assets.values():
			asset.attachToParentView()
		for visual in self.visuals.values():
			visual.parent = self.data['v_parent']

	def detachFromParentView(self):
		'''Sets all nested vispy visuals to use no parent -> stops rendering'''
		for asset in self.assets.values():
			asset.detachFromParentView()
		for visual in self.visuals.values():
			visual.parent = None

	def setParentView(self, view):
		'''Stores the v_parent to the vispy view to use'''
		self.data['v_parent'] = view
		for asset in self.assets.values():
			asset.data['v_parent'] = view

	def setVisibility(self, state):
		'''Sets the visibility of this asset and all sub-assets'''
		if state:
			self.attachToParentView()
		else:
			self.detachFromParentView()

	@abstractmethod
	def _initData(self):
		'''Initialise data used for drawing this and any sub assets
			Any parameters can be passed here'''
		raise NotImplementedError

	@abstractmethod
	def _instantiateAssets(self):
		'''Create sub assets'''
		raise NotImplementedError
	
	@abstractmethod
	def _createVisuals(self):
		'''Create visuals on canvas'''
		raise NotImplementedError

	@abstractmethod
	def _setDefaultOptions(self):
		''' Set the default options for the visualiser {dict} '''
		raise NotImplementedError

	@abstractmethod
	def recompute(self):
		'''Recompute the asset geometry; apply to sub assets and visuals
			Should include the following iteration in the overriding method
			for asset in self.assets.values():
				asset.recompute() 
			self.requires_recompute = False'''
		raise NotImplementedError
	
	@abstractmethod
	def updateIndex(self, index):
		'''Update the stored curr_index value
			Should include the following iteration in the overriding method
			for asset in self.assets.values():
				asset.updateIndex() 
			self.requires_recompute = True'''
		raise NotImplementedError
	
	def _listVisuals(self):
		keys = [key for key in self.visuals.keys()]
		values = [key for key in self.visuals.values()]
		return keys, values
	
	def _printVisuals(self):
		k,v = self._listVisuals()
		print(f"{self.__name__} asset has visuals:")
		for ii, key in enumerate(k):
			print(f"\t{key}-> ref:{v[ii]}")

	def _listAssets(self):
		keys = [key for key in self.assets.keys()]
		values = [key for key in self.assets.values()]
		return keys, values
	
	def _printAssets(self):
		k,v = self._listAssets()
		print(f"{self.__name__} asset has sub assets:")
		for ii, key in enumerate(k):
			print(f"\t{key}-> ref:{v[ii]}")