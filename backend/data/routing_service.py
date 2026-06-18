import httpx
import logging
from typing import Dict, List, Tuple
from backend.data.hyderabad_attractions import ATTRACTIONS, GRAPH

logger = logging.getLogger(__name__)

class RoutingService:
    async def fetch_live_traffic(self) -> bool:
        """
        Fetches a 25x25 routing matrix from OSRM public API and updates the global GRAPH.
        Returns True if successful, False otherwise.
        """
        # Build coordinates string for OSRM: "lon1,lat1;lon2,lat2;..."
        coords_list = []
        for a in ATTRACTIONS:
            coords_list.append(f"{a.lng},{a.lat}")
        
        coords_str = ";".join(coords_list)
        url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=duration,distance"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                if data.get("code") != "Ok":
                    logger.error(f"OSRM returned non-Ok code: {data.get('code')}")
                    return False

                distances = data["distances"] # in meters
                durations = data["durations"] # in seconds

                new_graph: Dict[int, List[Tuple[int, float, float, float]]] = {
                    a.id: [] for a in ATTRACTIONS
                }

                auto_cost_per_km = 12.0

                for i, src in enumerate(ATTRACTIONS):
                    for j, dst in enumerate(ATTRACTIONS):
                        if i == j:
                            continue
                        
                        dist_m = distances[i][j]
                        dur_s = durations[i][j]

                        # If OSRM can't find a route, it might return None or 0. 
                        # Fallback to straight line if something goes wrong.
                        if dist_m is None or dur_s is None:
                            continue

                        road_km = round(dist_m / 1000.0, 2)
                        time_min = round(dur_s / 60.0, 1)
                        cost_inr = round(road_km * auto_cost_per_km, 0)

                        new_graph[src.id].append((dst.id, road_km, time_min, cost_inr))

                # Update the global GRAPH in place so existing imports in co2_search.py see the new values
                GRAPH.clear()
                GRAPH.update(new_graph)
                logger.info("Successfully updated global GRAPH with live OSRM traffic data.")
                return True

        except Exception as e:
            logger.error(f"Failed to fetch live traffic from OSRM: {e}")
            return False

routing_service = RoutingService()
