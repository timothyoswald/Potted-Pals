# Sprout & Study

A cozy desktop companion app that promotes productivity through a reward system. Complete tasks to earn Dewdrops, grow your plant, and collect pets!

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

## Features

- **Main window** – Plant display, Dewdrop balance, plant switcher
- **Tasks** – Add tasks from a menu to earn Dewdrops (e.g. “Went to a class”, “Studied 30 min”)
- **Shop** – Two sections:
  - **Your pets** – Rename owned pets; names show as “Name (Original)” in the shop
  - **Pets to buy** – Person, Cat, Mushroom, Slime (only owned pets appear on the main window)
  - **Plants** – Baby Cactus, Clover, Rose, Cherry Blossom, Strawberry
- **Grow** – Upgrade your active plant’s stage with Dewdrops
- **Pets** – Owned pets wander on the plant area; hover for name tooltip; click and drag to move them (clamped to the window)
- **Data** – Saves to `data/user_data.json` (balance, inventory, plant stages, pet names, active plant)

## Project Structure

```
sprout & study/
├── main.py              # Entry point
├── requirements.txt     # Python dependencies
├── README.md
├── project_description.md
├── src/
│   ├── models.py        # Data models (UserData, ShopItem, TASKS)
│   ├── data_handler.py  # JSON load/save
│   ├── shop_manager.py  # Shop items, plants/pets owned, purchase logic
│   ├── plant_manager.py # Plant growth helpers
│   ├── ui/               # CustomTkinter UI
│   │   ├── main_window.py   # Main window, plant, pets, buttons
│   │   ├── shop_window.py   # Shop (pets + plants)
│   │   ├── grow_window.py   # Stage upgrades
│   │   ├── task_dialog.py   # Add task popup
│   │   ├── rename_dialog.py # Rename plant/pet
│   │   ├── styles.py        # Colors, fonts, window size
│   │   └── ...
│   └── utils/
│       ├── image_loader.py  # Plant images, dewdrop icon
│       └── pet_sprites.py  # Pet frames (Idle, Run, Sit)
├── assets/
│   ├── plants/          # Plant folders, stage images
│   ├── pets/            # Pet folders (person, cat, mushroom, slime, etc.)
│   └── icons/           # water_drop.png
└── data/                # user_data.json (created at first run)
```

## Window & Assets

- **Window** – Default 280×380px, minimum 240×300px; resizable
- **Plant images** – `assets/plants/{folder}/{folder}_stage_N.png`
- **Pet sprites** – `assets/pets/{pet_id}/Idle/`, `Run/`, `Sit/` (PNG frames)
- **Transparency** – Pets use color-key transparency on Windows; on macOS the app uses a transparent window with RGBA compositing

## Notes

- User data is saved locally in `data/user_data.json`
- Custom plant names and pet names are stored and shown in the UI
- Pets stay behind popups (Shop, Grow, Task dialog, Plant switcher)
