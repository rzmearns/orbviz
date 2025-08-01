from abc import ABC, abstractmethod
from inspect import Attribute
import logging
import numpy as np
import numpy.typing as nptyping
from typing import Any
from typing_extensions import Self
from vispy.scene.widgets.viewbox import ViewBox

logger = logging.getLogger(__name__)

class AbstractSimpleAsset(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		# Is this asset is_active for drawing
		self.is_active = False
		# dict storing vispy visuals to be drawn as part of this asset
		self.visuals = {}
		# dict storing crucial data for this asset
		self.data = {}
		self.data['name'] = name
		self.data['v_parent'] = v_parent
		self.data['curr_index'] = None
		self._dflt_opts = {}
		self.opts = {}

		# Flag to indicate that this is the first drawing since the asset
		# has been re-instantiated. This generally means that any visuals
		# must be re-created
		self.first_draw = True
		# Flag to indicate that the underlying data of the asset has changed
		# (likely due to a new timestep being displayed), and as such, the
		# positions and transforms of child-assets and visuals must be recomputed
		self.is_stale = False

	def _attachToParentView(self) -> None:
		'''Sets all vispy visuals to use the stored parent'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				visual.parent = self.data['v_parent']
			elif visual is not None:
				for el in visual:
					el.parent = self.data['v_parent']

	def attachToParentViewRecursive(self) -> None:
		'''Sets all nested vispy visuals to use the stored parent'''
		self._attachToParentView()

	def _detachFromParentView(self) -> None:
		'''Sets all nested vispy visuals to use no parent -> stops rendering'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				# single visual
				visual.parent = None
			elif visual is not None:
				# list of visuals
				for el in visual:
					el.parent = None

	def detachFromParentViewRecursive(self) -> None:
		self._detachFromParentView()

	def setParentView(self, view:ViewBox) -> None:
		'''Stores the v_parent to the vispy view to use'''
		self.data['v_parent'] = view

	##### State methods
	def makeActive(self) -> None:
		if not self.is_active:
			self.setFirstDrawFlagRecursive()
			self.attachToParentViewRecursive()
		self.is_active = True

	def makeDormant(self) -> None:
		self.clearActiveFlagRecursive()
		self.setStaleFlagRecursive()
		self.detachFromParentViewRecursive()

	def isActive(self) -> bool:
		return self.is_active

	def _setActiveFlag(self) -> None:
		self.is_active = True
		logger.debug(f'Setting ACTIVE flag for {self}')

	def _clearActiveFlag(self) -> None:
		self.is_active = False
		logger.debug(f'Clearing ACTIVE flag for {self}')

	def setActiveFlagRecursive(self) -> None:
		self._setActiveFlag()

	def clearActiveFlagRecursive(self) -> None:
		self._clearActiveFlag()

	def _setStaleFlag(self) -> None:
		logger.debug(f'Setting STALE flag for {self}')
		self.is_stale = True

	def setStaleFlagRecursive(self) -> None:
		self._setStaleFlag()

	def _clearStaleFlag(self) -> None:
		self.is_stale = False
		logger.debug(f'Clearing STALE flag for {self}')

	def isStale(self) -> bool:
		return self.is_stale

	def _setFirstDrawFlag(self) -> None:
		self.first_draw = True
		logger.debug(f'Setting FIRSTDRAW flag for {self}')

	def setFirstDrawFlagRecursive(self) -> None:
		self._setFirstDrawFlag()

	# first_draw flag should only be cleared within its own recomputeRedraw
	def _clearFirstDrawFlag(self) -> None:
		self.first_draw = False
		logger.debug(f'Clearing FIRSTDRAW flag for {self}')

	def isFirstDraw(self) -> bool:
		return self.first_draw

	def setVisibility(self, state:bool) -> None:
		logger.debug(f'Setting visibility for {self} to {state}')
		for visual_name, visual in self.visuals.items():
			if visual is None:
				continue
			visual.visible = state

	def setVisibilityRecursive(self, state:bool) -> None:
		'''Sets the visibility of this asset and all child-assets'''
		self.setVisibility(state)

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		for k,v in self.opts.items():
			state[f'opt_{k}'] = serialiseOption(self.opts[k])
		return state

	def deSerialise(self, state):
		logger.debug(f"Deserialisation of asset {self}")
		for k,v in state.items():
			if 'opt_' in k:
				logger.debug(f'\t{k}:{v}')
				deSerialiseOption(k.removeprefix('opt_'),v,self)

		self.runOptionCallbacks()

	def runOptionCallbacks(self):
		if not self.isActive():
			return
		for opt_str, opt in self.opts.items():
			if opt['callback'] is not None:
				try:
					opt['callback'](opt['value'])
				except NotImplementedError:
					continue

	@abstractmethod
	def _initData(self, *args, **kwargs) -> None:
		'''Initialise data used for drawing this and any child assets
			Any parameters can be passed here'''
		raise NotImplementedError

	@abstractmethod
	def _createVisuals(self) -> None:
		'''Create visuals on canvas'''
		raise NotImplementedError

	@abstractmethod
	def _setDefaultOptions(self) -> None:
		''' Set the default options for the visualiser {dict} '''
		raise NotImplementedError

	@abstractmethod
	def setTransform(self, pos:tuple[float,float,float]=(0,0,0), rotation:nptyping.NDArray=np.eye(3)):
		'''Directly set the linear transform to be applied to the visuals

			Should include the following iteration in the overriding method
			for asset in self.assets.values():
				asset.setTransform()'''
		raise NotImplementedError

	def updateIndex(self, index:int) -> None:
		'''Update the stored curr_index value
			Should include the following iteration in the overriding method
			for asset in self.assets.values():
				asset.updateIndex()
			self.is_stale = True'''
		self.data['curr_index'] = index
		self.setStaleFlagRecursive()

	def _listVisuals(self) -> tuple[list, list]:
		keys = [key for key in self.visuals.keys()]
		values = [key for key in self.visuals.values()]
		return keys, values

	def _printVisuals(self) -> None:
		k,v = self._listVisuals()
		print(f"{self.__name__} asset has visuals:")
		for ii, key in enumerate(k):
			print(f"\t{key}-> ref:{v[ii]}")

	def _printFlags(self) -> None:
		print(f'\tactive:{self.isActive()}')
		print(f'\tstale:{self.isStale()}')
		print(f'\tfirst_draw:{self.isFirstDraw()}')

	def _printParent(self,visual_key:str|None=None):
		print(f"asset {self.data['name']} parent scene:{self.data['v_parent']}")
		if visual_key is not None:
			print(f"\tvisual {visual_key} parent scene:{self.visuals[visual_key].parent}")

	def _printOptions(self) -> None:
		for k,v in self.opts.items():
			print(f'{k}:')
			for k2,v2 in v.items():
				print(f'\t{k2}:{v2}')


class AbstractCompoundAsset(ABC):
	# name_str: str

	@abstractmethod
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		# Is this asset is_active for drawing
		self.is_active = False
		# dict storing satplot child assets
		self.assets = {}
		# dict storing vispy visuals to be drawn as part of this asset
		self.visuals = {}
		# dict storing crucial data for this asset
		self.data = {}
		self.data['name'] = name
		self.data['v_parent'] = v_parent
		self.data['curr_index'] = None
		self._dflt_opts = {}
		self.opts = {}

		# Flag to indicate that this is the first drawing since the asset
		# has been re-instantiated. This generally means that any visuals
		# must be re-created
		self.first_draw = True
		# Flag to indicate that the underlying data of the asset has changed
		# (likely due to a new timestep being displayed), and as such, the
		# positions and transforms of child-assets and visuals must be recomputed
		self.is_stale = False

	def _attachToParentView(self) -> None:
		'''Sets all vispy visuals to use the stored parent'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				visual.parent = self.data['v_parent']
			elif visual is not None:
				for el in visual:
					el.parent = self.data['v_parent']

	def attachToParentViewRecursive(self) -> None:
		'''Sets all nested vispy visuals to use the stored parent'''
		self._attachToParentView()
		for asset in self.assets.values():
			if asset is not None:
				asset.attachToParentViewRecursive()

	def _detachFromParentView(self) -> None:
		'''Sets all nested vispy visuals to use no parent -> stops rendering'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				# single visual
				visual.parent = None
			elif visual is not None:
				# list of visuals
				for el in visual:
					el.parent = None

	def detachFromParentViewRecursive(self) -> None:
		self._detachFromParentView()

		for asset in self.assets.values():
			asset.detachFromParentViewRecursive()

	def setParentView(self, view:ViewBox) -> None:
		'''Stores the v_parent to the vispy view to use'''
		self.data['v_parent'] = view

	##### State methods
	def makeActive(self) -> None:
		if not self.is_active:
			self.setFirstDrawFlagRecursive()
			self.attachToParentViewRecursive()
		self.setActiveFlagRecursive()

	def makeDormant(self) -> None:
		self.clearActiveFlagRecursive()
		self.setStaleFlagRecursive()
		self.detachFromParentViewRecursive()

	def isActive(self) -> bool:
		return self.is_active

	def _setActiveFlag(self) -> None:
		self.is_active = True
		logger.debug(f'Setting ACTIVE flag for {self}')

	def _clearActiveFlag(self) -> None:
		self.is_active = False
		logger.debug(f'Clearing ACTIVE flag for {self}')

	def setActiveFlagRecursive(self) -> None:
		self._setActiveFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.setActiveFlagRecursive()

	def clearActiveFlagRecursive(self) -> None:
		self._clearActiveFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.clearActiveFlagRecursive()

	def _setStaleFlag(self) -> None:
		self.is_stale = True
		logger.debug(f'Setting STALE flag for {self}')

	def setStaleFlagRecursive(self) -> None:
		self._setStaleFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.setStaleFlagRecursive()

	def _clearStaleFlag(self) -> None:
		self.is_stale = False
		logger.debug(f'Clearing STALE flag for {self}')

	def isStale(self) -> bool:
		return self.is_stale

	def _setFirstDrawFlag(self) -> None:
		self.first_draw = True
		logger.debug(f'Setting FIRSTDRAW flag for {self}')

	def setFirstDrawFlagRecursive(self) -> None:
		self._setFirstDrawFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.setFirstDrawFlagRecursive()

	# first_draw flag should only be cleared within its own recomputeRedraw
	def _clearFirstDrawFlag(self) -> None:
		self.first_draw = False
		logger.debug(f'Clearing FIRSTDRAW flag for {self}')

	def isFirstDraw(self) -> bool:
		return self.first_draw

	def setVisibility(self, state:bool) -> None:
		logger.debug(f'Setting visibility for {self} to {state}')
		for visual_name, visual in self.visuals.items():
			if visual is None:
				continue
			visual.visible = state

	def setVisibilityRecursive(self, state) -> None:
		'''Sets the visibility of this asset and all child-assets'''
		self.setVisibility(state)
		for asset in self.assets.values():
			asset.setVisibilityRecursive(state)

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		for asset_name, asset in self.assets.items():
			state[f'asset_{asset_name}'] = asset.prepSerialisation()
		for k,v in self.opts.items():
			state[f'opt_{k}'] = serialiseOption(self.opts[k])
		return state

	def deSerialise(self, state):
		logger.debug(f"Deserialisation of asset {self}")
		for k,v in state.items():
			if 'asset_' in k:
				self.assets[k.removeprefix('asset_')].deSerialise(v)
				continue
			elif 'opt_' in k:
				logger.debug(f'\t{k}:{v}')
				deSerialiseOption(k.removeprefix('opt_'),v,self)
		self.runOptionCallbacks()

	def runOptionCallbacks(self):
		if not self.isActive():
			return
		for opt_str, opt in self.opts.items():
			if opt['callback'] is not None:
				try:
					opt['callback'](opt['value'])
				except NotImplementedError:
					continue

	@abstractmethod
	def _initData(self, *args, **kwargs) -> None:
		'''Initialise data used for drawing this and any child assets
			Any parameters can be passed here'''
		raise NotImplementedError

	@abstractmethod
	def _instantiateAssets(self) -> None:
		'''Create child assets
			pass desired parent to asset at instantiation'''
		raise NotImplementedError

	@abstractmethod
	def _createVisuals(self) -> None:
		'''Create visuals on canvas'''
		raise NotImplementedError

	@abstractmethod
	def _setDefaultOptions(self) -> None:
		''' Set the default options for the visualiser {dict} '''
		raise NotImplementedError

	@abstractmethod
	def setTransform(self, pos:tuple[float,float,float]=(0,0,0), rotation:nptyping.NDArray=np.eye(3)) -> None:
		'''Directly set the linear transform to be applied to the visuals

			Should include the following iteration in the overriding method
			for asset in self.assets.values():
				asset.setTransform()'''
		raise NotImplementedError

	def updateIndex(self, index:int) -> None:
		'''Update the stored curr_index value
			Should include the following iteration in the overriding method
			for asset in self.assets.values():
				asset.updateIndex()
			self.is_stale = True'''
		self.data['curr_index'] = index
		self.setStaleFlagRecursive()
		self._updateIndexChildren(index)

	def _updateIndexChildren(self, index:int) -> None:
		for asset in self.assets.values():
			asset.updateIndex(index)

	def getScreenMouseOverInfo(self) -> dict[str,list]:
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		return mo_info

	def mouseOver(self, index:int) -> None:
		return

	def _listVisuals(self) -> tuple[list, list]:
		keys = [key for key in self.visuals.keys()]
		values = [key for key in self.visuals.values()]
		return keys, values

	def _printVisuals(self) -> None:
		k,v = self._listVisuals()
		print(f"{self.__name__} asset has visuals:")
		for ii, key in enumerate(k):
			print(f"\t{key}-> ref:{v[ii]}")

	def _printFlags(self) -> None:
		print(f'\tactive:{self.isActive()}')
		print(f'\tstale:{self.isStale()}')
		print(f'\tfirst_draw:{self.isFirstDraw()}')

	def _listAssets(self) -> tuple[list, list]:
		keys = [key for key in self.assets.keys()]
		values = [key for key in self.assets.values()]
		return keys, values

	def _printAssets(self) -> None:
		k,v = self._listAssets()
		print(f"{self.__name__} asset has child assets:")
		for ii, key in enumerate(k):
			print(f"\t{key}-> ref:{v[ii]}")

	def _printParent(self,visual_key:str|None=None) -> None:
		print(f"asset {self.data['name']} parent scene:{self.data['v_parent']}")
		if visual_key is not None:
			print(f"\tvisual {visual_key} parent scene:{self.visuals[visual_key].parent}")

	def _printOptions(self) -> None:
		for k,v in self.opts.items():
			print(f'{k}:')
			for k2,v2 in v.items():
				print(f'\t{k2}:{v2}')




class AbstractAsset(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
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
		self._dflt_opts = {}
		self.opts = {}

		# Flag to indicate that this is the first drawing since the asset
		# has been re-instantiated. This generally means that any visuals
		# must be re-created
		self.first_draw = True
		# Flag to indicate that the underlying data of the asset has changed
		# (likely due to a new timestep being displayed), and as such, the
		# positions and transforms of child-assets and visuals must be recomputed
		self.is_stale = False

	##### Viewbox methods
	def _attachToParentView(self) -> None:
		'''Sets all vispy visuals to use the stored parent'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				logger.debug(f"Attaching visual of {self.data['name']} to parent")
				visual.parent = self.data['v_parent']
			elif visual is not None:
				logger.debug(f"Attaching visual of {self.data['name']} to parent")
				for el in visual:
					el.parent = self.data['v_parent']

	def attachToParentViewRecursive(self) -> None:
		'''Sets all nested vispy visuals to use the stored parent'''
		self._attachToParentView()
		for asset in self.assets.values():
			if asset is not None:
				asset.attachToParentViewRecursive()

	def _detachFromParentView(self) -> None:
		'''Sets all vispy visuals to use no parent -> stops rendering'''
		for visual in self.visuals.values():
			if visual is not None and not isinstance(visual, list):
				# single visual
				logger.debug(f"Detaching visual of {self.data['name']} to parent")
				visual.parent = None
			elif visual is not None:
				logger.debug(f"Detaching visual of {self.data['name']} from parent")
				# list of visuals
				for el in visual:
					el.parent = None

	def detachFromParentViewRecursive(self) -> None:
		'''Sets all nested vispy visuals to use no parent -> stops rendering'''
		self._detachFromParentView()

		for asset in self.assets.values():
			asset.detachFromParentViewRecursive()

	def setParentView(self, view:ViewBox) -> None:
		'''Stores the v_parent to the vispy view to use'''
		self.data['v_parent'] = view
		for asset in self.assets.values():
			asset.data['v_parent'] = view

	##### State methods
	def makeActive(self) -> None:
		logger.debug(f"{self.data['name']} being made active.")
		if not self.is_active:
			self.setFirstDrawFlagRecursive()
			self.attachToParentViewRecursive()  # will attach all assets  recursively
		self.setActiveFlagRecursive()

	def makeDormant(self) -> None:
		self.clearActiveFlagRecursive()
		self.setStaleFlagRecursive()
		self.detachFromParentViewRecursive()

	def _setActiveFlag(self) -> None:
		self.is_active = True
		logger.debug(f'Setting ACTIVE flag for {self}')

	def _clearActiveFlag(self) -> None:
		self.is_active = False
		logger.debug(f'Clearing ACTIVE flag for {self}')

	def setActiveFlagRecursive(self) -> None:
		self._setActiveFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.setActiveFlagRecursive()

	def clearActiveFlagRecursive(self) -> None:
		self._clearActiveFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.clearActiveFlagRecursive()

	def isActive(self) -> bool:
		return self.is_active

	def _setStaleFlag(self) -> None:
		self.is_stale = True
		logger.debug(f'Setting STALE flag for {self}')

	def setStaleFlagRecursive(self) -> None:
		self._setStaleFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.setStaleFlagRecursive()

	def _clearStaleFlag(self) -> None:
		logger.debug(f'Clearing STALE flag for {self}')
		self.is_stale = False

	def isStale(self) -> bool:
		return self.is_stale

	def _setFirstDrawFlag(self) -> None:
		logger.debug(f'Setting FIRSTDRAW flag for {self}')
		self.first_draw = True

	def setFirstDrawFlagRecursive(self) -> None:
		self._setFirstDrawFlag()
		for asset in self.assets.values():
			if asset is not None:
				asset.setFirstDrawFlagRecursive()

	# should only be called within its own recomputeRedraw
	def _clearFirstDrawFlag(self) -> None:
		logger.debug(f'Clearing FIRSTDRAW flag for {self}')
		self.first_draw = False

	def isFirstDraw(self) -> bool:
		return self.first_draw

	def setVisibility(self, state:bool) -> None:
		logger.debug(f'Setting visibility for {self} to {state}')
		for visual_name, visual in self.visuals.items():
			if visual is None:
				continue
			visual.visible = state

	def setVisibilityRecursive(self, state:bool) -> None:
		'''Sets the visibility of this asset and all child-assets'''
		self.setVisibility(state)
		for asset in self.assets.values():
			asset.setVisibilityRecursive(state)


	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		for asset_name, asset in self.assets.items():
			state[f'asset_{asset_name}'] = asset.prepSerialisation()
		for k,v in self.opts.items():
			state[f'opt_{k}'] = serialiseOption(self.opts[k])
		return state

	def deSerialise(self, state):
		logger.debug(f"Deserialisation of asset {self}")
		for k,v in state.items():
			if 'asset_' in k:
				self.assets[k.removeprefix('asset_')].deSerialise(v)
				continue
			elif 'opt_' in k:
				logger.debug(f'\t{k}:{v}')
				deSerialiseOption(k.removeprefix('opt_'),v,self)

		self.runOptionCallbacks()

	def runOptionCallbacks(self):
		if not self.isActive():
			return
		for opt_str, opt in self.opts.items():
			if opt['callback'] is not None:
				try:
					opt['callback'](opt['value'])
				except NotImplementedError:
					continue
				except KeyError:
					continue

	@abstractmethod
	def _initData(self, *args, **kwargs):
		'''Initialise data used for drawing this and any child assets
			Any parameters can be passed here'''
		raise NotImplementedError

	@abstractmethod
	def _instantiateAssets(self) -> None:
		'''Create child assets
			pass desired parent to asset at instantiation'''
		raise NotImplementedError

	@abstractmethod
	def _createVisuals(self) -> None:
		'''Create visuals on canvas'''
		raise NotImplementedError

	@abstractmethod
	def _setDefaultOptions(self) -> None:
		''' Set the default options for the visualiser {dict} '''
		raise NotImplementedError

	@abstractmethod
	def recomputeRedraw(self) -> None:
		'''Recompute the asset geometry; apply to child assets and visuals

			Should include the following check at the beginning of the function
			if self.first_draw:
				...
				self.first_draw = False

			Should include the following iteration in the overriding method
			self.subAssetsRecompute()
			self.is_stale = False'''
		raise NotImplementedError

	def _recomputeRedrawChildren(self,pos:tuple[float,float,float]=(0,0,0), rotation:nptyping.NDArray=np.eye(3)) -> None:
		for asset in self.assets.values():
			if isinstance(asset, AbstractAsset):
				asset.recomputeRedraw()
			elif isinstance(asset, AbstractSimpleAsset) or isinstance(asset, AbstractCompoundAsset):
				asset.setTransform(pos=pos, rotation=rotation)

	def updateIndex(self, index:int) -> None:
		'''Update the stored curr_index value
			Should include the following iteration in the overriding method
			for asset in self.assets.values():
				asset.updateIndex()
			self.is_stale = True'''
		self.data['curr_index'] = index
		self.setStaleFlagRecursive()
		self._updateIndexChildren(index)

	def _updateIndexChildren(self, index:int) -> None:
		for asset in self.assets.values():
			asset.updateIndex(index)

	def getScreenMouseOverInfo(self) -> dict[str,list]:
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		return mo_info

	def mouseOver(self, index: int) -> Self:
		return self

	def restoreMouseOver(self) -> None:
		return

	##### helper functions
	def _listVisuals(self) -> tuple[list, list]:
		keys = [key for key in self.visuals.keys()]
		values = [key for key in self.visuals.values()]
		return keys, values

	def _printVisuals(self) -> None:
		k,v = self._listVisuals()
		print(f"{self.__name__} asset has visuals:")
		for ii, key in enumerate(k):
			print(f"\t{key}-> ref:{v[ii]}")

	def _printFlags(self) -> None:
		print(f'\tactive:{self.isActive()}')
		print(f'\tstale:{self.isStale()}')
		print(f'\tfirst_draw:{self.isFirstDraw()}')

	def _listAssets(self) -> tuple[list,list]:
		keys = [key for key in self.assets.keys()]
		values = [key for key in self.assets.values()]
		return keys, values

	def _printAssets(self) -> None:
		k,v = self._listAssets()
		print(f"{self.__name__} asset has child assets:")
		for ii, key in enumerate(k):
			print(f"\t{key}-> ref:{v[ii]}")

	def _printParent(self,visual_key:str|None=None, asset_key:str|None=None) -> None:
		print(f"asset {self.data['name']} parent scene:{self.data['v_parent']}")
		if visual_key is not None:
			print(f"\tvisual {visual_key} parent scene:{self.visuals[visual_key].parent}")
		if asset_key is not None:
			print(f"\tasset {asset_key} parent scene:{self.assets[asset_key].data['v_parent']}")

	def _printOptions(self) -> None:
		for k,v in self.opts.items():
			print(f'{k}:')
			for k2,v2 in v.items():
				print(f'\t{k2}:{v2}')


def serialiseOption(opt_dict:dict[str,Any]) -> dict[str,Any]:
	opt_state = {}
	opt_state['value'] = opt_dict['value']

	# These don't need to be serialised
	# opt_state['type'] = opt_dict['type']
	# opt_state['help'] = opt_dict['help']
	# opt_state['static'] = opt_dict['static']

	# These can't be serialised
	# opt_state['callback'] = opt_dict['callback']
	# opt_state['widget'] = opt_dict['widget']

	return opt_state

def deSerialiseOption(opt_name:str, opt_state:dict[str, Any], asset:AbstractAsset|AbstractCompoundAsset|AbstractSimpleAsset) -> None:
	for k,v in opt_state.items():
		if k not in asset.opts[opt_name].keys():
			continue
		asset.opts[opt_name][k] = v