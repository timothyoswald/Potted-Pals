"""
Dialog to set a custom name for a plant.
"""
import customtkinter as ctk
from typing import Optional

from .styles import COLORS, FONTS


class RenamePlantDialog:
    """Modal dialog: entry for name, OK/Cancel. Returns new name or None on cancel. Used for plants or pets."""

    def __init__(
        self,
        parent: ctk.CTk,
        current_name: str,
        default_name: str,
        title: str = "Name your plant",
        prompt: str = "Plant name (leave empty to use default):",
    ):
        self.parent = parent
        self.current_name = current_name
        self.default_name = default_name
        self.title = title
        self.prompt = prompt
        self.result: Optional[str] = None
        self._dialog: Optional[ctk.CTkToplevel] = None

    def show(self) -> Optional[str]:
        """Show the dialog and block until user submits or cancels."""
        self.result = None
        self._dialog = ctk.CTkToplevel(self.parent)
        self._dialog.title(self.title)
        self._dialog.geometry("320x140")
        self._dialog.configure(fg_color=COLORS["cream"])
        self._dialog.transient(self.parent)
        self._dialog.grab_set()

        content = ctk.CTkFrame(self._dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            content,
            text=self.prompt,
            font=FONTS["default"],
            text_color=COLORS["dark_text"],
        ).pack(anchor="w", pady=(0, 8))

        self._entry = ctk.CTkEntry(
            content,
            font=FONTS["default"],
            fg_color="white",
            text_color=COLORS["dark_text"],
            placeholder_text=self.default_name,
            width=260,
            height=32,
        )
        self._entry.pack(fill="x", pady=(0, 16))
        self._entry.insert(0, self.current_name)
        self._entry.focus()

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=FONTS["default"],
            fg_color=COLORS["light_text"],
            hover_color=COLORS["warm_beige"],
            text_color=COLORS["dark_text"],
            width=80,
            height=28,
            command=self._cancel,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btn_frame,
            text="OK",
            font=FONTS["default"],
            fg_color=COLORS["sage_green"],
            hover_color=COLORS["muted_teal"],
            text_color="white",
            width=80,
            height=28,
            command=self._ok,
        ).pack(side="right")

        self._dialog.protocol("WM_DELETE_WINDOW", self._cancel)
        self._entry.bind("<Return>", lambda e: self._ok())
        self._dialog.wait_window()
        return self.result

    def _ok(self) -> None:
        self.result = self._entry.get().strip()
        self._dialog.destroy()

    def _cancel(self) -> None:
        self.result = None
        self._dialog.destroy()
