"""
Data handler for loading and saving user data to JSON.
"""
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .models import UserData, DEFAULT_PLANT_ID


# Path to user data file
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_FILE = DATA_DIR / "user_data.json"


def ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def get_default_data() -> Dict[str, Any]:
    """Return default user data structure."""
    return {
        "currency_balance": 0,
        "active_plant_id": DEFAULT_PLANT_ID,
        "plant_stages": {DEFAULT_PLANT_ID: 0},
        "pet_custom_names": {},
        "inventory": [],
        "last_login": datetime.now().strftime("%Y-%m-%d")
    }


def load_user_data() -> UserData:
    """Load user data from JSON file, or return default if file doesn't exist."""
    ensure_data_dir()
    
    if not DATA_FILE.exists():
        default_data = get_default_data()
        save_user_data_dict(default_data)
        return UserData(**default_data)
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        default_data = get_default_data()
        if "pet_custom_names" not in data:
            data["pet_custom_names"] = data.get("plant_custom_names", {})
        if "plant_custom_names" in data:
            del data["plant_custom_names"]
        # Migrate old plant_stage to plant_stages / active_plant_id
        if "plant_stages" not in data:
            data["plant_stages"] = {DEFAULT_PLANT_ID: data.get("plant_stage", 0)}
        if "active_plant_id" not in data:
            data["active_plant_id"] = default_data["active_plant_id"]
        if data.get("active_plant_id") == "plant_japanese":
            data["active_plant_id"] = DEFAULT_PLANT_ID
        if "plant_stages" in data and "plant_japanese" in data["plant_stages"]:
            stages = data["plant_stages"]
            stages[DEFAULT_PLANT_ID] = stages.get(DEFAULT_PLANT_ID, stages["plant_japanese"])
            del stages["plant_japanese"]
        if "plant_stage" in data:
            del data["plant_stage"]
        for key in default_data.keys():
            if key not in data:
                data[key] = default_data[key]
        
        return UserData(**data)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # If file is corrupted, return default
        print(f"Error loading user data: {e}. Using default data.")
        default_data = get_default_data()
        return UserData(**default_data)


def save_user_data(user_data: UserData) -> None:
    """Save user data to JSON file."""
    ensure_data_dir()
    
    data_dict = {
        "currency_balance": user_data.currency_balance,
        "active_plant_id": user_data.active_plant_id,
        "plant_stages": user_data.plant_stages,
        "pet_custom_names": user_data.pet_custom_names,
        "inventory": user_data.inventory,
        "last_login": user_data.last_login
    }
    
    save_user_data_dict(data_dict)


def save_user_data_dict(data: Dict[str, Any]) -> None:
    """Save data dictionary to JSON file."""
    ensure_data_dir()
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
