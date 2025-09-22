from abc import abstractmethod
import logging

from typing import Any

from vispy import scene

import orbviz.visualiser.assets.base_assets as base_assets

logger = logging.getLogger(__name__)

class BaseCanvas:
	def __init__(self, w:int=800, h:int=600, keys:str='interactive', bgcolor:str='white'):
		pass

	@abstractmethod
	def _buildAssets(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def getActiveAssets(self) -> list[base_assets.AbstractAsset|base_assets.AbstractCompoundAsset|base_assets.AbstractSimpleAsset]:
		raise NotImplementedError()

	@abstractmethod
	def setModel(self, *args, **kwargs) -> None:
		# Can accept any subclass of Base Data Model
		raise NotImplementedError()

	@abstractmethod
	def _modelUpdated(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def updateIndex(self, index:int) -> None:
		raise NotImplementedError()

	@abstractmethod
	def recomputeRedraw(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def setfirstDrawFlags(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def prepSerialisation(self) -> dict[str, Any]:
		raise NotImplementedError()

	@abstractmethod
	def deSerialise(self, state:dict[str, Any]) -> None:
		raise NotImplementedError()


	def getCanvas(self) -> scene.canvas.SceneCanvas:
		if self.canvas is None:
			logger.error('Canvas wrapper:%s does not have a canvas yet.', self)
			raise ValueError(f'Canvas wrapper:{self} does not have a canvas yet.')
		else:
			return self.canvas