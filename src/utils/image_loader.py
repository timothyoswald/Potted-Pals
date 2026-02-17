"""
Image loading utility using Pillow.
Plant assets live in assets/plants/{folder}/{folder}_stage_N.png; each folder may have a different number of stages.
"""
from pathlib import Path
from typing import Dict, Optional
from PIL import Image, ImageTk


ASSETS_DIR = (Path(__file__).resolve().parent.parent.parent / "assets").resolve()
PLANTS_DIR = (ASSETS_DIR / "plants").resolve()
DEWDROP_ICON_MAX = 24  # match heading text size (~16pt); aspect ratio preserved


def load_dewdrop_icon_pil() -> Optional[Image.Image]:
    """Load and resize the water_drop icon for balance display. Preserves aspect ratio. Returns PIL Image or None."""
    path = ASSETS_DIR / "icons" / "water_drop.png"
    if not path.exists():
        return None
    try:
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        if not w or not h:
            return img
        scale = min(DEWDROP_ICON_MAX / w, DEWDROP_ICON_MAX / h, 1.0)
        new_w, new_h = int(w * scale), int(h * scale)
        if new_w < 1:
            new_w = 1
        if new_h < 1:
            new_h = 1
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Error loading dewdrop icon: {e}")
        return None

# Cache max stage per folder (folder_name -> int)
_max_stage_cache: Dict[str, int] = {}


def load_image(image_path: Path, size: Optional[tuple] = None) -> Optional[ImageTk.PhotoImage]:
    """
    Load an image from the given path and optionally resize it.
    
    Args:
        image_path: Path to the image file
        size: Optional tuple (width, height) for resizing
        
    Returns:
        PhotoImage object or None if loading fails
    """
    try:
        full_path = ASSETS_DIR / image_path if not image_path.is_absolute() else image_path
        
        if not full_path.exists():
            print(f"Image not found: {full_path}")
            return None
        
        img = Image.open(full_path)
        
        # Convert RGBA to RGB if needed for better compatibility
        if img.mode == 'RGBA':
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None


def get_plant_folder(plant_id: str) -> str:
    """Return the folder name for this plant_id (e.g. plant_rose -> rose). Unknown folders fall back to shrub."""
    if plant_id.startswith("plant_"):
        folder = plant_id[6:]
    else:
        folder = plant_id
    if not (PLANTS_DIR / folder).is_dir():
        return "shrub"
    return folder


def get_max_stage(plant_id: str) -> int:
    """Return the highest stage number (0-based) available for this plant by scanning the folder."""
    folder = get_plant_folder(plant_id)
    if folder in _max_stage_cache:
        return _max_stage_cache[folder]
    folder_path = PLANTS_DIR / folder
    if not folder_path.is_dir():
        _max_stage_cache[folder] = 0
        return 0
    prefix = f"{folder}_stage_"
    max_n = -1
    for f in folder_path.iterdir():
        if f.suffix.lower() in (".png", ".jpg") and f.stem.startswith(prefix):
            rest = f.stem[len(prefix) :]
            if rest.isdigit():
                max_n = max(max_n, int(rest))
            elif "_" in rest and rest.split("_")[0].isdigit():
                max_n = max(max_n, int(rest.split("_")[0]))
    _max_stage_cache[folder] = max(0, max_n)
    return _max_stage_cache[folder]


def get_plant_image_path(plant_id: str, stage: int) -> Path:
    """Get the path to a plant stage image under plants/{folder}/{folder}_stage_N.png."""
    folder = get_plant_folder(plant_id)
    max_s = get_max_stage(plant_id)
    stage = max(0, min(max_s, int(stage)))
    name = f"{folder}_stage_{stage}"
    for ext in (".png", ".jpg"):
        path = Path("plants") / folder / f"{name}{ext}"
        if (ASSETS_DIR / path).exists():
            return path
    return Path("plants") / folder / f"{name}.png"
