Project Outline: Sprout & Study (Local Python App)
1. Project Overview
Goal: A desktop companion app that promotes productivity through a "cozy gaming" reward system.
Core Loop: Complete real-life tasks $\rightarrow$ Manually log tasks to earn "Dewdrops" (currency) $\rightarrow$ Purchase decorations or upgrades for a digital plant.
Visual Style: Lo-fi, pixel art, or soft pastel aesthetics.
2. Technical Stack & Packages
To keep it simple and local, the following Python libraries are recommended:
GUI Framework: CustomTkinter or PySide6.
Why: CustomTkinter provides a modern, rounded, "app-like" look out of the box compared to standard Tkinter.
Data Persistence: json (Standard Library).
Why: To save the user’s currency balance, plant growth stage, and inventory locally without needing a complex database.
Image Handling: Pillow (PIL).
Why: To render and scale the plant graphics and shop icons.
Timing/Background: threading.
Why: To allow the plant to have small animations (like swaying) without freezing the task-entry window.
3. Architecture & Module Breakdown
A. The Data Manager (data_handler.py)
Create a user_data.json file.
Keys to track: currency_balance, plant_stage (0-5), inventory (list of purchased items), and last_login.
B. The Main Interface (main_window.py)
The "Sanctuary" View: A window showing the plant. As the user earns currency/points, the image updates to a larger plant.
Task Logging Button: A simple "+" button that opens a popup.
The Shop Button: Opens a separate tab or sliding menu.
C. The Honor System (Task Logic)
Input Field: A text box for "What did you accomplish?"
Reward Logic: * Short Task (e.g., "Wash dishes"): 10 Dewdrops.
Deep Work (e.g., "30 min study"): 50 Dewdrops.
D. The Shop System
Items: Decorative pots, different plant seeds (succulent, fern, sunflower), or background colors.
Logic: If currency >= item_cost, append item to inventory and subtract cost.
4. Graphic Requirements
Since you are keeping it cozy, you will need the following transparent PNG assets:
Plant Growth Stages: 4-5 images (Seed $\rightarrow$ Sprout $\rightarrow$ Small Plant $\rightarrow$ Flowering Plant).
UI Icons: A small water drop (currency icon) and a shopping basket.
Background: A soft, neutral-colored room or a simple wooden desk surface.
Animations (Optional): Two frames for each plant stage to create a "breathing" or "swaying" effect.
5. Development Roadmap (Phases)
Phase 1: The Shell. Create a basic window that displays a static image of a seed and a "Balance: 0" label.
Phase 2: Currency Logic. Implement the popup window where typing a task and clicking "Submit" increases the balance and saves it to the JSON file.
Phase 3: The Shop. Create a simple list of items. Clicking one checks if the user has enough dewdrops and unlocks the item.
Phase 4: Growth Trigger. Program the plant image to change once the user reaches certain currency milestones (e.g., at 100 dewdrops, the seed becomes a sprout).
Phase 5: Polish. Add custom fonts (like "Comfortaa" or "Quicksand") and soft color hex codes (e.g., #F0EAD6 for Eggshell or #A2B59F for Sage Green).

Tips for the "Cozy" Feel:
Transparency: Use root.attributes("-alpha", 0.9) in Python to make the app slightly see-through so it feels less heavy on the desktop.
Always on Top: Add a toggle to keep the plant "Always on Top" so it sits in the corner of the screen while the user works.
