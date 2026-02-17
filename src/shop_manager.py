"""
Shop: plants and pets. Stage upgrades live in a separate Grow UI.
"""
from typing import List, Optional

from .models import ShopItem, UserData, DEFAULT_PLANT_ID
from .utils.image_loader import get_max_stage


# Plants (names match folder: baby_cactus -> Baby Cactus)
SHOP_ITEMS: List[ShopItem] = [
    ShopItem(id="plant_baby_cactus", name="Baby Cactus", cost=100, description=""),
    ShopItem(id="plant_clover", name="Clover", cost=200, description=""),
    ShopItem(id="plant_rose", name="Rose", cost=300, description=""),
    ShopItem(id="plant_cherry_blossom", name="Cherry Blossom", cost=500, description=""),
    ShopItem(id="plant_strawberry", name="Strawberry", cost=1000, description=""),
]

# Pets (id prefix pet_; name for display)
SHOP_PET_ITEMS: List[ShopItem] = [
    ShopItem(id="pet_person", name="Person", cost=250, description=""),
    ShopItem(id="pet_mushroom", name="Mushroom", cost=500, description=""),
    ShopItem(id="pet_cat", name="Cat", cost=750, description=""),
    ShopItem(id="pet_slime", name="Slime", cost=1000, description=""),
]


def get_shop_items() -> List[ShopItem]:
    """Return all shop items (plants and pets). For sectioned UI use get_shop_plant_items / get_shop_pet_items."""
    return get_shop_plant_items() + get_shop_pet_items()


def get_shop_plant_items() -> List[ShopItem]:
    """Return plant shop items only."""
    return SHOP_ITEMS


def get_shop_pet_items() -> List[ShopItem]:
    """Return pet shop items only."""
    return SHOP_PET_ITEMS


def get_item(item_id: str) -> Optional[ShopItem]:
    """Return the shop item with the given id (plant or pet), or None."""
    for item in SHOP_PET_ITEMS + SHOP_ITEMS:
        if item.id == item_id:
            return item
    return None


def get_stage_upgrade_items(plant_id: str) -> List[ShopItem]:
    """Return stage upgrade items for this plant (stages 1 through max_stage for its folder)."""
    max_s = get_max_stage(plant_id)
    items: List[ShopItem] = []
    for n in range(1, max_s + 1):
        name = f"Grow to Stage {n}"
        cost = 100 * n
        items.append(
            ShopItem(id=f"upgrade_stage_{n}", name=name, cost=cost, description="", upgrade_stage=n)
        )
    return items




def get_upgrade_item(item_id: str, plant_id: str) -> Optional[ShopItem]:
    """Return the stage upgrade item with the given id for this plant, or None."""
    for item in get_stage_upgrade_items(plant_id):
        if item.id == item_id:
            return item
    return None


def get_plants_owned(user_data: UserData) -> List[str]:
    """Return list of plant ids the user has (default plant + purchased from shop)."""
    owned = [DEFAULT_PLANT_ID]
    for item_id in user_data.inventory:
        if item_id.startswith("plant_"):
            owned.append(item_id)
    return owned


def get_pets_owned(user_data: UserData) -> List[str]:
    """Return list of pet ids the user has bought (e.g. ['person', 'cat'] from inventory 'pet_person', 'pet_cat')."""
    return [item_id[4:] for item_id in user_data.inventory if item_id.startswith("pet_")]


def get_plant_display_name(plant_id: str) -> str:
    """Default display name from plant id (e.g. plant_baby_cactus -> Baby Cactus)."""
    item = get_item(plant_id)
    if item:
        return item.name
    if plant_id.startswith("plant_"):
        return plant_id[6:].replace("_", " ").title()
    return plant_id.replace("_", " ").title()


def get_plant_display_name_for_user(plant_id: str, user_data: UserData) -> str:
    """Display name for UI (plants use default names only)."""
    return get_plant_display_name(plant_id)


def get_pet_display_name(pet_id: str) -> str:
    """Default display name from pet id (e.g. person -> Person)."""
    item = get_item(f"pet_{pet_id}")
    if item:
        return item.name
    return pet_id.replace("_", " ").title()


def get_pet_display_name_for_user(pet_id: str, user_data: UserData) -> str:
    """Display name for UI: custom name if set, otherwise default."""
    custom = user_data.pet_custom_names.get(pet_id, "").strip()
    return custom if custom else get_pet_display_name(pet_id)


def _active_plant_stage(user_data: UserData) -> int:
    """Current stage of the active plant."""
    return user_data.plant_stages.get(user_data.active_plant_id, 0)


def can_afford(user_data: UserData, item_id: str) -> bool:
    """True if user can buy this shop item (enough dewdrops, not already owned)."""
    item = get_item(item_id)
    if item is None:
        return False
    if item_id in user_data.inventory:
        return False
    return user_data.currency_balance >= item.cost


def can_afford_upgrade(user_data: UserData, item: ShopItem) -> bool:
    """True if user can buy this stage upgrade for the active plant."""
    if item.upgrade_stage is None:
        return False
    if user_data.currency_balance < item.cost:
        return False
    return _active_plant_stage(user_data) == item.upgrade_stage - 1


def already_has_upgrade(user_data: UserData, item: ShopItem) -> bool:
    """True if the active plant is already at or past this upgrade stage."""
    if item.upgrade_stage is None:
        return False
    return _active_plant_stage(user_data) >= item.upgrade_stage


def purchase(user_data: UserData, item_id: str) -> bool:
    """If affordable and not owned: deduct cost, add to inventory; for plants only, init stage 0."""
    if not can_afford(user_data, item_id):
        return False
    item = get_item(item_id)
    if item is None:
        return False
    user_data.currency_balance -= item.cost
    user_data.inventory.append(item_id)
    if item_id.startswith("plant_"):
        user_data.plant_stages[item_id] = 0
    return True


def purchase_upgrade(user_data: UserData, item: ShopItem) -> bool:
    """Deduct cost and set the active plant's stage to item.upgrade_stage."""
    if item.upgrade_stage is None or not can_afford_upgrade(user_data, item):
        return False
    user_data.currency_balance -= item.cost
    pid = user_data.active_plant_id
    user_data.plant_stages[pid] = item.upgrade_stage
    return True
