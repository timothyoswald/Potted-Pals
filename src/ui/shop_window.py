"""
Shop window: list of items, purchase with dewdrops, inventory tracked.
"""
import customtkinter as ctk
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from ..data_handler import save_user_data
from ..models import UserData
from ..shop_manager import (
    get_shop_plant_items,
    get_shop_pet_items,
    get_item,
    can_afford,
    purchase,
    get_pets_owned,
    get_pet_display_name,
    get_pet_display_name_for_user,
)
from ..utils.image_loader import load_dewdrop_icon_pil
from .styles import COLORS, FONTS
from .rename_dialog import RenamePlantDialog

# Button width for price (e.g. "500" fits)
PRICE_BTN_WIDTH = 52
ROW_PADY = 4


class ShopWindow:
    """Toplevel shop: item name + price button (grayed when unavailable)."""

    def __init__(
        self,
        parent: ctk.CTk,
        user_data: UserData,
        on_purchase: Callable[[], None],
        on_open: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        self.parent = parent
        self.user_data = user_data
        self.on_purchase = on_purchase
        self.on_open = on_open
        self.on_close = on_close
        self._win: Optional[ctk.CTkToplevel] = None
        self._balance_label: Optional[ctk.CTkLabel] = None
        self._item_rows: List[Tuple[ctk.CTkLabel, ctk.CTkButton, str]] = []  # (name_lbl, price_btn, item_id)

    def show(self) -> None:
        """Show the shop window (non-blocking)."""
        self._win = ctk.CTkToplevel(self.parent)
        self._win.title("Shop")
        self._win.geometry("320x480")
        self._win.minsize(280, 360)
        self._win.configure(fg_color=COLORS["cream"])
        self._win.transient(self.parent)
        if self.on_open:
            self.on_open(self._win)

        content = ctk.CTkFrame(self._win, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=16)

        dewdrop_pil = load_dewdrop_icon_pil()
        dewdrop_ctk = None
        if dewdrop_pil:
            dewdrop_ctk = ctk.CTkImage(
                light_image=dewdrop_pil,
                dark_image=dewdrop_pil,
                size=(dewdrop_pil.width, dewdrop_pil.height),
            )
            self._dewdrop_pil_ref = dewdrop_pil
        balance_frame = ctk.CTkFrame(content, fg_color="transparent")
        balance_frame.pack(anchor="w", pady=(0, 14))
        balance_frame.grid_columnconfigure(0, weight=0)
        balance_frame.grid_columnconfigure(1, weight=0)
        if dewdrop_ctk:
            ctk.CTkLabel(
                balance_frame,
                text="",
                image=dewdrop_ctk,
                font=FONTS["heading"],
                text_color=COLORS["dark_text"],
            ).grid(row=0, column=0, padx=(0, 8), sticky="")
        self._balance_label = ctk.CTkLabel(
            balance_frame,
            text=f"{self.user_data.currency_balance} Dewdrops",
            font=FONTS["heading"],
            text_color=COLORS["dark_text"],
        )
        self._balance_label.grid(row=0, column=1, sticky="")

        scroll = ctk.CTkScrollableFrame(content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._item_rows.clear()
        self._your_pet_rows: List[Tuple[str, ctk.CTkLabel]] = []

        your_pets = get_pets_owned(self.user_data)
        if your_pets:
            your_pets_label = ctk.CTkLabel(
                scroll,
                text="Your pets",
                font=FONTS["heading"],
                text_color=COLORS["dark_text"],
            )
            your_pets_label.pack(anchor="w", pady=(0, 8))
            for pet_id in your_pets:
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=ROW_PADY)
                name = get_pet_display_name_for_user(pet_id, self.user_data)
                default = get_pet_display_name(pet_id)
                # Show default name in parentheses if there's a custom name
                if name != default:
                    display_name = f"{name} ({default})"
                else:
                    display_name = name
                lbl = ctk.CTkLabel(
                    row,
                    text=display_name,
                    font=FONTS["default"],
                    text_color=COLORS["dark_text"],
                )
                lbl.pack(side="left", fill="x", expand=True, padx=(0, 12))
                self._your_pet_rows.append((pet_id, lbl))
                ctk.CTkButton(
                    row,
                    text="Rename",
                    font=FONTS["small"],
                    fg_color=COLORS["warm_beige"],
                    hover_color=COLORS["soft_pink"],
                    text_color=COLORS["dark_text"],
                    width=64,
                    height=28,
                    command=lambda pid=pet_id: self._rename_pet(pid),
                ).pack(side="right")
            spacer = ctk.CTkLabel(scroll, text="", font=FONTS["default"])
            spacer.pack(anchor="w", pady=(0, 4))

        pets_label = ctk.CTkLabel(
            scroll,
            text="Pets to buy",
            font=FONTS["heading"],
            text_color=COLORS["dark_text"],
        )
        pets_label.pack(anchor="w", pady=(0, 8))
        for item in get_shop_pet_items():
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=ROW_PADY)
            lbl = ctk.CTkLabel(
                row,
                text=item.name,
                font=FONTS["default"],
                text_color=COLORS["dark_text"],
            )
            lbl.pack(side="left", fill="x", expand=True, padx=(0, 12))
            btn = ctk.CTkButton(
                row,
                text=str(item.cost),
                font=FONTS["default"],
                fg_color=COLORS["sage_green"],
                hover_color=COLORS["muted_teal"],
                text_color="white",
                width=PRICE_BTN_WIDTH,
                height=28,
                command=lambda iid=item.id: self._buy(iid),
            )
            if self._is_item_disabled(item):
                btn.configure(state="disabled", fg_color=COLORS["light_text"])
            btn.pack(side="right")
            self._item_rows.append((lbl, btn, item.id))

        plants_label = ctk.CTkLabel(
            scroll,
            text="Plants",
            font=FONTS["heading"],
            text_color=COLORS["dark_text"],
        )
        plants_label.pack(anchor="w", pady=(16, 8))
        for item in get_shop_plant_items():
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=ROW_PADY)
            lbl = ctk.CTkLabel(
                row,
                text=item.name,
                font=FONTS["default"],
                text_color=COLORS["dark_text"],
            )
            lbl.pack(side="left", fill="x", expand=True, padx=(0, 12))
            btn = ctk.CTkButton(
                row,
                text=str(item.cost),
                font=FONTS["default"],
                fg_color=COLORS["sage_green"],
                hover_color=COLORS["muted_teal"],
                text_color="white",
                width=PRICE_BTN_WIDTH,
                height=28,
                command=lambda iid=item.id: self._buy(iid),
            )
            if self._is_item_disabled(item):
                btn.configure(state="disabled", fg_color=COLORS["light_text"])
            btn.pack(side="right")
            self._item_rows.append((lbl, btn, item.id))

        def close_shop():
            if self.on_close:
                self.on_close(self._win)
            self._win.destroy()

        self._win.protocol("WM_DELETE_WINDOW", close_shop)

    def _is_item_disabled(self, item) -> bool:
        return item.id in self.user_data.inventory or not can_afford(self.user_data, item.id)

    def _rename_pet(self, pet_id: str) -> None:
        """Open rename dialog for this pet and save."""
        current = get_pet_display_name_for_user(pet_id, self.user_data)
        default = get_pet_display_name(pet_id)
        new_name = RenamePlantDialog(
            self._win,
            current_name=current,
            default_name=default,
            title="Name your pet",
            prompt="Pet name (leave empty to use default):",
        ).show()
        if new_name is not None:
            if new_name.strip():
                self.user_data.pet_custom_names[pet_id] = new_name.strip()
            elif pet_id in self.user_data.pet_custom_names:
                del self.user_data.pet_custom_names[pet_id]
            save_user_data(self.user_data)
            self.on_purchase()
        self._refresh_display()

    def _buy(self, item_id: str) -> None:
        if not purchase(self.user_data, item_id):
            return
        save_user_data(self.user_data)
        self.on_purchase()
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Update balance, your-pet names, and gray out price buttons when not available."""
        if self._balance_label:
            self._balance_label.configure(text=f"{self.user_data.currency_balance} Dewdrops")
        for pet_id, lbl in getattr(self, "_your_pet_rows", []):
            name = get_pet_display_name_for_user(pet_id, self.user_data)
            default = get_pet_display_name(pet_id)
            # Show default name in parentheses if there's a custom name
            if name != default:
                display_name = f"{name} ({default})"
            else:
                display_name = name
            lbl.configure(text=display_name)
        for lbl, btn, item_id in self._item_rows:
            item = get_item(item_id)
            if item:
                disabled = self._is_item_disabled(item)
                if disabled:
                    btn.configure(state="disabled", fg_color=COLORS["light_text"])
                else:
                    btn.configure(state="normal", fg_color=COLORS["sage_green"])
