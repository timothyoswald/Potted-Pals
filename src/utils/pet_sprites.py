"""
Pet sprite loader for assets/pets/{pet_id}/{Action}/ frame images.
Format: assets/pets/{pet_id}/{Action}/__*_NNN.png (e.g. Idle, Run, Sit).
Actions are mapped: Idle->idle, Run->walk, Sit->sit. Sprites face right; flip for left-facing.
For transparency: Windows uses color-key (magenta), macOS uses RGBA with transparent window.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from .image_loader import ASSETS_DIR

PETS_DIR = (ASSETS_DIR / "pets").resolve()

# Transparent key for Toplevel wm_attributes
PET_TRANSPARENT_KEY_RGB: Tuple[int, int, int] = (255, 0, 255)
PET_TRANSPARENT_KEY_HEX: str = "#ff00ff"

# Folder name -> internal state key (Idle, Run, Sit are standard)
ACTION_MAP = {"Idle": "idle", "Run": "walk", "Sit": "sit"}

# Cap so pet never fills the window (cat/person assets can be large)
MAX_PET_DISPLAY = 80


def list_pets() -> List[str]:
    """Return pet ids (folder names) in assets/pets, e.g. ['cat', 'person']."""
    if not PETS_DIR.is_dir():
        return []
    return sorted(
        p.name for p in PETS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )


def _composite_onto_bg(rgba: Image.Image, bg_rgb: Tuple[int, int, int]) -> Image.Image:
    """Composite RGBA onto opaque background; alpha > 128 = opaque for clean transparent key."""
    bg = Image.new("RGB", rgba.size, bg_rgb)
    alpha = rgba.split()[3]
    mask = alpha.point(lambda p: 255 if p > 128 else 0, mode="1")
    bg.paste(rgba.convert("RGB"), mask=mask)
    return bg


def _cap_to_max_size(img: Image.Image, max_side: int) -> Image.Image:
    """Scale down image so the longer side is at most max_side; preserve aspect ratio."""
    w, h = img.size
    if w <= max_side and h <= max_side:
        return img
    scale = max_side / max(w, h)
    new_size = (int(w * scale), int(h * scale))
    if new_size[0] < 1:
        new_size = (1, max(1, int(h * scale)))
    if new_size[1] < 1:
        new_size = (max(1, int(w * scale)), 1)
    return img.resize(new_size, Image.Resampling.LANCZOS)


def load_pet_sprites(
    pet_id: Optional[str] = None,
    scale: float = 2.5,
    background_rgb: Optional[Tuple[int, int, int]] = None,
    max_display_size: int = MAX_PET_DISPLAY,
) -> Optional[Dict[str, List[Image.Image]]]:
    """
    Load frames for one pet from assets/pets/{pet_id}/{Action}/.
    pet_id: folder name (e.g. 'person', 'cat'). If None, uses default from list_pets() (prefers "person").
    Frames are scaled, then capped so the longer side is at most max_display_size, then composited.
    Returns {"idle": [...], "walk": [...], "sit": [...]} with at least idle and walk, or None.
    """
    if background_rgb is None:
        background_rgb = PET_TRANSPARENT_KEY_RGB
    if pet_id is None:
        pets = list_pets()
        if not pets:
            return None
        pet_id = "person" if "person" in pets else pets[0]
    pet_dir = PETS_DIR / pet_id
    if not pet_dir.is_dir():
        return None
    try:
        result: Dict[str, List[Image.Image]] = {}
        action_dirs = sorted(p for p in pet_dir.iterdir() if p.is_dir())
        for action_dir in action_dirs:
            action_name = action_dir.name
            internal_key = ACTION_MAP.get(action_name, action_name.lower())
            paths = sorted(action_dir.glob("*.png"))
            if not paths:
                continue
            frames = []
            for path in paths:
                img = Image.open(path).convert("RGBA")
                w, h = img.size
                if scale != 1.0:
                    new_size = (int(w * scale), int(h * scale))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                img = _cap_to_max_size(img, max_display_size)
                # Composite RGBA onto color key background for consistent behavior on all platforms
                # This ensures transparency works via color-key transparency
                frames.append(_composite_onto_bg(img, background_rgb))
            if frames:
                result[internal_key] = frames
        if "idle" not in result or "walk" not in result:
            return None
        if "sit" not in result:
            result["sit"] = list(result["idle"])
        return result
    except Exception as e:
        print(f"Error loading pet sprites for {pet_id}: {e}")
        return None


def pet_display_size(scale: float = 2.5, pet_id: Optional[str] = None) -> Tuple[int, int]:
    """
    Return (width, height) in pixels for displayed pet frames.
    Uses first frame of first available action; if pet not loaded, returns (int(24*scale), int(24*scale)).
    """
    loaded = load_pet_sprites(pet_id=pet_id, scale=scale, background_rgb=PET_TRANSPARENT_KEY_RGB)
    if loaded:
        for frames in loaded.values():
            if frames:
                return frames[0].size
    return (int(24 * scale), int(24 * scale))


def flip_frames(frames: List[Image.Image]) -> List[Image.Image]:
    """Return left-right flipped copies (for left-facing movement)."""
    return [f.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for f in frames]
