# RUN THIS FILE:  python3 trip_planner.py
# (stations.txt must be in the same folder)
"""
Sydney Trip Planner - COMP9001 Final Project

Finds the fastest train / metro / ferry route between two Sydney stations,
shows where you can get to within N minutes, and remembers your recent trips.

Advanced concepts used:
  1. Classes and objects   - the Network class stores and searches the map
  2. Recursion             - Network.reachable() explores the map recursively
  3. File input / output   - reads stations.txt, saves recent_trips.txt
  4. Exception handling    - missing files, bad data lines, invalid input
"""

import difflib

DATA_FILE = "stations.txt"
HISTORY_FILE = "recent_trips.txt"
CHANGE_MINUTES = 5          # extra minutes allowed for every change of line


class Network:
    """The rail network: stations, the lines that join them and travel times."""

    def __init__(self, filename):
        # graph[station][neighbour] = (minutes, [line codes that run between them])
        self.graph = {}
        # lines[code] = (line name, [stations in order])
        self.lines = {}
        # aliases[landmark in lower case] = station, e.g. "usyd" -> "Redfern"
        self.aliases = {}
        self.load(filename)

    def load(self, filename):
        """Read the data file. A missing file raises FileNotFoundError;
        a line that cannot be understood is skipped with a warning."""
        current_code = None
        previous_station = None
        with open(filename, "r", encoding="utf-8") as file:
            for number, text in enumerate(file, start=1):
                text = text.strip()
                if text == "" or text.startswith("#"):
                    continue
                parts = text.split("|")
                try:
                    if parts[0] == "LINE":
                        current_code = parts[1]
                        self.lines[current_code] = (parts[2], [])
                        previous_station = None
                    elif parts[0] == "END":
                        current_code = None
                    elif parts[0] == "ALIAS":
                        self.aliases[parts[1].lower()] = parts[2]
                    else:
                        station, minutes = parts[0], int(parts[1])
                        self.add_stop(current_code, station, previous_station, minutes)
                        previous_station = station
                except (IndexError, ValueError, KeyError):
                    print(f"Warning: line {number} of {filename} skipped: {text}")

    def add_stop(self, code, station, previous_station, minutes):
        """Add a station to a line and connect it to the previous stop."""
        self.lines[code][1].append(station)          # KeyError if not inside a LINE
        self.graph.setdefault(station, {})
        if previous_station is not None:
            for a, b in ((previous_station, station), (station, previous_station)):
                if b in self.graph[a]:
                    self.graph[a][b][1].append(code)  # another line on the same track
                else:
                    self.graph[a][b] = (minutes, [code])

    def find_station(self, text):
        """Return the station the user means, or None.
        Accepts any capitalisation and landmarks such as 'USYD'."""
        text = text.strip().lower()
        if text in self.aliases:
            return self.aliases[text]
        for station in self.graph:
            if station.lower() == text:
                return station
        return None

    def suggestions(self, text):
        """Up to 3 station names that look similar to a misspelt name."""
        return difflib.get_close_matches(text.title(), list(self.graph), n=3, cutoff=0.6)

    def fastest_route(self, start, end):
        """Dijkstra's algorithm. Returns (total minutes, legs) or (None, []).

        A "place" is (station, line we are on). Repeatedly take the unvisited
        place with the smallest known time and see if going through it gives
        its neighbours a shorter time. Changing to another line costs
        CHANGE_MINUTES extra, so the route does not change lines for no reason.
        legs is a list like [("T1", ["Penrith", ..., "Wynyard"]), ...].
        """
        first = (start, None)               # at the start we are not on a line yet
        time = {first: 0}                   # best known minutes to each place
        came_from = {}                      # place -> place before it on the best route
        visited = set()
        while True:
            # choose the closest place we have not visited yet
            candidates = [p for p in time if p not in visited]
            if not candidates:
                return None, []             # destination cannot be reached
            current = min(candidates, key=lambda p: time[p])
            station, line = current
            if station == end:
                break
            visited.add(current)
            for neighbour, (minutes, codes) in self.graph[station].items():
                for code in codes:
                    cost = minutes
                    if line is not None and code != line:
                        cost += CHANGE_MINUTES          # time to change lines
                    place = (neighbour, code)
                    new_time = time[current] + cost
                    if place not in time or new_time < time[place]:
                        time[place] = new_time
                        came_from[place] = current
        total = time[current]
        # follow came_from backwards to rebuild the route, then group it by line
        places = [current]
        while places[-1] != first:
            places.append(came_from[places[-1]])
        places.reverse()
        legs = []
        for i in range(1, len(places)):
            station, code = places[i]
            if legs and legs[-1][0] == code:
                legs[-1][1].append(station)             # same line: one more stop
            else:
                legs.append((code, [places[i - 1][0], station]))   # boarded a new line
        return total, legs

    def reachable(self, station, minutes_left, found, time_so_far=0):
        """RECURSION: record every station reachable within minutes_left
        (time on board only; changes are not counted here).

        found[station] keeps the fastest time found so far. The function calls
        itself for each neighbour that can still be reached in time; it stops
        (base case) when no neighbour fits or a faster way is already known.
        """
        found[station] = time_so_far
        for neighbour, (minutes, _lines) in self.graph[station].items():
            new_time = time_so_far + minutes
            if minutes <= minutes_left and \
                    (neighbour not in found or new_time < found[neighbour]):
                self.reachable(neighbour, minutes_left - minutes, found, new_time)


# ---------------------------------------------------------------- user interface
def ask_station(network, prompt):
    """Ask until the user types a real station (or a landmark)."""
    while True:
        text = input(prompt)
        station = network.find_station(text)
        if station:
            if station.lower() != text.strip().lower():
                print(f"   -> using {station}")
            return station
        close = network.suggestions(text)
        if close:
            print(f"   '{text}' not found. Did you mean: {', '.join(close)}?")
        else:
            print(f"   '{text}' not found. Use option 3 to see the station names.")


def ask_number(prompt, low, high):
    """Ask until the user types a whole number between low and high."""
    while True:
        try:
            value = int(input(prompt))
            if low <= value <= high:
                return value
        except ValueError:
            pass
        print(f"   Please type a whole number from {low} to {high}.")


def plan_trip(network):
    start = ask_station(network, "From: ")
    end = ask_station(network, "To:   ")
    if start == end:
        print("   You are already there!")
        return
    minutes, legs = network.fastest_route(start, end)
    if not legs:
        print("   Sorry, there is no route between these stations.")
        return

    changes = len(legs) - 1
    print(f"\n{start} -> {end}:  {minutes} minutes, {changes} change(s)")
    if changes:
        print(f"(includes {CHANGE_MINUTES} minutes for each change)")
    print("-" * 50)
    for code, stations in legs:
        name = network.lines[code][0]
        print(f"  {code} {name}")
        print(f"     {stations[0]} -> {stations[-1]}  ({len(stations) - 1} stops)")
    print("-" * 50)
    save_trip(start, end, minutes)


def show_reachable(network):
    start = ask_station(network, "Starting station: ")
    limit = ask_number("Within how many minutes? (5-60): ", 5, 60)
    found = {}
    network.reachable(start, limit, found)
    del found[start]
    print(f"\nFrom {start} you can reach {len(found)} stations within {limit} minutes:")
    for station, minutes in sorted(found.items(), key=lambda item: item[1]):
        print(f"  {minutes:>3} min  {station}")


def show_line(network):
    for code, (name, stations) in network.lines.items():
        print(f"  {code:<3} {name}")
    code = input("Line code (e.g. T1): ").strip().upper()
    if code not in network.lines:
        print("   That line does not exist.")
        return
    name, stations = network.lines[code]
    print(f"\n{code} {name}:")
    for station in stations:
        print(f"  - {station}")


def save_trip(start, end, minutes):
    """Add the trip to the history file (file output)."""
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as file:
            file.write(f"{start},{end},{minutes}\n")
    except OSError:
        print("   (Could not save this trip to the history file.)")


def show_recent_trips():
    """Show the last 5 trips from the history file (file input)."""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            trips = [line.strip().split(",") for line in file if line.strip()]
    except FileNotFoundError:
        print("   No trips yet - plan one first!")
        return
    print("\nRecent trips:")
    for trip in trips[-5:]:
        if len(trip) == 3:
            print(f"  {trip[0]} -> {trip[1]}  ({trip[2]} min)")


def main():
    try:
        network = Network(DATA_FILE)
    except FileNotFoundError:
        print(f"Error: {DATA_FILE} was not found. Put it in the same folder as this program.")
        return

    print("=" * 50)
    print("   SYDNEY TRIP PLANNER")
    print(f"   {len(network.graph)} stations, {len(network.lines)} lines")
    print("=" * 50)
    while True:
        print("\n1. Plan a trip")
        print("2. Where can I go in N minutes?")
        print("3. Show a line")
        print("4. Recent trips")
        print("0. Quit")
        choice = input("Choose: ").strip()
        if choice == "1":
            plan_trip(network)
        elif choice == "2":
            show_reachable(network)
        elif choice == "3":
            show_line(network)
        elif choice == "4":
            show_recent_trips()
        elif choice == "0":
            print("Safe travels!")
            break
        else:
            print("   Please choose 0-4.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
