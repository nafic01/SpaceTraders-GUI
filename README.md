# SpaceTraders GUI

A desktop GUI application for the [SpaceTraders API](https://spacetraders.io), built in Python using Tkinter. This program allows you to play the game without manually sending API requests. I made this program and built upon my teachers code as part of a Mock NEA

---

## Requirements

- Python 3.8 or later
- `requests` library

---

## Installation

**1. Clone or download the repository**
```bash
git clone https://github.com/your-username/spacetraders-gui.git
cd spacetraders-gui
```

**2. Install the requests library**
```bash
pip install requests
```

**3. Run the program**
```bash
python main.py
```

---

## Getting Started

### New player
1. To reigster as a new agent, go to [Register](https://my.spacetraders.io/login) and create an account
2. Create a new agent and copy its token
3. Paste into login
(The register button doesn't work)

### Returning player
1. Select your agent from the dropdown (populated from previous sessions)
2. Press **Login agent**

---

## Features

### Welcome Tab
- Register a new SpaceTraders agent with a callsign and faction
- Log back in with one click using saved credentials
- Tokens are stored locally in `agents.json` so no need to copy or remember them

### Summary Tab
- View your agent name, faction, and current credit balance
- Browse all active contracts with deadlines and remaining delivery requirements
- See all your ships with registration, role, frame, status, fuel and cargo
- Dock or undock any ship directly from the ship list

### Activities Tab
- Select any ship from a dropdown to load its full details
- **Ship Info panel** — status, system, waypoint, flight mode, fuel level and a visual fuel progress bar
- **Ship Controls** — dock/undock, refuel, navigate to any waypoint by symbol, and mine resources
- **Marketplace** — load trade goods at your current waypoint, buy by clicking a row, sell by entering item symbol and quantity
- Status bar shows the result of every action in plain English

### Leaderboard Tab
- Top agents by credit balance
- Top agents by waypoints charted
- Refreshes automatically every time the tab is opened

---

## File Structure

```
spacetraders-gui/
├── main.py          # entire application — all logic and UI in one file
└── agents.json      # created automatically on first login, stores saved tokens
```

---

## Notes

- `agents.json` is created automatically the first time you log in. Do **not** share this file it contains your authentication tokens.
- The program requires an internet connection to communicate with the SpaceTraders API.
- The GUI may briefly freeze during API calls as well as crash - my programming skills aren't the best
