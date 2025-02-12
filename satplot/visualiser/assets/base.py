from abc import ABC, abstractmethod
import numpy as np
import traceback

class BaseAsset(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, name=None, v_parent=None):
		# Is this asset is_active for drawing
		self.is_active = False
		# dict storing vispy visuals to be drawn as part of this asset
		self.visuals = {}
		# dict storing satplot child assets
		self.assets = {}
		# dict storing crucial data for this asset
		self.data = {}
		self.data['name'] = name
		self.data['v_parent'] = v_parent
		self.data['curr_index'] = None


		# Flag to indicate that this is the first drawing since the asset 
		# has been re-instantiated. This generally means that any visuals 
		# must be re-created
		self.first_draw = True
		# Flag to indicate that the underlying data of the asset has changed
		# (likely due to a new timestep being displayed), and as such, the 
		# positions and transforms of child-assets and visuals must be recomputed
		self.is_stale = False
	
	##### Viewbox methods
	def _attachToParentView(self):
		'''Sets all vispy visuals to use the stored parent'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				# print(f"Attaching visual of {self.data['name']} to parent")
				visual.parent = self.data['v_parent']
			elif visual is not None:
				# print(f"Attaching visual of {self.data['name']} to parent")
				for el in visual:
					el.parent = self.data['v_parent']

	def attachToParentViewRecursive(self):
		'''Sets all nested vispy visuals to use the stored parent'''
		self._attachToParentView()
		for asset in self.assets.values():
			if asset is not None:
				asset.attachToParentViewRecursive()

	def _detachFromParentView(self):
		'''Sets all vispy visuals to use no parent -> stops rendering'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				# single visual
				# print(f"Detaching visual of {self.data['name']} to parent")
				visual.parent = None
			elif visual is not None:
				# print(f"Detaching visual of {self.data['name']} from parent")
				# list of visuals
				for el in visual:
					el.parent = None

	def detachFromParentViewRecursive(self):
		'''Sets all nested vispy visuals to use no parent -> stops rendering'''
		self._detachFromParentView()

		for asset in self.assets.values():
			asset.detachFromParentViewRecursive()

	def setParentView(self, view):
		'''Stores the v_parent to the vispy view to use'''
		self.data['v_parent'] = view
		for asset in self.assets.values():
			asset.data['v_parent'] = view

	##### State methods
	def makeActive(self):
		# print(f"{self.data['name']} being made active.")
		if not self.is_active:
			self.setFirstDrawFlagRecursive()
			self.attachToParentViewRecursive()  # will attach all assets  recursively
		self.setActiveFlagRecursive()

	def makeDormant(self):
		self.clearActiveFlagRecursive()
		self.setStaleFlagRecursive()
		self.detachFromParentViewRecursive()

	def _setActiveFlag(self):
		self.is_active = True

	def _clearActiveFlag(self):
		self.is_active = False

	def setActiveFlagRecursive(self):
		self._setActiveFlag()
		for asset in self.assets.values():
			asset.setActiveFlagRecursive()

	def clearActiveFlagRecursive(self):
		self._clearActiveFlag()
		for asset in self.assets.values():
			asset.clearActiveFlagRecursive()

	def isActive(self):
		return self.is_active

	def _setStaleFlag(self):
		self.is_stale = True

	def setStaleFlagRecursive(self):
		self._setStaleFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.setStaleFlagRecursive()

	def _clearStaleFlag(self):
		self.is_stale = False

	def isStale(self):
		return self.is_stale

	def _setFirstDrawFlag(self):
		self.first_draw = True

	def setFirstDrawFlagRecursive(self):
		self._setFirstDrawFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.setFirstDrawFlagRecursive()

	# should only be called within its own recomputeRedraw
	def _clearFirstDrawFlag(self):
		self.first_draw = False

	def isFirstDraw(self):
		return self.first_draw

	def setVisibility(self, state):
		for visual in self.visuals.values():
			visual.visible = state

	def setVisibilityRecursive(self, state):
		'''Sets the visibility of this asset and all child-assets'''
		self.setVisibility(state)
		for asset in self.assets.values():
			asset.setVisibilityRecursive(state)


	@abstractmethod
	def _initData(self):
		'''Initialise data used for drawing this and any child assets
			Any parameters can be passed here'''
		raise NotImplementedError

	@abstractmethod
	def _instantiateAssets(self):
		'''Create child assets
			pass desired parent to asset at instantiation'''
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
	def recomputeRedraw(self):
		'''Recompute the asset geometry; apply to child assets and visuals
			
			Should include the following check at the beginning of the function
			if self.first_draw:
				...
				self.first_draw = False

			Should include the following iteration in the overriding method
			self.subAssetsRecompute()
			self.is_stale = False'''
		raise NotImplementedError
	
	# def forceRedraw(self):
	# 	# Method to manually force the redraw of all assets

	# 	self.is_stale = True
	# 	self.recompute()
	# 	for asset in self.assets.values():
	# 		if isinstance(asset,BaseAsset):
	# 			asset.is_stale = True
	# 			asset.recompute()


	def updateIndex(self, index):
		'''Update the stored curr_index value
			Should include the following iteration in the overriding method
			for asset in self.assets.values():
				asset.updateIndex() 
			self.is_stale = True'''
		self.data['curr_index'] = index
		self._setStaleFlag()
		for asset in self.assets.values():
			if isinstance(asset,BaseAsset):
				asset.updateIndex(index)

	def getScreenMouseOverInfo(self):
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		return mo_info

	def mouseOver(self, index):
		return


	##### helper functions
	def _listVisuals(self):
		keys = [key for key in self.visuals.keys()]
		values = [key for key in self.visuals.values()]
		return keys, values
	
	def _printVisuals(self):
		k,v = self._listVisuals()
		print(f"{self.__name__} asset has visuals:")
		for ii, key in enumerate(k):
			print(f"\t{key}-> ref:{v[ii]}")

	def _printFlags(self):
		print(f'\tactive:{self.isActive()}')
		print(f'\tstale:{self.isStale()}')
		print(f'\tfirst_draw:{self.isFirstDraw()}')


	def _listAssets(self):
		keys = [key for key in self.assets.keys()]
		values = [key for key in self.assets.values()]
		return keys, values
	
	def _printAssets(self):
		k,v = self._listAssets()
		print(f"{self.__name__} asset has child assets:")
		for ii, key in enumerate(k):
			print(f"\t{key}-> ref:{v[ii]}")

	def _printParent(self,visual_key=None, asset_key=None):
		print(f"asset {self.data['name']} parent scene:{self.data['v_parent']}")
		if visual_key is not None:
			print(f"\tvisual {visual_key} parent scene:{self.visuals[visual_key].parent}")
		if asset_key is not None:
			print(f"\tasset {asset_key} parent scene:{self.assets[asset_key].data['v_parent']}")



class SimpleAsset(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, name=None, v_parent=None):
		# Is this asset is_active for drawing
		self.is_active = False
		# dict storing vispy visuals to be drawn as part of this asset
		self.visuals = {}
		# dict storing crucial data for this asset
		self.data = {}
		self.data['name'] = None
		self.data['v_parent'] = v_parent
		self.data['curr_index'] = None


		# Flag to indicate that this is the first drawing since the asset 
		# has been re-instantiated. This generally means that any visuals 
		# must be re-created
		self.first_draw = True
		# Flag to indicate that the underlying data of the asset has changed
		# (likely due to a new timestep being displayed), and as such, the 
		# positions and transforms of child-assets and visuals must be recomputed
		self.is_stale = False
	
	def _attachToParentView(self):
		'''Sets all vispy visuals to use the stored parent'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				visual.parent = self.data['v_parent']
			elif visual is not None:
				for el in visual:
					el.parent = self.data['v_parent']

	def attachToParentViewRecursive(self):
		'''Sets all nested vispy visuals to use the stored parent'''
		self._attachToParentView()

	def _detachFromParentView(self):
		'''Sets all nested vispy visuals to use no parent -> stops rendering'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				# single visual
				visual.parent = None
			elif visual is not None:
				# list of visuals
				for el in visual:
					el.parent = None

	def detachFromParentViewRecursive(self):
		self._detachFromParentView()

	def setParentView(self, view):
		'''Stores the v_parent to the vispy view to use'''
		self.data['v_parent'] = view

	##### State methods
	def makeActive(self):
		if not self.is_active:
			self.setFirstDrawFlagRecursive()
			self.attachToParentViewRecursive()
		self.is_active = True

	def makeDormant(self):
		self.clearActiveFlagRecursive()
		self.setStaleFlagRecursive()
		self.detachFromParentViewRecursive()

	def isActive(self):
		return self.is_active

	def _setActiveFlag(self):
		self.is_active = True

	def _clearActiveFlag(self):
		self.is_active = False

	def setActiveFlagRecursive(self):
		self._setActiveFlag()

	def clearActiveFlagRecursive(self):
		self._clearActiveFlag()

	def _setStaleFlag(self):
		self.is_stale = True

	def setStaleFlagRecursive(self):
		self._setStaleFlag()

	def _clearStaleFlag(self):
		self.is_stale = False

	def isStale(self):
		return self.is_stale

	def _setFirstDrawFlag(self):
		self.first_draw = True

	def setFirstDrawFlagRecursive(self):
		self._setFirstDrawFlag()

	# first_draw flag should only be cleared within its own recomputeRedraw
	def _clearFirstDrawFlag(self):
		self.first_draw = False

	def isFirstDraw(self):
		return self.first_draw

	def setVisibility(self, state):
		for visual in self.visuals.values():
			visual.visible = state

	def setVisibilityRecursive(self, state):
		'''Sets the visibility of this asset and all child-assets'''
		self.setVisibility(state)


	@abstractmethod
	def _initData(self):
		'''Initialise data used for drawing this and any child assets
			Any parameters can be passed here'''
		raise NotImplementedError

	@abstractmethod
	def _instantiateAssets(self):
		'''Create child assets
			pass desired parent to asset at instantiation'''
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
	def setTransform(self, pos=(0,0,0), rotation=np.eye(3)):
		'''Directly set the linear transform to be applied to the visuals

			Should include the following iteration in the overriding method
			for asset in self.assets.values():
				asset.setTransform()'''
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

	def _printParent(self,visual_key=None):
		print(f"asset {self.data['name']} parent scene:{self.data['v_parent']}")
		if visual_key is not None:
			print(f"\tvisual {visual_key} parent scene:{self.visuals[visual_key].parent}")