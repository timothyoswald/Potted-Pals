"""
Main window for the Sprout & Study application.
"""
import random
import sys
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import ImageTk

from ..data_handler import load_user_data, save_user_data, UserData
from ..shop_manager import (
    get_plants_owned,
    get_plant_display_name_for_user,
    get_pets_owned,
    get_pet_display_name_for_user,
)
from ..utils.image_loader import get_plant_image_path, load_dewdrop_icon_pil
from ..utils.pet_sprites import (
    load_pet_sprites,
    list_pets,
    flip_frames,
    PET_TRANSPARENT_KEY_HEX,
    PET_TRANSPARENT_KEY_RGB,
)
from .styles import COLORS, FONTS, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from .task_dialog import TaskDialog
from .shop_window import ShopWindow
from .grow_window import GrowWindow

PET_SCALE = 2.5
PET_MAX_DISPLAY_LARGE = 100  # person and cat (default in pet_sprites is 80)
PET_SPEED = 2.0
# Cat sprite is offset within its cell when facing left/right; shift tooltip so it stays above the head
CAT_TOOLTIP_OFFSET_X = 14
PET_ANIM_MS = 120
PET_STATE_MIN_SEC = 2.0
PET_STATE_MAX_SEC = 5.0


class MainWindow:
    """Main application window displaying the plant and currency."""
    
    def __init__(self):
        # Set appearance mode and theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Potted Pals")
        self.root.geometry(f"{WINDOW_DEFAULT_WIDTH}x{WINDOW_DEFAULT_HEIGHT}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Configure window background
        self.root.configure(bg=COLORS["cream"])
        
        # Load user data (plant stage is upgraded via shop only)
        self.user_data: UserData = load_user_data()

        # Plant image reference (keep ref to prevent garbage collection)
        self.plant_image: Optional[ctk.CTkImage] = None
        self._plant_pil_image: Optional[object] = None
        # macOS: render plant + pets on a Tk canvas so PNG alpha works
        self._scene_canvas: Optional[tk.Canvas] = None
        self._plant_canvas_img_id: Optional[int] = None
        self._plant_photo_ref: Optional[ImageTk.PhotoImage] = None

        # Pets: list of {sprites, sprites_left, window, label, photo_ref, x, y, state, frame_idx, direction, vx, vy, cell_w, cell_h, state_after_id}
        self._pets: List[Dict[str, Any]] = []
        self._pet_after_id: Optional[str] = None
        self._pets_initialized: bool = False
        self._popup_count: int = 0
        self._popup_windows: List[Any] = []
        self._dragging_pet: Optional[Dict[str, Any]] = None
        self._drag_offset_x: float = 0.0
        self._drag_offset_y: float = 0.0

        # Create UI
        self._create_ui()
        
        # Update display with loaded data
        self._update_display()
    
    def _create_ui(self):
        """Create the main UI components."""
        # Main container
        main_frame = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["cream"],
            corner_radius=0
        )
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Action buttons at the bottom, centered
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(side="bottom", pady=12, padx=12, fill="x")
        btn_inner = ctk.CTkFrame(button_frame, fg_color="transparent")
        btn_inner.pack(expand=True, anchor="center")

        self.add_task_button = ctk.CTkButton(
            btn_inner,
            text="+ Task",
            font=FONTS["default"],
            fg_color=COLORS["sage_green"],
            hover_color=COLORS["muted_teal"],
            text_color="white",
            height=30,
            width=64,
            command=self._on_add_task_clicked
        )
        self.add_task_button.pack(side="left", padx=2)

        self.shop_button = ctk.CTkButton(
            btn_inner,
            text="Shop",
            font=FONTS["default"],
            fg_color=COLORS["warm_beige"],
            hover_color=COLORS["soft_pink"],
            text_color=COLORS["dark_text"],
            height=30,
            width=64,
            command=self._on_shop_clicked
        )
        self.shop_button.pack(side="left", padx=2)

        self.grow_button = ctk.CTkButton(
            btn_inner,
            text="Grow",
            font=FONTS["default"],
            fg_color=COLORS["sage_green"],
            hover_color=COLORS["muted_teal"],
            text_color="white",
            height=30,
            width=64,
            command=self._on_grow_clicked
        )
        self.grow_button.pack(side="left", padx=2)
        
        # Top row: balance (Dewdrops + icon) and plant switcher, centered
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.pack(pady=10, padx=12, fill="x")
        top_inner = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_inner.pack(expand=True)

        self._dewdrop_pil = load_dewdrop_icon_pil()
        self._dewdrop_image = None
        if self._dewdrop_pil:
            self._dewdrop_image = ctk.CTkImage(
                light_image=self._dewdrop_pil,
                dark_image=self._dewdrop_pil,
                size=(self._dewdrop_pil.width, self._dewdrop_pil.height),
            )
        balance_frame = ctk.CTkFrame(top_inner, fg_color="transparent")
        balance_frame.pack(anchor="center")
        balance_frame.grid_columnconfigure(0, weight=0)
        balance_frame.grid_columnconfigure(1, weight=0)
        col = 0
        if self._dewdrop_image:
            dewdrop_lbl = ctk.CTkLabel(
                balance_frame,
                text="",
                image=self._dewdrop_image,
                font=FONTS["heading"],
                text_color=COLORS["dark_text"],
            )
            dewdrop_lbl.grid(row=0, column=0, padx=(0, 8), sticky="")
            col = 1
        self.currency_label = ctk.CTkLabel(
            balance_frame,
            text="0 Dewdrops",
            font=FONTS["heading"],
            text_color=COLORS["dark_text"],
        )
        self.currency_label.grid(row=0, column=col, sticky="")

        # Plant switcher: button shows current plant; click opens popup to pick another
        self.plant_switcher_btn = ctk.CTkButton(
            top_inner,
            text=get_plant_display_name_for_user(self.user_data.active_plant_id, self.user_data),
            font=FONTS["small"],
            fg_color=COLORS["warm_beige"],
            hover_color=COLORS["soft_pink"],
            text_color=COLORS["dark_text"],
            width=120,
            height=24,
            command=self._open_plant_switcher,
        )
        self.plant_switcher_btn.pack(anchor="center", pady=(4, 0))
        
        # Plant display area (center) - fills space between currency and buttons
        self.plant_frame = ctk.CTkFrame(
            main_frame,
            fg_color="transparent"
        )
        self.plant_frame.pack(fill="both", expand=True, padx=12, pady=6)

        if sys.platform == "darwin":
            # macOS: use a Tk canvas for reliable RGBA transparency
            self._scene_canvas = tk.Canvas(
                self.plant_frame,
                bg=COLORS["cream"],
                highlightthickness=0,
                bd=0,
            )
            self._scene_canvas.pack(fill="both", expand=True)
        else:
            # Plant image label (Windows/Linux)
            self.plant_label = ctk.CTkLabel(
                self.plant_frame,
                text="",
                fg_color="transparent"
            )
            self.plant_label.pack(expand=True)

        # Global bindings for pet drag (so motion/release work when mouse leaves pet window)
        # Bind on the underlying tk widget for CustomTkinter compatibility
        root_tk = self.root.winfo_toplevel()
        root_tk.bind("<B1-Motion>", self._on_pet_drag_motion)
        root_tk.bind("<ButtonRelease-1>", self._on_pet_drag_release)

        # Pet: init deferred so main window is laid out and winfo_rootx/y are valid
        self.root.after(150, self._init_pet)

    def _init_pet(self) -> None:
        """Load owned pets only; create a window per pet, random spawn, start tick."""
        available = list_pets()
        pet_ids = [p for p in get_pets_owned(self.user_data) if p in available]
        root_tk = self.root.winfo_toplevel()
        for pet_id in pet_ids:
            self._add_pet(pet_id, root_tk)
        if self._pets:
            self._pet_schedule_tick()
        self._pets_initialized = True

    def _add_pet(self, pet_id: str, root_tk: tk.Tk) -> None:
        """Create one pet and add to _pets. Caller ensures pet_id is in list_pets()."""
        kwargs = {"pet_id": pet_id, "scale": PET_SCALE, "background_rgb": None}
        if pet_id in ("person", "cat"):
            kwargs["max_display_size"] = PET_MAX_DISPLAY_LARGE
        raw = load_pet_sprites(**kwargs)
        if not raw:
            return
        sprites = {k: list(v) for k, v in raw.items()}
        sprites_left = {k: flip_frames(v) for k, v in raw.items()}
        first_frames = next((v for v in sprites.values() if v), None)
        if not first_frames:
            return
        cell_w, cell_h = first_frames[0].size

        # macOS: draw pets on the scene canvas (alpha transparency works here)
        if sys.platform == "darwin":
            if self._scene_canvas is None:
                return
            pet = {
                "pet_id": pet_id,
                "sprites": sprites,
                "sprites_left": sprites_left,
                "canvas_image_id": None,
                "photo_ref": None,
                "x": None,
                "y": None,
                "spawned": False,
                "state": "idle",
                "frame_idx": 0,
                "direction": 1,
                "vx": 0.0,
                "vy": 0.0,
                "cell_w": cell_w,
                "cell_h": cell_h,
                "state_after_id": None,
                "tooltip_after_id": None,
                "tooltip": None,
            }
            self._pets.append(pet)
            self._pet_show_frame_one(pet)
            # Bind hover/drag to the canvas item once it exists
            if pet.get("canvas_image_id") is not None:
                item_id = pet["canvas_image_id"]
                self._scene_canvas.tag_bind(item_id, "<Enter>", lambda e, p=pet: self._pet_tooltip_schedule_show(p))
                self._scene_canvas.tag_bind(item_id, "<Leave>", lambda e, p=pet: self._pet_tooltip_hide(p))
                self._scene_canvas.tag_bind(item_id, "<ButtonPress-1>", lambda e, p=pet: (self._on_pet_drag_start(e, p), "break")[1])
            self._pet_schedule_state_change_one(pet)
            return

        win = tk.Toplevel(root_tk)
        win.overrideredirect(True)
        is_macos = sys.platform == "darwin"
        if is_macos:
            # macOS: use transparent window - -transparentcolor doesn't work on macOS
            # With transparent window, RGBA images will show transparency properly
            try:
                win.wm_attributes("-transparent", True)
            except tk.TclError:
                pass
            # Window background - with transparent window, this becomes transparent
            # Use cream to match plant area background so transparent areas blend correctly
            win.configure(bg=COLORS["cream"])
            # Use Canvas for better RGBA transparency support on macOS
            # Canvas background matches plant area - transparent pixels in RGBA will show through
            canvas = tk.Canvas(
                win,
                width=cell_w,
                height=cell_h,
                bg=COLORS["cream"],
                highlightthickness=0,
                bd=0
            )
            canvas.pack()
            label = None  # Not using Label on macOS
            canvas_image_id = None
        else:
            # Windows: use color-key transparency with composited images
            win.configure(bg=PET_TRANSPARENT_KEY_HEX)
            try:
                win.wm_attributes("-transparentcolor", PET_TRANSPARENT_KEY_HEX)
            except tk.TclError:
                pass
            label_bg = PET_TRANSPARENT_KEY_HEX
            label = tk.Label(win, image=None, bg=label_bg, bd=0, highlightthickness=0)
            label.pack()
            canvas = None  # Not used on Windows
            canvas_image_id = None  # Not used on Windows
        win.withdraw()
        pet = {
            "pet_id": pet_id,
            "sprites": sprites,
            "sprites_left": sprites_left,
            "window": win,
            "label": label,
            "canvas": canvas,
            "canvas_image_id": canvas_image_id,
            "photo_ref": None,
            "x": None,
            "y": None,
            "spawned": False,
            "state": "idle",
            "frame_idx": 0,
            "direction": 1,
            "vx": 0.0,
            "vy": 0.0,
            "cell_w": cell_w,
            "cell_h": cell_h,
            "state_after_id": None,
            "tooltip_after_id": None,
            "tooltip": None,
            "is_macos": is_macos,
        }
        win.bind("<Enter>", lambda e, p=pet: self._pet_tooltip_schedule_show(p))
        win.bind("<Leave>", lambda e, p=pet: self._pet_tooltip_hide(p))
        if label:
            label.bind("<Enter>", lambda e, p=pet: self._pet_tooltip_schedule_show(p))
            label.bind("<Leave>", lambda e, p=pet: self._pet_tooltip_hide(p))
        if canvas:
            canvas.bind("<Enter>", lambda e, p=pet: self._pet_tooltip_schedule_show(p))
            canvas.bind("<Leave>", lambda e, p=pet: self._pet_tooltip_hide(p))
        def start_drag(e, p=pet):
            self._on_pet_drag_start(e, p)
            return "break"
        def drag_motion(e, p=pet):
            self._on_pet_drag_motion(e)
            return "break"
        win.bind("<ButtonPress-1>", start_drag)
        if label:
            label.bind("<ButtonPress-1>", start_drag)
            label.bind("<B1-Motion>", drag_motion)
        if canvas:
            canvas.bind("<ButtonPress-1>", start_drag)
            canvas.bind("<B1-Motion>", drag_motion)
        self._pets.append(pet)
        self._pet_show_frame_one(pet)
        self._pet_schedule_state_change_one(pet)

    def _refresh_pets(self) -> None:
        """Add any newly purchased pets that are not yet in _pets (e.g. after shop purchase)."""
        available = list_pets()
        owned = get_pets_owned(self.user_data)
        current_ids = [p["pet_id"] for p in self._pets]
        root_tk = self.root.winfo_toplevel()
        added = False
        for pet_id in owned:
            if pet_id in available and pet_id not in current_ids:
                self._add_pet(pet_id, root_tk)
                added = True
        if added and self._pets and self._pet_after_id is None:
            self._pet_schedule_tick()

    def _pet_tooltip_schedule_show(self, pet: Dict[str, Any]) -> None:
        """Schedule showing the pet name tooltip after a short delay."""
        if pet.get("tooltip_after_id") is not None:
            self.root.after_cancel(pet["tooltip_after_id"])
        pet["tooltip_after_id"] = self.root.after(400, lambda: self._pet_tooltip_show(pet))

    def _pet_tooltip_position(self, pet: Dict[str, Any], tip_w: int, tip_h: int) -> Optional[tuple]:
        """Return (tip_x, tip_y) to center the tooltip above the pet, or None if not available."""
        if not pet.get("spawned") or pet.get("x") is None or pet.get("y") is None:
            return None
        try:
            root_x = self.plant_frame.winfo_rootx()
            root_y = self.plant_frame.winfo_rooty()
        except tk.TclError:
            return None
        pet_left = root_x + int(pet["x"])
        pet_top = root_y + int(pet["y"])
        cell_w = pet["cell_w"]
        cell_h = pet["cell_h"]
        tip_x = pet_left + (cell_w - tip_w) // 2
        if pet.get("pet_id") == "cat":
            direction = pet.get("direction", 1)
            if direction == -1:
                tip_x -= CAT_TOOLTIP_OFFSET_X
            else:
                tip_x += CAT_TOOLTIP_OFFSET_X
        tip_y = pet_top - tip_h - 4
        if tip_y < 0:
            tip_y = pet_top + cell_h + 4
        return (tip_x, tip_y)

    def _pet_tooltip_show(self, pet: Dict[str, Any]) -> None:
        """Show a tooltip with the pet's name centered above the pet."""
        pet["tooltip_after_id"] = None
        self._pet_tooltip_hide(pet)
        if not pet.get("spawned") or pet.get("x") is None or pet.get("y") is None:
            return
        name = get_pet_display_name_for_user(pet["pet_id"], self.user_data)
        # macOS canvas pets don't have their own Toplevel window
        parent = self.root.winfo_toplevel()
        if "window" in pet:
            try:
                parent = pet["window"].winfo_toplevel()
            except Exception:
                parent = self.root.winfo_toplevel()
        tip = tk.Toplevel(parent)
        tip.overrideredirect(True)
        tip.wm_attributes("-topmost", True)
        tip.configure(bg=COLORS["dark_text"], bd=0)
        lbl = tk.Label(
            tip,
            text=name,
            font=("Comfortaa", 10),
            fg=COLORS["cream"],
            bg=COLORS["dark_text"],
            padx=6,
            pady=2,
            bd=0,
        )
        lbl.pack()
        tip.update_idletasks()
        tw, th = tip.winfo_reqwidth(), tip.winfo_reqheight()
        pos = self._pet_tooltip_position(pet, tw, th)
        if pos is not None:
            tip.geometry(f"+{pos[0]}+{pos[1]}")
        pet["tooltip"] = tip

    def _pet_tooltip_reposition(self, pet: Dict[str, Any]) -> None:
        """Update tooltip position to follow the pet (call each tick while tooltip is visible)."""
        tip = pet.get("tooltip")
        if tip is None:
            return
        try:
            if not tip.winfo_exists():
                pet["tooltip"] = None
                return
            tw = tip.winfo_reqwidth()
            th = tip.winfo_reqheight()
        except tk.TclError:
            return
        pos = self._pet_tooltip_position(pet, tw, th)
        if pos is not None:
            tip.geometry(f"+{pos[0]}+{pos[1]}")

    def _pet_tooltip_hide(self, pet: Dict[str, Any]) -> None:
        """Cancel scheduled tooltip and hide/destroy the tooltip window."""
        if pet.get("tooltip_after_id") is not None:
            try:
                self.root.after_cancel(pet["tooltip_after_id"])
            except (tk.TclError, ValueError):
                pass
            pet["tooltip_after_id"] = None
        if pet.get("tooltip") is not None:
            try:
                pet["tooltip"].destroy()
            except tk.TclError:
                pass
            pet["tooltip"] = None

    def _on_pet_drag_start(self, event: tk.Event, pet: Dict[str, Any]) -> None:
        """Start dragging this pet (mouse down on pet)."""
        if not pet.get("spawned") or pet.get("x") is None or pet.get("y") is None:
            return
        self._pet_tooltip_hide(pet)
        try:
            root_x = self.plant_frame.winfo_rootx()
            root_y = self.plant_frame.winfo_rooty()
            # Get mouse position in screen coordinates
            if hasattr(event, 'x_root') and hasattr(event, 'y_root'):
                mouse_x = event.x_root
                mouse_y = event.y_root
            else:
                # Fallback: use widget coordinates + widget position
                widget = event.widget
                mouse_x = widget.winfo_rootx() + event.x
                mouse_y = widget.winfo_rooty() + event.y
            frame_x = mouse_x - root_x
            frame_y = mouse_y - root_y
            self._drag_offset_x = frame_x - pet["x"]
            self._drag_offset_y = frame_y - pet["y"]
            self._dragging_pet = pet
        except (tk.TclError, AttributeError):
            return

    def _on_pet_drag_motion(self, event: tk.Event) -> None:
        """Update pet position while dragging; clamp to plant area bounds."""
        if self._dragging_pet is None:
            return
        pet = self._dragging_pet
        try:
            root_x = self.plant_frame.winfo_rootx()
            root_y = self.plant_frame.winfo_rooty()
            # Get mouse position in screen coordinates
            if hasattr(event, 'x_root') and hasattr(event, 'y_root'):
                mouse_x = event.x_root
                mouse_y = event.y_root
            else:
                # Fallback: use widget coordinates + widget position
                widget = event.widget
                mouse_x = widget.winfo_rootx() + event.x
                mouse_y = widget.winfo_rooty() + event.y
            frame_x = mouse_x - root_x
            frame_y = mouse_y - root_y
            new_x = frame_x - self._drag_offset_x
            new_y = frame_y - self._drag_offset_y
            min_x, max_x, min_y, max_y = self._pet_bounds(pet["cell_w"], pet["cell_h"])
            pet["x"] = max(min_x, min(max_x, new_x))
            pet["y"] = max(min_y, min(max_y, new_y))
            self._pet_place_one(pet)
            self._pet_tooltip_reposition(pet)
        except (tk.TclError, AttributeError):
            return

    def _on_pet_drag_release(self, event: tk.Event) -> None:
        """Stop dragging (mouse up)."""
        self._dragging_pet = None

    def _pet_bounds(self, cell_w: int, cell_h: int) -> tuple:
        """Return (min_x, max_x, min_y, max_y) for movement inside plant_frame."""
        try:
            w = self.plant_frame.winfo_width()
            h = self.plant_frame.winfo_height()
            if w < 50 or h < 50:
                rw = self.root.winfo_width()
                rh = self.root.winfo_height()
                w = max(w, rw - 80 if rw > 0 else 300)
                h = max(h, rh - 180 if rh > 0 else 280)
            w = max(w, 100)
            h = max(h, 150)
        except Exception:
            w, h = 300, 280
        min_x, max_x = 0, max(0, w - cell_w - 1)
        min_y, max_y = 0, max(0, h - cell_h - 1)
        if min_x > max_x:
            max_x = min_x
        if min_y > max_y:
            max_y = min_y
        return (min_x, max_x, min_y, max_y)

    def _pet_place_one(self, pet: Dict[str, Any]) -> None:
        """Position one pet. On macOS pets are canvas items; otherwise Toplevel windows."""
        if not pet.get("spawned"):
            return
        # macOS: canvas-rendered pets
        if sys.platform == "darwin" and self._scene_canvas is not None and "canvas_image_id" in pet:
            item_id = pet.get("canvas_image_id")
            if item_id is None or pet.get("x") is None or pet.get("y") is None:
                return
            x = float(pet["x"]) + pet["cell_w"] / 2.0
            y = float(pet["y"]) + pet["cell_h"] / 2.0
            try:
                self._scene_canvas.coords(item_id, x, y)
            except tk.TclError:
                return
            return
        try:
            root_x = self.plant_frame.winfo_rootx()
            root_y = self.plant_frame.winfo_rooty()
        except tk.TclError:
            return
        x = root_x + int(pet["x"])
        y = root_y + int(pet["y"])
        pet["window"].geometry(f"{pet['cell_w']}x{pet['cell_h']}+{x}+{y}")
        pet["window"].deiconify()
        if self._popup_count > 0 and self._popup_windows:
            top_popup = None
            for w in reversed(self._popup_windows):
                try:
                    if w.winfo_exists():
                        top_popup = w
                        break
                except (tk.TclError, AttributeError):
                    continue
            if top_popup is not None:
                try:
                    pet["window"].lower(top_popup)
                except tk.TclError:
                    pass
        else:
            pet["window"].lift()

    def _pet_show_frame_one(self, pet: Dict[str, Any]) -> None:
        """Set one pet's label image. Run sprites only when moving (vx or vy != 0); reflect when moving left."""
        state = pet["state"]
        vx, vy = pet.get("vx", 0), pet.get("vy", 0)
        is_moving = abs(vx) > 0.01 or abs(vy) > 0.01
        if state == "walk" and not is_moving:
            state = "idle"
        face_left = pet["direction"] == -1
        if pet.get("pet_id") == "cat":
            face_left = not face_left
        sprites = pet["sprites_left"] if face_left else pet["sprites"]
        frames = sprites.get(state)
        if not frames:
            return
        idx = pet["frame_idx"] % len(frames)
        pil_img = frames[idx]
        # macOS: canvas-rendered pets keep RGBA so alpha transparency works
        if sys.platform == "darwin" and self._scene_canvas is not None and "canvas_image_id" in pet:
            if pil_img.mode != "RGBA":
                pil_img = pil_img.convert("RGBA")
            pet["photo_ref"] = ImageTk.PhotoImage(pil_img)
            if pet.get("canvas_image_id") is None:
                try:
                    pet["canvas_image_id"] = self._scene_canvas.create_image(
                        pet["cell_w"] // 2,
                        pet["cell_h"] // 2,
                        image=pet["photo_ref"],
                        anchor="center",
                    )
                except tk.TclError:
                    return
            else:
                try:
                    self._scene_canvas.itemconfigure(pet["canvas_image_id"], image=pet["photo_ref"])
                except tk.TclError:
                    return
            return

        # Windows/other: existing Toplevel+Label rendering (color-key)
        if pet.get("is_macos", False):
            # Legacy macOS window-pet path (kept for safety; should not be used now)
            if pil_img.mode != "RGBA":
                pil_img = pil_img.convert("RGBA")
            pet["photo_ref"] = ImageTk.PhotoImage(pil_img)
            label = pet.get("label")
            if label:
                label.configure(image=pet["photo_ref"])
            return

        if pil_img.mode == "RGBA":
            from PIL import Image as PILImage
            rgb_img = PILImage.new("RGB", pil_img.size, PET_TRANSPARENT_KEY_RGB)
            rgb_img.paste(pil_img, mask=pil_img.split()[3])
            pil_img = rgb_img
        pet["photo_ref"] = ImageTk.PhotoImage(pil_img)
        label = pet.get("label")
        if label:
            label.configure(image=pet["photo_ref"])

    def _pet_schedule_tick(self) -> None:
        if self._pet_after_id is not None:
            self.root.after_cancel(self._pet_after_id)
        if not self._pets:
            return
        self._pet_after_id = self.root.after(PET_ANIM_MS, self._pet_tick)

    def _pet_tick(self) -> None:
        self._pet_after_id = None
        if not self._pets:
            return
        self.root.update_idletasks()
        for pet in self._pets:
            cw, ch = pet["cell_w"], pet["cell_h"]
            min_x, max_x, min_y, max_y = self._pet_bounds(cw, ch)
            if not pet.get("spawned"):
                pet["x"] = float(random.randint(min_x, max(max_x, min_x)))
                pet["y"] = float(random.randint(min_y, max(max_y, min_y)))
                pet["spawned"] = True
            elif pet is self._dragging_pet:
                pass
            else:
                vx, vy = pet["vx"], pet["vy"]
                if abs(vx) > 0.01 or abs(vy) > 0.01:
                    pet["x"] += vx
                    pet["y"] += vy
                    if pet["x"] <= min_x:
                        pet["x"] = min_x
                        pet["vx"] = abs(pet["vx"])
                    elif pet["x"] >= max_x:
                        pet["x"] = max_x
                        pet["vx"] = -abs(pet["vx"])
                    if pet["y"] <= min_y:
                        pet["y"] = min_y
                        pet["vy"] = abs(pet["vy"])
                    elif pet["y"] >= max_y:
                        pet["y"] = max_y
                        pet["vy"] = -abs(pet["vy"])
                    if pet["vx"] < 0:
                        pet["direction"] = -1
                    elif pet["vx"] > 0:
                        pet["direction"] = 1
                pet["x"] = max(min_x, min(max_x, pet["x"]))
                pet["y"] = max(min_y, min(max_y, pet["y"]))
            frames = pet["sprites"].get(pet["state"]) or []
            if frames:
                pet["frame_idx"] = (pet["frame_idx"] + 1) % len(frames)
            self._pet_show_frame_one(pet)
            self._pet_place_one(pet)
            self._pet_tooltip_reposition(pet)
        self._pet_schedule_tick()

    def _pet_schedule_state_change_one(self, pet: Dict[str, Any]) -> None:
        if pet.get("state_after_id") is not None:
            self.root.after_cancel(pet["state_after_id"])
        delay_ms = int(1000 * (PET_STATE_MIN_SEC + random.random() * (PET_STATE_MAX_SEC - PET_STATE_MIN_SEC)))
        pet["state_after_id"] = self.root.after(delay_ms, lambda p=pet: self._pet_state_change_one(p))

    def _pet_state_change_one(self, pet: Dict[str, Any]) -> None:
        pet["state_after_id"] = None
        pet["state"] = random.choice(["idle", "walk", "sit"])
        pet["frame_idx"] = 0
        if pet["state"] == "walk":
            pet["vx"] = PET_SPEED * random.choice((1, -1))
            pet["vy"] = PET_SPEED * random.choice((1, -1))
            pet["direction"] = -1 if pet["vx"] < 0 else 1
        else:
            pet["vx"] = 0.0
            pet["vy"] = 0.0
        self._pet_show_frame_one(pet)
        self._pet_schedule_state_change_one(pet)
    
    def _on_popup_opened(self, popup_win: Any = None) -> None:
        """Keep pets visible but below the menu window so they don't appear on top of it."""
        self._popup_count += 1
        if popup_win is not None:
            self._popup_windows.append(popup_win)
        for pet in self._pets:
            try:
                if popup_win is not None:
                    pet["window"].lower(popup_win)
                else:
                    pet["window"].lower()
            except tk.TclError:
                pass

    def _on_popup_closed(self, popup_win: Any = None) -> None:
        """Popup closed; stop forcing pets to stay behind it."""
        self._popup_count = max(0, self._popup_count - 1)
        if popup_win is not None and popup_win in self._popup_windows:
            self._popup_windows.remove(popup_win)

    def _open_plant_switcher(self) -> None:
        """Open a small popup to choose which plant to display."""
        popup = ctk.CTkToplevel(self.root)
        self._on_popup_opened(popup)
        popup.title("Choose plant")
        popup.geometry("280x280")
        popup.configure(fg_color=COLORS["cream"])
        popup.transient(self.root)

        def close_plant_switcher():
            self._on_popup_closed(popup)
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", close_plant_switcher)
        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        for pid in get_plants_owned(self.user_data):
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=4)
            name = get_plant_display_name_for_user(pid, self.user_data)
            btn = ctk.CTkButton(
                row,
                text=name,
                font=FONTS["default"],
                fg_color=COLORS["warm_beige"] if pid == self.user_data.active_plant_id else COLORS["sage_green"],
                hover_color=COLORS["soft_pink"],
                text_color=COLORS["dark_text"],
                command=lambda p=pid, w=popup: self._select_plant_and_close(p, w),
            )
            btn.pack(side="left", fill="x", expand=True)

    def _select_plant_and_close(self, plant_id: str, popup: ctk.CTkToplevel) -> None:
        """Set active plant, save, close popup, refresh main window."""
        self.user_data.active_plant_id = plant_id
        save_user_data(self.user_data)
        self._on_popup_closed(popup)
        popup.destroy()
        self._update_display()

    def _update_display(self):
        """Update currency, plant switcher button text, plant image, and add any newly bought pets."""
        self.currency_label.configure(text=f"{self.user_data.currency_balance} Dewdrops")
        self.plant_switcher_btn.configure(text=get_plant_display_name_for_user(self.user_data.active_plant_id, self.user_data))
        self._update_plant_image()
        if self._pets_initialized:
            self._refresh_pets()

    def _update_plant_image(self):
        """Load and display the plant stage image."""
        stage = self.user_data.plant_stages.get(self.user_data.active_plant_id, 0)
        assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"

        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        if window_width < 100:
            window_width = WINDOW_DEFAULT_WIDTH
        if window_height < 100:
            window_height = WINDOW_DEFAULT_HEIGHT
        padding_h = 48
        reserved_vertical = 168
        max_width = window_width - padding_h
        max_height = window_height - reserved_vertical
        max_width = max(120, min(max_width, 240))
        max_height = max(140, min(max_height, 240))

        plant_id = self.user_data.active_plant_id
        image_path = get_plant_image_path(plant_id, stage)
        full_path = assets_dir / image_path

        try:
            if not full_path.exists():
                if sys.platform == "darwin" and self._scene_canvas is not None:
                    # Clear plant image on canvas
                    if self._plant_canvas_img_id is not None:
                        try:
                            self._scene_canvas.delete(self._plant_canvas_img_id)
                        except tk.TclError:
                            pass
                        self._plant_canvas_img_id = None
                else:
                    self.plant_label.configure(image="", text=f"Image not found:\n{image_path}")
                return
            from PIL import Image

            img = Image.open(full_path).convert("RGBA")
            w, h = img.size
            if w and h:
                scale = min(max_width / w, max_height / h, 1.0)
                disp_w, disp_h = int(w * scale), int(h * scale)
                img = img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
            self._plant_pil_image = img
            if sys.platform == "darwin" and self._scene_canvas is not None:
                # Draw plant on canvas so pets can be RGBA on top
                self._plant_photo_ref = ImageTk.PhotoImage(img)
                self._scene_canvas.update_idletasks()
                cw = max(1, self._scene_canvas.winfo_width())
                ch = max(1, self._scene_canvas.winfo_height())
                x = cw // 2
                y = ch // 2
                if self._plant_canvas_img_id is None:
                    self._plant_canvas_img_id = self._scene_canvas.create_image(
                        x, y, image=self._plant_photo_ref, anchor="center"
                    )
                    # Ensure plant is behind pets
                    self._scene_canvas.tag_lower(self._plant_canvas_img_id)
                else:
                    self._scene_canvas.itemconfigure(self._plant_canvas_img_id, image=self._plant_photo_ref)
                    self._scene_canvas.coords(self._plant_canvas_img_id, x, y)
                    self._scene_canvas.tag_lower(self._plant_canvas_img_id)
            else:
                self.plant_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(img.width, img.height),
                )
                self.plant_label.configure(image=self.plant_image, text="")
        except Exception as e:
            print(f"Error loading plant image: {e}")
            if sys.platform == "darwin":
                return
            self.plant_label.configure(image="", text="Error loading image")
    
    def _on_add_task_clicked(self):
        """Handle Add Task button click: show task dialog, add dewdrops, update growth, save, refresh."""
        result = TaskDialog(
            self.root,
            on_open=self._on_popup_opened,
            on_close=self._on_popup_closed,
        ).show()
        if result is None:
            return
        task_id, dewdrops = result
        self.user_data.currency_balance += dewdrops
        save_user_data(self.user_data)
        self._update_display()
    
    def _on_shop_clicked(self):
        """Open shop (plants only)."""
        ShopWindow(
            self.root,
            self.user_data,
            self._update_display,
            on_open=self._on_popup_opened,
            on_close=self._on_popup_closed,
        ).show()

    def _on_grow_clicked(self):
        """Open grow window (stage upgrades only)."""
        GrowWindow(
            self.root,
            self.user_data,
            self._update_display,
            on_open=self._on_popup_opened,
            on_close=self._on_popup_closed,
        ).show()
    
    def run(self):
        """Start the application main loop."""
        # Bind window resize to update plant image
        self.root.bind('<Configure>', self._on_window_resize)
        self.root.mainloop()
    
    def _on_window_resize(self, event):
        """Handle window resize to update plant image size and clamp pet position."""
        if event.widget == self.root:
            self._update_plant_image()
            for pet in self._pets:
                if not pet.get("spawned"):
                    continue
                min_x, max_x, min_y, max_y = self._pet_bounds(pet["cell_w"], pet["cell_h"])
                pet["x"] = max(min_x, min(max_x, pet["x"]))
                pet["y"] = max(min_y, min(max_y, pet["y"]))
                self._pet_place_one(pet)
