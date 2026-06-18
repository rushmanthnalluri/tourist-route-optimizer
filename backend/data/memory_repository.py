from typing import List, Dict, Optional, Tuple
from backend.data.repository import AbstractAttractionRepository
from backend.data.attraction_models import AttractionModel
from backend.data.hyderabad_attractions import ATTRACTION_MAP, get_neighbors

class MemoryAttractionRepository(AbstractAttractionRepository):
    def get_all_attractions(self) -> List[AttractionModel]:
        return [AttractionModel(**a.__dict__) for a in ATTRACTION_MAP.values()]

    def get_attraction(self, attraction_id: int) -> Optional[AttractionModel]:
        a = ATTRACTION_MAP.get(attraction_id)
        if a:
            return AttractionModel(**a.__dict__)
        return None

    def get_neighbors(
        self, attraction_id: int
    ) -> List[Tuple[int, float, float, float]]:
        return get_neighbors(attraction_id)

    def get_graph(self) -> Dict[int, List[Tuple[int, float, float, float]]]:
        return {aid: get_neighbors(aid) for aid in ATTRACTION_MAP.keys()}
