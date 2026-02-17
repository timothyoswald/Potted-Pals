"""
Data models for Sprout & Study application.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# Hardcoded tasks for Phase 2: (id, label, dewdrops)
TASKS: List[Tuple[str, str, int]] = [
    ("went_to_class", "Went to a class (5)", 5),
    ("ate_a_meal", "Ate a meal (10)", 10),
    ("drank_water", "Drank one bottle of water (10)", 10),
    ("cooked_a_meal", "Cooked a meal (20)", 20),
    ("did_laundry", "Did laundry (30)", 30),
    ("studied_30min", "Studied/Worked 30 minutes (50)", 50),
    ("slept_8hours", "Slept for 8 or more hours (100)", 100),
    ("submitted_homework", "Submitted a homework assignment (100)", 100),
    ("took_a_test", "Took a test (200)", 200),
]


DEFAULT_PLANT_ID = "plant_shrub"


@dataclass
class UserData:
    """User data structure for persistence."""
    currency_balance: int = 0
    active_plant_id: str = DEFAULT_PLANT_ID  # which plant is displayed
    plant_stages: Dict[str, int] = field(default_factory=lambda: {DEFAULT_PLANT_ID: 0})  # stage 0-5 per plant
    pet_custom_names: Dict[str, str] = field(default_factory=dict)  # pet_id -> custom display name
    inventory: List[str] = field(default_factory=list)
    last_login: str = ""  # ISO date string (YYYY-MM-DD)


@dataclass
class ShopItem:
    """Shop item structure. If upgrade_stage is set, buying it sets plant_stage (no inventory)."""
    id: str
    name: str
    cost: int
    description: str = ""
    upgrade_stage: Optional[int] = None  # 1-5: buying this sets plant_stage to this value
