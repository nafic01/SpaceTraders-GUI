import tkinter as tk
from tkinter import ttk

from collections import defaultdict
from datetime import datetime
from itertools import zip_longest

import json
import os.path
import requests

import locale
    
locale.setlocale(locale.LC_ALL, "")  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

AGENT_FILE = "agents.json"

API_STATUS = "https://api.spacetraders.io/v2/"
LIST_FACTIONS = "https://api.spacetraders.io/v2/factions"
CLAIM_USER = "https://api.spacetraders.io/v2/register"
MY_ACCOUNT = "https://api.spacetraders.io/v2/my/agent"
MY_CONTRACTS = "https://api.spacetraders.io/v2/my/contracts"
MY_SHIPS = "https://api.spacetraders.io/v2/my/ships"
DOCK_SHIP = "https://api.spacetraders.io/v2/my/ships/{}/dock"
ORBIT_SHIP = "https://api.spacetraders.io/v2/my/ships/{}/orbit"
NAVIGATE_SHIP = "https://api.spacetraders.io/v2/my/ships/{}/navigate"
REFUEL_SHIP = "https://api.spacetraders.io/v2/my/ships/{}/refuel"
MY_SHIP = "https://api.spacetraders.io/v2/my/ships/{}"
GET_MARKET = "https://api.spacetraders.io/v2/systems/{}/waypoints/{}/market"
BUY_CARGO = "https://api.spacetraders.io/v2/my/ships/{}/purchase"
SELL_CARGO = "https://api.spacetraders.io/v2/my/ships/{}/sell"
MINE = "https://api.spacetraders.io/v2/my/ships/{}/extract"



UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
DISPLAY_FORMAT = " %B, %Y"

FACTION_LOOKUPS = {}


def parse_datetime(dt):
    return datetime.strptime(dt, UTC_FORMAT)


def format_datetime(dt_text):
    dt = parse_datetime(dt_text)
    d = dt.day
    return (
        str(d)
        + ("th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th"))
        + datetime.strftime(dt, DISPLAY_FORMAT)
    )


def load_player_logins():
    known_agents = {}

    if os.path.exists(AGENT_FILE):
        with open(AGENT_FILE) as json_agents:
            known_agents = json.load(json_agents)

    return known_agents


def store_agent_login(json_result):
    known_agents = load_player_logins()
    known_agents[json_result["symbol"]] = json_result["token"]

    with open(AGENT_FILE, "w") as json_agents:
        json.dump(known_agents, json_agents)


def get_faction_lookups():
    global FACTION_LOOKUPS
    if len(FACTION_LOOKUPS) > 0:
        return FACTION_LOOKUPS

    try:
        response = requests.get(
            LIST_FACTIONS,
            params={"limit": 20},
        )

        if response.status_code == 200:
            faction_json = response.json()
            for faction in faction_json["data"]:
                FACTION_LOOKUPS[faction["symbol"]] = faction["name"]

        else:
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print("Failed:", ce)

    return FACTION_LOOKUPS


def generate_faction_combobox():
    faction_combobox["values"] = sorted(get_faction_lookups().values())


def generate_login_combobox():
    known_agents = load_player_logins()
    agent_list = sorted(known_agents.keys(), key=str.casefold)

    id_login["values"] = agent_list


def show_agent_summary(json_result):
    global FACTION_LOOKUPS
    tabs.tab(0, state=tk.DISABLED)
    tabs.tab(1, state=tk.NORMAL)
    tabs.tab(2, state=tk.NORMAL)
    tabs.tab(3, state=tk.NORMAL)

    player_token.set(json_result["token"])
    player_login.set(json_result["symbol"])
    player_faction.set(get_faction_lookups()[json_result["startingFaction"]])
    player_worth.set(f"{json_result['credits']:n}")

    tabs.select(1)


def register_agent():
    try:
        username = agent_name.get()
        faction = next(
            iter(
                [
                    symbol
                    for symbol, name in get_faction_lookups().items()
                    if name == agent_faction.get()
                ]
            )
        )

        response = requests.post(
            CLAIM_USER,
            data={"faction": faction, "symbol": username},
        )
        if response.status_code < 400:
            result = response.json()
            # used to hold the token for later
            result["data"]["agent"]["token"] = result["data"]["token"]
            store_agent_login(result["data"]["agent"])
            show_agent_summary(result["data"]["agent"])
            agent_name.set("")
        else:
            print("Failed:", response.status_code, response.reason, response.text)

    except StopIteration:
        print("Did they pick a faction?")

    except ConnectionError as ce:
        print("Failed:", ce)


def login_agent():
    player_token.set(player_login.get())

    if id_login.current() != -1:
        known_agents = load_player_logins()
        player_token.set(known_agents[player_login.get()])

    try:
        response = requests.get(
            MY_ACCOUNT,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {player_token.get()}",
            },
        )
        if response.status_code == 200:
            result = response.json()
            result["data"]["token"] = player_token.get()
            show_agent_summary(result["data"])

            if id_login.current() == -1:
                store_agent_login(result["data"])

        else:
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print("Failed:", ce)


def logout_agent():
    tabs.tab(0, state=tk.NORMAL)
    tabs.tab(1, state=tk.DISABLED)
    tabs.tab(2, state=tk.DISABLED)
    tabs.tab(3, state=tk.DISABLED)

    player_login.set("")
    player_token.set("")

    tabs.select(0)


def refresh_tabs(event):
    selected_index = tabs.index(tabs.select())
    if selected_index == 1:
        refresh_player_summary()

    elif selected_index == 2:
        refresh_activities()

    elif selected_index == 3:
        refresh_leaderboard()


def refresh_player_summary(*args):
    try:
        response = requests.get(
            MY_ACCOUNT,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {player_token.get()}",
            },
        )
        if response.status_code == 200:
            result = response.json()

            player_worth.set(f"{result['data']['credits']:n}")

        response = requests.get(
            MY_CONTRACTS,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {player_token.get()}",
            },
        )
        if response.status_code == 200:
            result = response.json()
            contract_view.delete(*contract_view.get_children())
            for row in result["data"]:
                if len(row["terms"]["deliver"]) > 0:
                    remaining = (
                        row["terms"]["deliver"][0]["unitsRequired"]
                        - row["terms"]["deliver"][0]["unitsFulfilled"]
                    )
                    contract_view.insert(
                        "",
                        "end",
                        iid=row["id"],
                        text="contract_values",
                        open=True,
                        values=(
                            get_faction_lookups()[row["factionSymbol"]],
                            row["type"],
                            format_datetime(row["terms"]["deadline"]),
                            row["terms"]["deliver"][0]["tradeSymbol"],
                            row["terms"]["deliver"][0]["destinationSymbol"],
                            f"{remaining:n}",
                        ),
                    )
                for subrow, item in enumerate(row["terms"]["deliver"][1:]):
                    contract_view.insert(
                        row["id"],
                        "end",
                        iid=f'{row["id"]}#{subrow}',
                        text="extra_items",
                        values=(
                            "",
                            "",
                            "",
                            item["tradeSymbol"],
                            item["destinationSymbol"],
                            f"{(item['unitsRequired']-item['unitsFulfilled']):n}",
                        ),
                    )

        else:
            print("Failed:", response.status_code, response.reason, response.text)

        response = requests.get(
            MY_SHIPS,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {player_token.get()}",
            },
        )
        if response.status_code == 200:
            result = response.json()
            ship_view.delete(*ship_view.get_children())
            for row in result["data"]:
                ship_view.insert(
                    "",
                    "end",
                    iid=row["symbol"],
                    text="ship_values",
                    open=True,
                    values=(
                        row["symbol"],
                        row["registration"]["role"],
                        row["frame"]["name"],
                        row["reactor"]["name"],
                        row["engine"]["name"],
                        row["nav"]["status"],
                        f'{row["fuel"]["current"]} / {row["fuel"]["capacity"]}',
                        f'{row["cargo"]["units"]} / {row["cargo"]["capacity"]}',
                    ),
                )

        else:
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print("Failed:", ce)


def display_clicked_contract(*args):
    print(contract_view.index(contract_view.focus()), contract_view.focus())


def display_clicked_ship(*args):
    print(ship_view.index(ship_view.focus()), ship_view.focus())


def on_ship_select(event):
    # Called when user clicks a row in the ship table
    selected = ship_view.focus()
    if selected:
        # Get the status value from the selected row (column index 5)
        status = ship_view.item(selected)["values"][5]
        selected_ship_label.set(f"Selected: {selected}")
        if status == "DOCKED":
            dock_button.config(text="Undock")
        else:
            dock_button.config(text="Dock")


def dock_or_undock():
    selected = ship_view.focus()
    if not selected:
        dock_status_label.set("No ship selected!")
        return

    status = ship_view.item(selected)["values"][5]

    try:
        if status == "DOCKED":
            # undock = put into orbit
            response = requests.post(
                ORBIT_SHIP.format(selected),
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {player_token.get()}",
                },
            )
        else:
            # dock the ship
            response = requests.post(
                DOCK_SHIP.format(selected),
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {player_token.get()}",
                },
            )

        if response.status_code == 200:
            # Retrieve the new status from the response and update the ship view
            new_status = response.json()["data"]["nav"]["status"]
            values = list(ship_view.item(selected)["values"])
            values[5] = new_status
            ship_view.item(selected, values=values)
            # update the button and label
            dock_status_label.set(f"{selected}: {new_status}")
            if new_status == "DOCKED":
                dock_button.config(text="Undock")
            else:
                dock_button.config(text="Dock")
        else:
            dock_status_label.set(f"Failed: {response.status_code} {response.reason}")
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        dock_status_label.set("Connection error!")
        print("Failed:", ce)


###
# Activities tab functions
#

def refresh_activities(*args):
    # repopulate the ship selector dropdown with current ships
    try:
        response = requests.get(
            MY_SHIPS,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {player_token.get()}",
            },
        )
        if response.status_code == 200:
            result = response.json()
            ship_symbols = [row["symbol"] for row in result["data"]]
            activities_ship_selector["values"] = ship_symbols
            if ship_symbols:
                activities_ship_selector.current(0)
                on_activities_ship_select(None)
        else:
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print("Failed:", ce)


def on_activities_ship_select(event):
    # called when a ship is chosen from the dropdown
    symbol = activities_ship_var.get()
    if not symbol:
        return

    try:
        response = requests.get(
            MY_SHIP.format(symbol),
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {player_token.get()}",
            },
        )
        if response.status_code == 200:
            ship = response.json()["data"]
            update_activities_panel(ship)
        else:
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print("Failed:", ce)


def update_activities_panel(ship):
    fuel_current = ship["fuel"]["current"]
    fuel_capacity = ship["fuel"]["capacity"]
    status = ship["nav"]["status"]
    waypoint = ship["nav"]["waypointSymbol"]
    system = ship["nav"]["systemSymbol"]
    flight_mode = ship["nav"]["flightMode"]

    act_status_var.set(status)
    act_waypoint_var.set(waypoint)
    act_system_var.set(system)
    act_flight_mode_var.set(flight_mode)
    act_fuel_var.set(f"{fuel_current} / {fuel_capacity}")

    if fuel_capacity > 0:
        fuelbar = (fuel_current / fuel_capacity) * 100
        print(f"Fuel: {fuel_current}/{fuel_capacity} ({fuelbar:.1f}%)")
    else:
        fuelbar = 0
    fuel_bar["value"] = fuelbar

    # update dock/orbit button text
    if status == "DOCKED":
        act_dock_button.config(text="Undock (Orbit)")
    else:
        act_dock_button.config(text="Dock")

# This is the dock button function on the summary page. It is dynamic and changes based on if the ship is already docked or not
def act_dock_or_undock():
    symbol = activities_ship_var.get()
    if not symbol:
        act_status_label_var.set("No ship selected!")
        return

    status = act_status_var.get()

    try:
        if status == "DOCKED":
            response = requests.post(
                ORBIT_SHIP.format(symbol),
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {player_token.get()}",
                },
            )
        else:
            response = requests.post(
                DOCK_SHIP.format(symbol),
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {player_token.get()}",
                },
            )

        if response.status_code == 200:
            ship = response.json()["data"]
            nav = ship.get("nav", ship)
            act_status_var.set(nav["status"])
            act_waypoint_var.set(nav["waypointSymbol"])
            if nav["status"] == "DOCKED":
                act_dock_button.config(text="Undock (Orbit)")
            else:
                act_dock_button.config(text="Dock")
            act_status_label_var.set(f"Success: {symbol} is now {nav['status']}")
        else:
            act_status_label_var.set(f"Failed: {response.status_code} {response.reason}")
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        act_status_label_var.set("Connection error!")
        print("Failed:", ce)

def act_mine():
    symbol = activities_ship_var.get()
    if not symbol:
        act_status_label_var.set("No ship selected!")
        return

    status = act_status_var.get()
    if status == "DOCKED":
        act_status_label_var.set("Can't mine while docked")
        return

    try:
        response = requests.post(
            MINE.format(symbol),
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {player_token.get()}",
            },
        )
        if response.status_code == 201:
            result = response.json()["data"]
            yield_data = result["extraction"]["yield"]
            act_status_label_var.set(f"Mined {yield_data['units']}x {yield_data['symbol']}!")
        else:
            act_status_label_var.set(f"Failed: {response.status_code} {response.reason}")
            print("Failed:", response.status_code, response.reason, response.text)

        total = 80
        passed = 0
        while passed < total:
            act_mine_progress["value"] = (passed / total) * 100
            passed += 1
            root.after(1000, lambda: None)  # Allow the GUI to update

    except ConnectionError as ce:
        act_status_label_var.set("Connection error!")
        print("Failed:", ce)




# btw for future reference, act = activities
def act_navigate():
    symbol = activities_ship_var.get()
    waypoint = nav_waypoint_var.get().strip()

    if not symbol:
        act_status_label_var.set("No ship selected!")
        return
    if not waypoint:
        act_status_label_var.set("Enter a waypoint symbol!")
        return

    try:
        response = requests.post(
            NAVIGATE_SHIP.format(symbol),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {player_token.get()}",
            },
            json={"waypointSymbol": waypoint},
        )

        if response.status_code == 200:
            result = response.json()["data"]
            nav = result["nav"]
            fuel = result["fuel"]
            act_status_var.set(nav["status"])
            act_waypoint_var.set(nav["waypointSymbol"])
            act_fuel_var.set(f'{fuel["current"]} / {fuel["capacity"]}')
            if fuel["capacity"] > 0:
                fuel_bar["value"] = (fuel["current"] / fuel["capacity"]) * 100
            arrival = nav["route"]["arrival"]
            act_status_label_var.set(f"Navigating to {waypoint} — arrives {format_datetime(arrival)}")
        else:
            act_status_label_var.set(f"Failed: {response.status_code} {response.reason}")
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        act_status_label_var.set("Connection error!")
        print("Failed:", ce)


def act_refuel():
    symbol = activities_ship_var.get()
    if not symbol:
        act_status_label_var.set("No ship selected!")
        return

    try:
        response = requests.post(
            REFUEL_SHIP.format(symbol),
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {player_token.get()}",
            },
        )

        if response.status_code == 200:
            result = response.json()["data"]
            fuel = result["fuel"]
            act_fuel_var.set(f'{fuel["current"]} / {fuel["capacity"]}')
            if fuel["capacity"] > 0:
                fuel_bar["value"] = (fuel["current"] / fuel["capacity"]) * 100
            act_status_label_var.set(f"Refuelled! {fuel['current']} / {fuel['capacity']}")
        else:
            act_status_label_var.set(f"Failed: {response.status_code} {response.reason}")
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        act_status_label_var.set("Connection error!")
        print("Failed:", ce)


def load_market(*args):
    symbol = activities_ship_var.get()
    if not symbol:
        act_status_label_var.set("No ship selected!")
        return

    try:
        # this gets the ships info first bcuz u need it to know the current waypoint to load the market.
        response = requests.get(MY_SHIP.format(symbol), headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {player_token.get()}",
        })
        if response.status_code != 200:
            act_status_label_var.set(f"couldnt get ship: {response.status_code}")
            return

        ship = response.json()["data"]
        system = ship["nav"]["systemSymbol"]
        waypoint = ship["nav"]["waypointSymbol"]

        response = requests.get(GET_MARKET.format(system, waypoint), headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {player_token.get()}",
        })
        if response.status_code == 200:
            market = response.json()["data"]
            marketplace_view.delete(*marketplace_view.get_children())
            for row in market.get("tradeGoods", []):
                marketplace_view.insert("", "end", text="market_values", values=(
                    row["symbol"],
                    row["type"],
                    f"{row['purchasePrice']:n}",
                    f"{row['sellPrice']:n}",
                    f"{row['tradeVolume']:n}",
                ))
            act_status_label_var.set(f"loaded market at {waypoint}")
        else:
            act_status_label_var.set(f"Failed: {response.status_code} {response.reason}")
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        act_status_label_var.set("Connection error!")
        print("Failed:", ce)


def buy_good():
    symbol = activities_ship_var.get()
    if not symbol:
        act_status_label_var.set("No ship selected!")
        return

    selected = marketplace_view.focus()
    if not selected:
        act_status_label_var.set("pick something from the market first!")
        return

    trade_symbol = marketplace_view.item(selected)["values"][0]
    qty_str = buy_qty_var.get().strip()

    if not qty_str.isdigit() or int(qty_str) < 1:
        act_status_label_var.set("Enter a valid quantity!")
        return

    try:
        response = requests.post(BUY_CARGO.format(symbol), headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {player_token.get()}",
        }, json={"symbol": trade_symbol, "units": int(qty_str)})

        if response.status_code == 201:
            result = response.json()["data"]
            transaction = result["transaction"]
            player_worth.set(f"{result['agent']['credits']:n}")
            act_status_label_var.set(
                f"Bought {transaction['units']}x {trade_symbol} for {transaction['totalPrice']:n} credits"
            )
        else:
            act_status_label_var.set(f"Failed: {response.status_code} {response.reason}")
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        act_status_label_var.set("Connection error!")
        print("Failed:", ce)


def sell_good():
    symbol = activities_ship_var.get()
    if not symbol:
        act_status_label_var.set("No ship selected!")
        return

    # type the item symbol and qty then press sell
    trade_symbol = sell_item_var.get().strip()
    qty_str = sell_qty_var.get().strip()

    if not trade_symbol:
        act_status_label_var.set("enter an item symbol to sell!")
        return
    if not qty_str.isdigit() or int(qty_str) < 1:
        act_status_label_var.set("Enter a valid quantity!")
        return

    try:
        response = requests.post(SELL_CARGO.format(symbol), headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {player_token.get()}",
        }, json={"symbol": trade_symbol, "units": int(qty_str)})

        if response.status_code == 201:
            result = response.json()["data"]
            transaction = result["transaction"]
            player_worth.set(f"{result['agent']['credits']:n}")
            act_status_label_var.set(
                f"Sold {transaction['units']}x {trade_symbol} for {transaction['totalPrice']:n} credits"
            )
        else:
            act_status_label_var.set(f"Failed: {response.status_code} {response.reason}")
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        act_status_label_var.set("Connection error!")
        print("Failed:", ce)


def refresh_leaderboard(*args):
    try:
        response = requests.get(
            API_STATUS,
            params={"token": player_token.get()},
        )
        if response.status_code == 200:
            result = response.json()
            credits_leaderboard_view.delete(*credits_leaderboard_view.get_children())
            for rank, row in enumerate(result["leaderboards"]["mostCredits"]):
                credits_leaderboard_view.insert(
                    "",
                    "end",
                    text="values",
                    values=(rank + 1, row["agentSymbol"], f"{row['credits']:n}"),
                )

            charts_leaderboard_view.delete(*charts_leaderboard_view.get_children())
            for rank, row in enumerate(result["leaderboards"]["mostSubmittedCharts"]):
                charts_leaderboard_view.insert(
                    "",
                    "end",
                    text="values",
                    values=(rank + 1, row["agentSymbol"], f"{row['chartCount']:n}"),
                )

        else:
            print("Failed:", response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print("Failed:", ce)


###
# Root window, with app title
#
# I am going to change the window name to something cooler
root = tk.Tk()
root.title("SpaceTraders GUI")
s = ttk.Style()
s.theme_use("aqua")
# Main themed frame, for all other widgets to rest upon
main = ttk.Frame(root, padding="3 3 12 12")
main.grid(sticky=tk.NSEW)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Tabbed widget for rest of the app to run in
tabs = ttk.Notebook(main)
tabs.grid(sticky=tk.NSEW)
tabs.bind("<<NotebookTabChanged>>", refresh_tabs)

main.columnconfigure(0, weight=1)
main.rowconfigure(0, weight=1)

# setup the four main tabs
welcome = ttk.Frame(tabs)
summary = ttk.Frame(tabs)
activities = ttk.Frame(tabs)
leaderboard = ttk.Frame(tabs)

tabs.add(welcome, text="Welcome")
tabs.add(summary, text="Summary")
tabs.add(activities, text="Activities")
tabs.add(leaderboard, text="Leaderboard")

tabs.tab(1, state=tk.DISABLED)
tabs.tab(2, state=tk.DISABLED)
tabs.tab(3, state=tk.DISABLED)

###
# agent registration/login tab
#

welcome_frame = ttk.Frame(welcome)
welcome_frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)

# left hand frame will check/register new agents and return/store the UUID
register = ttk.LabelFrame(welcome_frame, text="Register", relief="groove", padding=5)
register.grid(sticky=tk.NSEW)

# widgets required on the left are a label, an entry, a dropdown, and a button
agent_name = tk.StringVar()
agent_faction = tk.StringVar()
ttk.Label(
    register, text="Enter a new agent name\nto start a new account", anchor=tk.CENTER
).grid(sticky=tk.EW)
faction_combobox = ttk.Combobox(
    register, textvariable=agent_faction, postcommand=generate_faction_combobox
)
faction_combobox.grid(row=1, column=0, sticky=tk.EW)
ttk.Entry(register, textvariable=agent_name).grid(row=2, column=0, sticky=tk.EW)
ttk.Button(register, text="Register new agent", command=register_agent).grid(
    row=3, column=0, columnspan=2, sticky=tk.EW
)

register.columnconfigure(0, weight=1)
register.rowconfigure(0, weight=1)

ttk.Label(welcome_frame, text="or", padding=10, anchor=tk.CENTER).grid(
    row=0, column=1, sticky=tk.EW
)

# right hand frame will allow to choose from known players and/or paste in existing
# UUID to login and play as that agent
login = ttk.LabelFrame(welcome_frame, text="Login", relief=tk.GROOVE, padding=5)
login.grid(row=0, column=2, sticky=tk.NSEW)

# widgets required on the right are a dropdown, and a button
player_login = tk.StringVar()
player_token = (
    tk.StringVar()
)  # going to use this to remember the currently logged in agent
ttk.Label(login, text="Choose the agent to play as\nor paste an existing id", anchor=tk.CENTER).grid(
    sticky=tk.EW,
)
id_login = ttk.Combobox(
    login, textvariable=player_login, postcommand=generate_login_combobox
)
id_login.grid(row=1, column=0, sticky=tk.EW)
ttk.Button(login, text="Login agent", command=login_agent).grid(
    row=2, column=0, columnspan=2, sticky=tk.EW
)

login.columnconfigure(0, weight=1)
login.rowconfigure(0, weight=1)

welcome_frame.columnconfigure(0, weight=1)
welcome_frame.columnconfigure(2, weight=1)
welcome_frame.rowconfigure(0, weight=1)

welcome.columnconfigure(0, weight=1)
welcome.rowconfigure(0, weight=1)

###
# summary tab
#

player_summary = ttk.LabelFrame(summary, text="Agent", relief=tk.GROOVE, padding=5)

player_faction = tk.StringVar()
player_worth = tk.StringVar()

ttk.Label(player_summary, textvariable=player_login, anchor=tk.CENTER).grid(
    columnspan=2, sticky=tk.EW
)
ttk.Label(player_summary, text="Faction:").grid(row=1, column=0, sticky=tk.W)
ttk.Label(player_summary, textvariable=player_faction, anchor=tk.CENTER).grid(
    row=1, column=1, sticky=tk.EW
)
ttk.Label(player_summary, text="Credits:").grid(row=2, column=0, sticky=tk.W)
ttk.Label(player_summary, textvariable=player_worth, anchor=tk.CENTER).grid(
    row=2, column=1, sticky=tk.EW
)
ttk.Button(player_summary, text="Logout", command=logout_agent).grid(
    row=3, column=0, columnspan=2, sticky=tk.EW
)

player_summary.columnconfigure(0, weight=1)

contract_summary = ttk.LabelFrame(
    summary, text="Contracts", relief=tk.GROOVE, padding=5
)

contract_view = ttk.Treeview(
    contract_summary,
    height=3,
    columns=("Faction", "Type", "Deadline", "Goods", "Destination", "Owing"),
    show="headings",
)
contract_view.column("Faction", anchor=tk.W, width=20)
contract_view.column("Type", anchor=tk.W, width=20)
contract_view.column("Deadline", anchor=tk.W, width=20)
contract_view.column("Goods", anchor=tk.W, width=30)
contract_view.column("Destination", anchor=tk.W, width=20)
contract_view.column("Owing", anchor=tk.E, width=20)
contract_view.heading("#1", text="Faction")
contract_view.heading("#2", text="Type")
contract_view.heading("#3", text="Deadline")
contract_view.heading("#4", text="Goods")
contract_view.heading("#5", text="Destination")
contract_view.heading("#6", text="Owing")
contract_view.grid(sticky=tk.NSEW)
contract_scroll = ttk.Scrollbar(
    contract_summary, orient=tk.VERTICAL, command=contract_view.yview
)
contract_scroll.grid(column=1, row=0, sticky=tk.NS)
contract_view.config(yscrollcommand=contract_scroll.set)
contract_view.bind("<Double-1>", display_clicked_contract)

contract_summary.columnconfigure(0, weight=1)
contract_summary.rowconfigure(0, weight=1)

ship_summary = ttk.LabelFrame(summary, text="Ships", relief=tk.GROOVE, padding=5)
ship_view = ttk.Treeview(
    ship_summary,
    height=3,
    columns=(
        "Registration",
        "Role",
        "Frame",
        "Reactor",
        "Engine",
        "Status",
        "Fuel",
        "Cargo",
    ),
    show="headings",
)
ship_view.column("Registration", anchor=tk.W, width=30)
ship_view.column("Role", anchor=tk.W, width=30)
ship_view.column("Frame", anchor=tk.W, width=30)
ship_view.column("Reactor", anchor=tk.W, width=30)
ship_view.column("Engine", anchor=tk.W, width=30)
ship_view.column("Status", anchor=tk.W, width=30)
ship_view.column("Fuel", anchor=tk.E, width=20)
ship_view.column("Cargo", anchor=tk.E, width=20)
ship_view.heading("#1", text="Registration")
ship_view.heading("#2", text="Role")
ship_view.heading("#3", text="Frame")
ship_view.heading("#4", text="Reactor")
ship_view.heading("#5", text="Engine")
ship_view.heading("#6", text="Status")
ship_view.heading("#7", text="Fuel")
ship_view.heading("#8", text="Cargo")
ship_view.grid(sticky=tk.NSEW)
ship_scroll = ttk.Scrollbar(ship_summary, orient=tk.VERTICAL, command=ship_view.yview)
ship_scroll.grid(column=1, row=0, sticky=tk.NS)
ship_view.config(yscrollcommand=ship_scroll.set)
ship_view.bind("<Double-1>", display_clicked_ship)
ship_view.bind("<<TreeviewSelect>>", on_ship_select)

ship_summary.columnconfigure(0, weight=1)
ship_summary.rowconfigure(0, weight=1)

# dock/undock controls frame
dock_controls = ttk.LabelFrame(summary, text="Ship Controls", relief=tk.GROOVE, padding=5)

selected_ship_label = tk.StringVar(value="No ship selected")
dock_status_label = tk.StringVar(value="")

ttk.Label(dock_controls, textvariable=selected_ship_label).grid(
    row=0, column=0, sticky=tk.W
)
dock_button = ttk.Button(dock_controls, text="Dock", command=dock_or_undock)
dock_button.grid(row=0, column=1, padx=10, sticky=tk.EW)
ttk.Label(dock_controls, textvariable=dock_status_label, foreground="gray").grid(
    row=0, column=2, sticky=tk.W
)

dock_controls.columnconfigure(0, weight=1)

# grid everything onto the summary tab
player_summary.grid(row=0, column=0, sticky=tk.NSEW)
contract_summary.grid(row=0, column=1, sticky=tk.NSEW)
ship_summary.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)
dock_controls.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=(5, 0))

summary.columnconfigure(0, weight=1)
summary.columnconfigure(1, weight=3)
summary.rowconfigure(0, weight=2)
summary.rowconfigure(1, weight=3)

###
# activities tab
#

# --- ship selector frame ---
ship_selector_frame = ttk.LabelFrame(activities, text="Select Ship", relief=tk.GROOVE, padding=5)
ship_selector_frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)

activities_ship_var = tk.StringVar()
activities_ship_selector = ttk.Combobox(ship_selector_frame, textvariable=activities_ship_var, state="readonly")
activities_ship_selector.grid(row=0, column=0, sticky=tk.EW, padx=5)
activities_ship_selector.bind("<<ComboboxSelected>>", on_activities_ship_select)
ttk.Button(ship_selector_frame, text="Refresh Ships", command=refresh_activities).grid(row=0, column=1, padx=5)

ship_selector_frame.columnconfigure(0, weight=1)

# --- ship info frame ---
ship_info_frame = ttk.LabelFrame(activities, text="Ship Info", relief=tk.GROOVE, padding=5)
ship_info_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)

act_status_var = tk.StringVar(value="-")
act_waypoint_var = tk.StringVar(value="-")
act_system_var = tk.StringVar(value="-")
act_flight_mode_var = tk.StringVar(value="-")
act_fuel_var = tk.StringVar(value="-")

ttk.Label(ship_info_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
ttk.Label(ship_info_frame, textvariable=act_status_var).grid(row=0, column=1, sticky=tk.W, padx=5)

ttk.Label(ship_info_frame, text="System:").grid(row=1, column=0, sticky=tk.W)
ttk.Label(ship_info_frame, textvariable=act_system_var).grid(row=1, column=1, sticky=tk.W, padx=5)

ttk.Label(ship_info_frame, text="Waypoint:").grid(row=2, column=0, sticky=tk.W)
ttk.Label(ship_info_frame, textvariable=act_waypoint_var).grid(row=2, column=1, sticky=tk.W, padx=5)

ttk.Label(ship_info_frame, text="Flight Mode:").grid(row=3, column=0, sticky=tk.W)
ttk.Label(ship_info_frame, textvariable=act_flight_mode_var).grid(row=3, column=1, sticky=tk.W, padx=5)

ttk.Label(ship_info_frame, text="Fuel:").grid(row=4, column=0, sticky=tk.W)
ttk.Label(ship_info_frame, textvariable=act_fuel_var).grid(row=4, column=1, sticky=tk.W, padx=5)

# fuel progress bar
fuel_bar = ttk.Progressbar(ship_info_frame, orient=tk.HORIZONTAL, length=200, mode="determinate")
fuel_bar.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))

ship_info_frame.columnconfigure(1, weight=1)

# ship controls frame
ship_controls_frame = ttk.LabelFrame(activities, text="Advanced Ship Controls", relief=tk.GROOVE, padding=5)
ship_controls_frame.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=5)

# dock / orbit button
act_dock_button = ttk.Button(ship_controls_frame, text="Dock", command=act_dock_or_undock)
act_dock_button.grid(row=0, column=0, columnspan=2, sticky=tk.EW, pady=2)

# mining button and waiting bar
act_mine_button = ttk.Button(ship_controls_frame, text="Mine", command=act_mine).grid(
    row=2, column=0, columnspan=2, sticky=tk.EW, pady=2
)
act_mine_progress = ttk.Progressbar(ship_controls_frame, orient=tk.HORIZONTAL, length=200, mode="determinate")
act_mine_progress.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))

# refuel button
ttk.Button(ship_controls_frame, text="Refuel", command=act_refuel).grid(
    row=1, column=0, columnspan=2, sticky=tk.EW, pady=2
)

# navigate section
ttk.Separator(ship_controls_frame, orient=tk.HORIZONTAL).grid(
    row=3, column=0, columnspan=2, sticky=tk.EW, pady=5
)
ttk.Label(ship_controls_frame, text="Navigate to Waypoint:").grid(row=3, column=0, columnspan=2, sticky=tk.W)
nav_waypoint_var = tk.StringVar()
ttk.Entry(ship_controls_frame, textvariable=nav_waypoint_var).grid(
    row=4, column=0, sticky=tk.EW, padx=(0, 5)
)
ttk.Button(ship_controls_frame, text="Go", command=act_navigate).grid(row=4, column=1, sticky=tk.EW)

ship_controls_frame.columnconfigure(0, weight=1)

# ship marketplace frame
marketplace_frame = ttk.LabelFrame(activities, text="Marketplace", relief=tk.GROOVE, padding=5)
marketplace_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)

# --- marketplace controls ---
ttk.Button(marketplace_frame, text="Load Market", command=load_market).grid(
    row=0, column=0, columnspan=2, sticky=tk.EW, pady=(0, 5)
)

marketplace_view = ttk.Treeview(
    marketplace_frame,
    height=4,
    columns=("Symbol", "Type", "Buy", "Sell", "Volume"),
    show="headings",
)
marketplace_view.column("Symbol", anchor=tk.W, width=100)
marketplace_view.column("Type", anchor=tk.W, width=60)
marketplace_view.column("Buy", anchor=tk.E, width=55)
marketplace_view.column("Sell", anchor=tk.E, width=55)
marketplace_view.column("Volume", anchor=tk.E, width=45)
marketplace_view.heading("#1", text="Symbol")
marketplace_view.heading("#2", text="Type")
marketplace_view.heading("#3", text="Buy")
marketplace_view.heading("#4", text="Sell")
marketplace_view.heading("#5", text="Vol")
marketplace_view.grid(row=1, column=0, sticky=tk.NSEW)
marketplace_scroll = ttk.Scrollbar(
    marketplace_frame, orient=tk.VERTICAL, command=marketplace_view.yview
)
marketplace_scroll.grid(column=1, row=1, sticky=tk.NS)
marketplace_view.config(yscrollcommand=marketplace_scroll.set)

# buy - click a row in the table then set qty and press buy
buy_qty_var = tk.StringVar(value="1")
buy_frame = ttk.LabelFrame(marketplace_frame, text="Buy", padding=4)
buy_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))
ttk.Label(buy_frame, text="Qty:").grid(row=0, column=0, sticky=tk.W)
ttk.Entry(buy_frame, textvariable=buy_qty_var, width=6).grid(row=0, column=1, padx=5)
ttk.Button(buy_frame, text="Buy Selected", command=buy_good).grid(row=0, column=2, sticky=tk.EW)
buy_frame.columnconfigure(2, weight=1)

# sell - type in the item symbol and qty then press sell
sell_item_var = tk.StringVar()
sell_qty_var = tk.StringVar(value="1")
sell_frame = ttk.LabelFrame(marketplace_frame, text="Sell", padding=4)
sell_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(5, 0))
ttk.Label(sell_frame, text="Item:").grid(row=0, column=0, sticky=tk.W)
ttk.Entry(sell_frame, textvariable=sell_item_var).grid(row=0, column=1, sticky=tk.EW, padx=5)
ttk.Label(sell_frame, text="Qty:").grid(row=0, column=2, sticky=tk.W)
ttk.Entry(sell_frame, textvariable=sell_qty_var, width=6).grid(row=0, column=3, padx=5)
ttk.Button(sell_frame, text="Sell", command=sell_good).grid(row=0, column=4, sticky=tk.EW)
sell_frame.columnconfigure(1, weight=1)

marketplace_frame.columnconfigure(0, weight=1)
marketplace_frame.rowconfigure(1, weight=1)

# --- status bar at the bottom ---
act_status_label_var = tk.StringVar(value="Select a ship to get started")
ttk.Label(activities, textvariable=act_status_label_var, foreground="gray").grid(
    row=3, column=0, columnspan=2, sticky=tk.SW, padx=5, pady=5)

activities.columnconfigure(0, weight=1)
activities.columnconfigure(1, weight=1)
activities.rowconfigure(1, weight=1)
activities.rowconfigure(2, weight=2)

###
# leaderboard tab
#

credits_leaderboard_view = ttk.Treeview(
    leaderboard, height=6, columns=("Rank", "Agent", "Credits"), show="headings"
)
credits_leaderboard_view.column("Rank", anchor=tk.CENTER, width=10)
credits_leaderboard_view.column("Agent", anchor=tk.W, width=100)
credits_leaderboard_view.column("Credits", anchor=tk.E, width=100)
credits_leaderboard_view.heading("#1", text="Rank")
credits_leaderboard_view.heading("#2", text="Agent")
credits_leaderboard_view.heading("#3", text="Credits")
credits_leaderboard_view.grid(sticky=tk.NSEW)
credits_scroll = ttk.Scrollbar(
    leaderboard, orient=tk.VERTICAL, command=credits_leaderboard_view.yview
)
credits_scroll.grid(column=1, row=0, sticky=tk.NS)
credits_leaderboard_view.config(yscrollcommand=credits_scroll.set)

charts_leaderboard_view = ttk.Treeview(
    leaderboard, height=6, columns=("Rank", "Agent", "Chart Count"), show="headings"
)
charts_leaderboard_view.column("Rank", anchor=tk.CENTER, width=10)
charts_leaderboard_view.column("Agent", anchor=tk.W, width=100)
charts_leaderboard_view.column("Chart Count", anchor=tk.E, width=100)
charts_leaderboard_view.heading("#1", text="Rank")
charts_leaderboard_view.heading("#2", text="Agent")
charts_leaderboard_view.heading("#3", text="Chart Count")
charts_leaderboard_view.grid(sticky=tk.NSEW)
charts_scroll = ttk.Scrollbar(
    leaderboard, orient=tk.VERTICAL, command=charts_leaderboard_view.yview
)
charts_scroll.grid(column=1, row=1, sticky=tk.NS)
charts_leaderboard_view.config(yscrollcommand=charts_scroll.set)

refresh = ttk.Button(leaderboard, text="Refresh", command=refresh_leaderboard)
refresh.grid(column=0, row=2, sticky=tk.EW)

leaderboard.columnconfigure(0, weight=1)
leaderboard.rowconfigure((0, 1), weight=1)

root.mainloop()