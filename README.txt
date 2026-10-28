SYDNEY TRIP PLANNER - COMP9001 Final Project

HOW TO RUN
    python3 trip_planner.py
    Keep stations.txt in the same folder. No extra libraries are needed.

WHAT IT DOES
    1. Plan a trip      - fastest route between two stations, split into lines,
                          with the number of changes (each change adds 5 minutes)
    2. Where can I go?  - every station reachable within N minutes
    3. Show a line      - all stations on a line
    4. Recent trips     - the last 5 trips you planned (saved in recent_trips.txt)

    You can type station names in any capitals, landmarks such as USYD,
    Opera House or Airport, and the program suggests names if you misspell one.

FILES
    trip_planner.py   the program (run this)
    stations.txt      the network: 8 lines, 139 stations

ADVANCED CONCEPTS
    - Classes: the Network class stores the map and finds routes
    - Recursion: Network.reachable() calls itself to explore the map
    - File input/output: reads stations.txt, writes and reads recent_trips.txt
    - Exception handling: missing files, bad data lines, invalid numbers

NOTE
    Travel times are estimates, not official Transport for NSW timetables.
