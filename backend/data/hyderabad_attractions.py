from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Attraction:
    id: int
    name: str
    lat: float
    lng: float
    entry_cost: float
    duration_min: int
    category: str
    rating: float
    opening_time: int
    closing_time: int
    description: str
    crowd_probs: Dict[str, float] = field(default_factory=dict)
    weather_sensitivity: float = 0.3

    def is_open(self, hour: int) -> bool:
        return self.opening_time <= hour < self.closing_time

    def __repr__(self) -> str:
        return f"Attraction({self.id}: {self.name})"


ATTRACTIONS: List[Attraction] = [
    Attraction(
        id=0,
        name="Charminar",
        lat=17.3616,
        lng=78.4747,
        entry_cost=25,
        duration_min=60,
        category="historical",
        rating=4.5,
        opening_time=9,
        closing_time=17,
        description="Iconic 16th-century mosque and monument, symbol of Hyderabad.",
        crowd_probs={"morning": 0.4, "afternoon": 0.8, "evening": 0.7},
        weather_sensitivity=0.8,
    ),
    Attraction(
        id=1,
        name="Golconda Fort",
        lat=17.3833,
        lng=78.4011,
        entry_cost=50,
        duration_min=120,
        category="historical",
        rating=4.6,
        opening_time=8,
        closing_time=17,
        description="Medieval fortress with acoustic wonders and panoramic views.",
        crowd_probs={"morning": 0.3, "afternoon": 0.6, "evening": 0.5},
        weather_sensitivity=0.8,
    ),
    Attraction(
        id=2,
        name="Hussain Sagar Lake",
        lat=17.4239,
        lng=78.4738,
        entry_cost=20,
        duration_min=90,
        category="nature",
        rating=4.4,
        opening_time=8,
        closing_time=22,
        description="Heart-shaped lake built in 1562, famous for the Buddha statue and boating.",
        crowd_probs={"morning": 0.2, "afternoon": 0.5, "evening": 0.9},
        weather_sensitivity=0.9,
    ),
    Attraction(
        id=3,
        name="Salar Jung Museum",
        lat=17.3713,
        lng=78.4804,
        entry_cost=50,
        duration_min=180,
        category="museum",
        rating=4.7,
        opening_time=10,
        closing_time=17,
        description="One of the largest art museums in the world, housing antiquities.",
        crowd_probs={"morning": 0.6, "afternoon": 0.8, "evening": 0.2},
        weather_sensitivity=0.1,
    ),
    Attraction(
        id=4,
        name="Birla Mandir",
        lat=17.4062,
        lng=78.4691,
        entry_cost=0,
        duration_min=60,
        category="religious",
        rating=4.8,
        opening_time=7,
        closing_time=20,
        description="Stunning white marble Hindu temple on a 280-feet high hill.",
        crowd_probs={"morning": 0.8, "afternoon": 0.4, "evening": 0.7},
        weather_sensitivity=0.4,
    ),
    Attraction(
        id=5,
        name="Ramoji Film City",
        lat=17.2543,
        lng=78.6808,
        entry_cost=1200,
        duration_min=360,
        category="entertainment",
        rating=4.5,
        opening_time=9,
        closing_time=18,
        description="World's largest integrated film city and theme park.",
        crowd_probs={"morning": 0.7, "afternoon": 0.9, "evening": 0.8},
        weather_sensitivity=0.8,
    ),
    Attraction(
        id=6,
        name="Nehru Zoological Park",
        lat=17.3508,
        lng=78.4503,
        entry_cost=60,
        duration_min=240,
        category="nature",
        rating=4.3,
        opening_time=8,
        closing_time=17,
        description="380-acre zoo housing over 1,500 species of animals.",
        crowd_probs={"morning": 0.7, "afternoon": 0.8, "evening": 0.3},
        weather_sensitivity=0.85,
    ),
    Attraction(
        id=7,
        name="Lumbini Park",
        lat=17.4116,
        lng=78.4735,
        entry_cost=20,
        duration_min=60,
        category="nature",
        rating=4.2,
        opening_time=9,
        closing_time=21,
        description="Small urban park offering musical fountains and lake views.",
        crowd_probs={"morning": 0.2, "afternoon": 0.5, "evening": 0.8},
        weather_sensitivity=0.9,
    ),
    Attraction(
        id=8,
        name="Birla Science Museum",
        lat=17.4057,
        lng=78.4695,
        entry_cost=150,
        duration_min=120,
        category="museum",
        rating=4.4,
        opening_time=10,
        closing_time=20,
        description="Science center featuring a planetarium and interactive exhibits.",
        crowd_probs={"morning": 0.4, "afternoon": 0.7, "evening": 0.5},
        weather_sensitivity=0.1,
    ),
    Attraction(
        id=9,
        name="Chowmahalla Palace",
        lat=17.3582,
        lng=78.4716,
        entry_cost=100,
        duration_min=120,
        category="historical",
        rating=4.6,
        opening_time=10,
        closing_time=17,
        description="Grand palace of the Nizams, renowned for its courtyards and vintage car collection.",
        crowd_probs={"morning": 0.3, "afternoon": 0.7, "evening": 0.4},
        weather_sensitivity=0.4,
    ),
    Attraction(
        id=10,
        name="Qutb Shahi Tombs",
        lat=17.3962,
        lng=78.3966,
        entry_cost=20,
        duration_min=90,
        category="historical",
        rating=4.5,
        opening_time=9,
        closing_time=17,
        description="Magnificent domed tombs of the seven Qutb Shahi rulers.",
        crowd_probs={"morning": 0.3, "afternoon": 0.6, "evening": 0.4},
        weather_sensitivity=0.6,
    ),
    Attraction(
        id=11,
        name="Taramati Baradari",
        lat=17.3824,
        lng=78.3752,
        entry_cost=0,
        duration_min=60,
        category="historical",
        rating=4.3,
        opening_time=10,
        closing_time=18,
        description="Historical sarai featuring legendary acoustics.",
        crowd_probs={"morning": 0.2, "afternoon": 0.4, "evening": 0.7},
        weather_sensitivity=0.5,
    ),
    Attraction(
        id=12,
        name="Snow World",
        lat=17.4143,
        lng=78.4806,
        entry_cost=600,
        duration_min=120,
        category="entertainment",
        rating=4.1,
        opening_time=11,
        closing_time=21,
        description="Indoor snow theme park with ice slides and snow play.",
        crowd_probs={"morning": 0.5, "afternoon": 0.8, "evening": 0.6},
        weather_sensitivity=0.0,
    ),
    Attraction(
        id=13,
        name="NTR Gardens",
        lat=17.4124,
        lng=78.4697,
        entry_cost=15,
        duration_min=90,
        category="nature",
        rating=4.4,
        opening_time=14,
        closing_time=20,
        description="Lush gardens featuring a toy train, cascading waterfalls, and cafes.",
        crowd_probs={"morning": 0.1, "afternoon": 0.6, "evening": 0.9},
        weather_sensitivity=0.85,
    ),
    Attraction(
        id=14,
        name="Shilparamam",
        lat=17.4526,
        lng=78.3809,
        entry_cost=60,
        duration_min=120,
        category="cultural",
        rating=4.5,
        opening_time=10,
        closing_time=20,
        description="Traditional crafts village showcasing Indian arts, crafts, and culture.",
        crowd_probs={"morning": 0.3, "afternoon": 0.6, "evening": 0.8},
        weather_sensitivity=0.7,
    ),
    Attraction(
        id=15,
        name="Hitech City / Cyber Towers",
        lat=17.4504,
        lng=78.3808,
        entry_cost=0,
        duration_min=30,
        category="modern",
        rating=4.3,
        opening_time=0,
        closing_time=24,
        description="The heart of Hyderabad's IT industry, striking modern architecture.",
        crowd_probs={"morning": 0.8, "afternoon": 0.5, "evening": 0.7},
        weather_sensitivity=0.2,
    ),
    Attraction(
        id=16,
        name="Mecca Masjid",
        lat=17.3605,
        lng=78.4736,
        entry_cost=0,
        duration_min=45,
        category="religious",
        rating=4.6,
        opening_time=4,
        closing_time=21,
        description="One of the largest mosques in India, adjacent to Charminar.",
        crowd_probs={"morning": 0.5, "afternoon": 0.8, "evening": 0.4},
        weather_sensitivity=0.6,
    ),
    Attraction(
        id=17,
        name="Tank Bund",
        lat=17.4244,
        lng=78.4744,
        entry_cost=0,
        duration_min=60,
        category="nature",
        rating=4.4,
        opening_time=0,
        closing_time=24,
        description="Promenade along Hussain Sagar Lake featuring statues of famous personalities.",
        crowd_probs={"morning": 0.4, "afternoon": 0.5, "evening": 0.9},
        weather_sensitivity=0.9,
    ),
    Attraction(
        id=18,
        name="Laad Bazaar",
        lat=17.3619,
        lng=78.4729,
        entry_cost=0,
        duration_min=90,
        category="shopping",
        rating=4.5,
        opening_time=11,
        closing_time=23,
        description="Historic bustling market famous for traditional bangles and pearls.",
        crowd_probs={"morning": 0.2, "afternoon": 0.7, "evening": 1.0},
        weather_sensitivity=0.6,
    ),
    Attraction(
        id=19,
        name="Lotus Pond",
        lat=17.4187,
        lng=78.4116,
        entry_cost=0,
        duration_min=60,
        category="nature",
        rating=4.2,
        opening_time=6,
        closing_time=18,
        description="Quiet, scenic pond surrounded by lush greenery, perfect for walks.",
        crowd_probs={"morning": 0.6, "afternoon": 0.3, "evening": 0.7},
        weather_sensitivity=0.9,
    ),
    Attraction(
        id=20,
        name="Paigah Tombs",
        lat=17.3456,
        lng=78.4975,
        entry_cost=0,
        duration_min=45,
        category="historical",
        rating=4.3,
        opening_time=10,
        closing_time=17,
        description="Intricately carved tombs known for architectural excellence and stucco work.",
        crowd_probs={"morning": 0.3, "afternoon": 0.5, "evening": 0.2},
        weather_sensitivity=0.3,
    ),
    Attraction(
        id=21,
        name="KBR National Park",
        lat=17.4237,
        lng=78.4231,
        entry_cost=30,
        duration_min=120,
        category="nature",
        rating=4.5,
        opening_time=5,
        closing_time=18,
        description="Vast national park offering rich flora, fauna, and trekking trails.",
        crowd_probs={"morning": 0.9, "afternoon": 0.2, "evening": 0.6},
        weather_sensitivity=0.95,
    ),
    Attraction(
        id=22,
        name="Jalavihar Water Park",
        lat=17.4265,
        lng=78.4682,
        entry_cost=400,
        duration_min=180,
        category="entertainment",
        rating=4.2,
        opening_time=11,
        closing_time=19,
        description="Family-friendly water park featuring slides, wave pools, and rides.",
        crowd_probs={"morning": 0.4, "afternoon": 0.9, "evening": 0.5},
        weather_sensitivity=1.0,
    ),
    Attraction(
        id=23,
        name="Sudha Cars Museum",
        lat=17.3562,
        lng=78.4552,
        entry_cost=50,
        duration_min=60,
        category="museum",
        rating=4.1,
        opening_time=9,
        closing_time=18,
        description="Quirky museum showcasing handmade vehicles in bizarre shapes.",
        crowd_probs={"morning": 0.3, "afternoon": 0.7, "evening": 0.4},
        weather_sensitivity=0.1,
    ),
    Attraction(
        id=24,
        name="Falaknuma Palace",
        lat=17.3323,
        lng=78.4674,
        entry_cost=0,
        duration_min=120,
        category="historical",
        rating=4.8,
        opening_time=10,
        closing_time=17,
        description="Luxurious palace now functioning as a high-end heritage hotel.",
        crowd_probs={"morning": 0.2, "afternoon": 0.5, "evening": 0.6},
        weather_sensitivity=0.2,
    ),
]

ATTRACTION_MAP: Dict[int, Attraction] = {a.id: a for a in ATTRACTIONS}


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    a = max(0.0, min(1.0, a))
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_graph(
    attractions: List[Attraction],
    max_road_km: float = 15.0,
    road_factor: float = 1.35,
    avg_speed_kmh: float = 20.0,
    auto_cost_per_km: float = 12.0,
) -> Dict[int, List[Tuple[int, float, float, float]]]:
    if avg_speed_kmh <= 0:
        raise ValueError(
            "avg_speed_kmh must be strictly positive to avoid division by zero"
        )

    graph: Dict[int, List[Tuple[int, float, float, float]]] = {
        a.id: [] for a in attractions
    }
    for i, src in enumerate(attractions):
        for j, dst in enumerate(attractions):
            if i >= j:
                continue
            sl_dist = haversine(src.lat, src.lng, dst.lat, dst.lng)
            if sl_dist <= max_road_km:
                road_km = round(sl_dist * road_factor, 2)
                time_min = round((road_km / avg_speed_kmh) * 60, 1)
                cost_inr = round(road_km * auto_cost_per_km, 0)
                graph[src.id].append((dst.id, road_km, time_min, cost_inr))
                graph[dst.id].append((src.id, road_km, time_min, cost_inr))
    return graph


GRAPH: Dict[int, List[Tuple[int, float, float, float]]] = build_graph(ATTRACTIONS)


def straight_line_distance(a_id: int, b_id: int) -> float:
    a, b = ATTRACTION_MAP[a_id], ATTRACTION_MAP[b_id]
    return haversine(a.lat, a.lng, b.lat, b.lng)


def get_neighbors(node_id: int) -> List[Tuple[int, float, float, float]]:
    return GRAPH.get(node_id, [])


def get_attraction(a_id: int) -> Attraction:
    return ATTRACTION_MAP[a_id]


if __name__ == "__main__":
    print("=" * 60)
    print("HYDERABAD TOURIST ATTRACTIONS — KNOWLEDGE BASE")
    print("=" * 60)
    for a in ATTRACTIONS:
        status = f"{a.opening_time:02d}:00–{a.closing_time:02d}:00"
        print(
            f"  [{a.id:2d}] {a.name:<30} | Rs{a.entry_cost:<5} | {a.duration_min} min | "
            f"{a.category:<15} | *{a.rating} | {status}"
        )

    print("\n" + "=" * 60)
    print("GRAPH CONNECTIVITY SUMMARY")
    print("=" * 60)
    total_edges = sum(len(v) for v in GRAPH.values()) // 2
    print(f"  Nodes: {len(ATTRACTIONS)} attractions")
    print(f"  Edges: {total_edges} road connections")
    for a in ATTRACTIONS:
        nbrs = GRAPH[a.id]
        nbr_names = [ATTRACTION_MAP[n[0]].name for n in nbrs[:3]]
        print(
            f"  {a.name:<30} -> {len(nbrs)} neighbors  (e.g. {', '.join(nbr_names)}...)"
        )

    print("\n" + "=" * 60)
    print("SAMPLE DISTANCES")
    print("=" * 60)
    pairs = [(0, 1), (0, 16), (1, 10), (2, 7), (5, 0)]
    for a_id, b_id in pairs:
        d = straight_line_distance(a_id, b_id)
        a, b = ATTRACTION_MAP[a_id], ATTRACTION_MAP[b_id]
        print(f"  {a.name:<25} <-> {b.name:<25} : {d:.2f} km (straight-line)")
