"""
Color scheme and styling constants for the application.
Custom fonts: Comfortaa, Quicksand (install from Google Fonts if not present).
"""
# Color Palette (Cozy, soft pastel - from project description)
COLORS = {
    "eggshell": "#F0EAD6",
    "sage_green": "#A2B59F",
    "soft_pink": "#E8D5C4",
    "warm_beige": "#D4C5B9",
    "muted_teal": "#B8C5B1",
    "cream": "#F4EFE6",
    "dark_text": "#3A3A3A",
    "light_text": "#6B6B6B",
}

# Fonts: Comfortaa (body), Quicksand (headings). Tk falls back to default if not installed.
FONTS = {
    "default": ("Comfortaa", 12),
    "heading": ("Quicksand", 16, "bold"),
    "small": ("Comfortaa", 10),
}

# Window settings (windowed, not fullscreen; compact so tall plants fit when scaled)
WINDOW_DEFAULT_WIDTH = 280
WINDOW_DEFAULT_HEIGHT = 380
WINDOW_MIN_WIDTH = 240
WINDOW_MIN_HEIGHT = 300
