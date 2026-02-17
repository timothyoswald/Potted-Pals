"""
Grow window: stage upgrades only (separate from the shop).
"""
import customtkinter as ctk
from typing import Callable, List, Optional, Tuple

from ..data_handler import save_user_data
from ..models import UserData
from ..utils.image_loader import load_dewdrop_icon_pil
from ..shop_manager import (
    get_plant_display_name_for_user,
    get_stage_upgrade_items,
    get_upgrade_item,
    can_afford_upgrade,
    already_has_upgrade,
    purchase_upgrade,
)
from .styles import COLORS, FONTS

PRICE_BTN_WIDTH = 52
ROW_PADY = 4


class GrowWindow:
    """Toplevel window for plant stage upgrades only."""

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
        self._item_rows: List[Tuple[ctk.CTkLabel, ctk.CTkButton, str]] = []

    def show(self) -> None:
        """Show the grow window (non-blocking)."""
        self._win = ctk.CTkToplevel(self.parent)
        plant_name = get_plant_display_name_for_user(self.user_data.active_plant_id, self.user_data)
        self._win.title(f"Grow: {plant_name}")
        self._win.geometry("320x380")
        self._win.minsize(280, 320)
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
            self._dewdrop_pil_ref = dewdrop_pil  # keep ref so CTkImage works
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
        active_plant_id = self.user_data.active_plant_id
        for item in get_stage_upgrade_items(active_plant_id):
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
            if self._is_upgrade_disabled(item):
                btn.configure(state="disabled", fg_color=COLORS["light_text"])
            btn.pack(side="right")

            self._item_rows.append((lbl, btn, item.id))

        def close_grow():
            if self.on_close:
                self.on_close(self._win)
            self._win.destroy()

        self._win.protocol("WM_DELETE_WINDOW", close_grow)

    def _is_upgrade_disabled(self, item) -> bool:
        return already_has_upgrade(self.user_data, item) or not can_afford_upgrade(self.user_data, item)

    def _buy(self, item_id: str) -> None:
        item = get_upgrade_item(item_id, self.user_data.active_plant_id)
        if item is None or not purchase_upgrade(self.user_data, item):
            return
        save_user_data(self.user_data)
        self.on_purchase()
        self._refresh_display()

    def _refresh_display(self) -> None:
        if self._balance_label:
            self._balance_label.configure(text=f"{self.user_data.currency_balance} Dewdrops")
        pid = self.user_data.active_plant_id
        for lbl, btn, item_id in self._item_rows:
            item = get_upgrade_item(item_id, pid)
            if item:
                disabled = self._is_upgrade_disabled(item)
                if disabled:
                    btn.configure(state="disabled", fg_color=COLORS["light_text"])
                else:
                    btn.configure(state="normal", fg_color=COLORS["sage_green"])
