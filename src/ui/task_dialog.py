"""
Task entry dialog: choose one of two hardcoded tasks and submit for dewdrops.
"""
import customtkinter as ctk
from typing import Optional, Callable

from ..models import TASKS
from .styles import COLORS, FONTS


class TaskDialog:
    """Popup to select a task and submit. Returns (task_id, dewdrops) on submit, None on cancel."""

    def __init__(
        self,
        parent: ctk.CTk,
        on_open: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        self.parent = parent
        self.on_open = on_open
        self.on_close = on_close
        self.result: Optional[tuple] = None  # (task_id, dewdrops) or None
        self._dialog: Optional[ctk.CTkToplevel] = None

    def show(self) -> Optional[tuple]:
        """Show the dialog and block until user submits or cancels. Returns (task_id, dewdrops) or None."""
        self.result = None

        self._dialog = ctk.CTkToplevel(self.parent)
        self._dialog.title("Add Task")
        self._dialog.geometry("360x440")
        self._dialog.configure(fg_color=COLORS["cream"])
        self._dialog.transient(self.parent)
        self._dialog.grab_set()
        if self.on_open:
            self.on_open(self._dialog)

        # Content
        content = ctk.CTkFrame(self._dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=20)

        label = ctk.CTkLabel(
            content,
            text="What did you do? (Earn Dewdrops!)",
            font=FONTS["heading"],
            text_color=COLORS["dark_text"],
        )
        label.pack(anchor="w", pady=(0, 12))

        self._var = ctk.StringVar(value=TASKS[0][0])
        for task_id, task_label, _ in TASKS:
            rb = ctk.CTkRadioButton(
                content,
                text=task_label,
                variable=self._var,
                value=task_id,
                font=FONTS["default"],
                text_color=COLORS["dark_text"],
                fg_color=COLORS["sage_green"],
                hover_color=COLORS["muted_teal"],
            )
            rb.pack(anchor="w", pady=6)

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=FONTS["default"],
            fg_color=COLORS["light_text"],
            hover_color=COLORS["dark_text"],
            text_color="white",
            width=100,
            command=self._cancel,
        ).pack(side="right", padx=6)

        ctk.CTkButton(
            btn_frame,
            text="Submit",
            font=FONTS["default"],
            fg_color=COLORS["sage_green"],
            hover_color=COLORS["muted_teal"],
            text_color="white",
            width=100,
            command=self._submit,
        ).pack(side="right")

        self._dialog.protocol("WM_DELETE_WINDOW", self._cancel)
        self._dialog.wait_window()
        return self.result

    def _submit(self) -> None:
        task_id = self._var.get()
        amount = next(d for tid, _, d in TASKS if tid == task_id)
        self.result = (task_id, amount)
        if self._dialog:
            if self.on_close:
                self.on_close(self._dialog)
            self._dialog.destroy()
            self._dialog = None

    def _cancel(self) -> None:
        self.result = None
        if self._dialog:
            if self.on_close:
                self.on_close(self._dialog)
            self._dialog.destroy()
            self._dialog = None
