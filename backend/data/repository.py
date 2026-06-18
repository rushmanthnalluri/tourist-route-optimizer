from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from backend.data.attraction_models import AttractionModel


class AbstractAttractionRepository(ABC):
    @abstractmethod
    def get_all_attractions(self) -> List[AttractionModel]:
        pass

    @abstractmethod
    def get_attraction(self, attraction_id: int) -> Optional[AttractionModel]:
        pass

    @abstractmethod
    def get_neighbors(
        self, attraction_id: int
    ) -> List[Tuple[int, float, float, float]]:
        pass

    @abstractmethod
    def get_graph(self) -> Dict[int, List[Tuple[int, float, float, float]]]:
        pass
