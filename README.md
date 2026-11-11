# Cab Pool Matcher (BITS Pilani)

A command-line app that collects cab ride requests from students, queues them per trip (destination + time slot), and fills cabs with the most senior students first. Built for the SUTT Back-End Developer Recruitment, Task 1.

## How to run

Requirements: Python 3.9 or newer. Only the standard library is used, so there is no `requirements.txt` to install.

```bash
python main.py
```

Put a `cabs.json` file in the same folder before you start. A sample is included in this repo.

## Files

| File | Purpose |
|---|---|
| `main.py` | The whole app: classes, matching and dispatch logic, saving and loading, and the menu |
| `cabs.json` | The list of cabs, edited by you (format below) |
| `data.json` | The saved state, created and managed by the app. Not meant to be edited |
| `README.md` | This file |

## Menu

```
1. Add a New Ride Request
2. View All Cabs & Waiting Requests
3. Find Matches (Preview Seat Allocation)
4. Dispatch a Cab
5. Quit
```

1. **Add a request:** enter a name, destination, slot and year (1-5). The destinations are currently Delhi and Jaipur, and the slots are currently Morning, Afternoon, Evening and Night. Invalid input shows an error and asks again. The name can be left blank, so anonymous requests are allowed. The request joins the waiting list for its trip; nobody gets a seat yet.
2. **View everything:** waiting students for every trip (in priority order) and all cabs, both open and already left, with seats taken (like `3/4`).
3. **Find matches:** a preview of who would get a seat in each open cab right now. Nothing changes: no one is seated and the waiting list stays as it is.
4. **Dispatch a cab:** pick a destination and slot. The first open cab for that trip is filled with the most senior waiting students (up to its seats) and marked as left.
5. **Quit.** Pressing Ctrl+C is also a safe way to exit (see "Saving" below).

## The cab file (`cabs.json`)

A JSON list, one object per cab. Cabs are used in the order they appear in the file, so results are the same every run.

```json
[
    {
        "driver_name": "Ramesh Kumar",
        "destination": "Delhi",
        "slot": "Morning",
        "seats": 4
    },
    {
        "driver_name": "Suresh Singh",
        "destination": "Jaipur",
        "slot": "Night",
        "seats": 3
    },
    {
        "driver_name": "Vikram Rathore",
        "destination": "Delhi",
        "slot": "Evening",
        "seats": 4
    }
]
```

| Field | Rules |
|---|---|
| `driver_name` | text |
| `destination` | one of the destinations in `valid_destinations` (currently `Delhi` or `Jaipur`). Not checked when loading, so a cab with any other destination can never be matched |
| `slot` | one of the slots in `valid_slots` (currently `Morning`, `Afternoon`, `Evening` or `Night`). Same note as above |
| `seats` | whole number from 1 to 4 (can differ between cabs) |

If the file is missing or invalid, the app prints a clear message instead of crashing. Cabs are read one by one, so if one entry is bad (for example `seats` is 5), the cabs above it are still loaded and the ones from the bad entry onward are not. Fix the file, then delete `data.json` and restart, because the app saves the cab list it has after the first change.

## Saving and loading

State is saved to `data.json` **after every change** (a new request, or a cab leaving). It stores the waiting students, which students are in which cab, which cabs have left, and a request counter used for ordering (see below). On the next start the app loads it and continues exactly where it left off.

`data.json` is created automatically the first time you run the app and make a change (add a request or dispatch a cab), so you never need to create it yourself. **It is managed by the app and is not meant to be edited or touched by hand.** Editing it can corrupt the saved state (a damaged file is detected, but the saved data would be lost and the app would start fresh).

- **Why JSON and not pickle:** JSON is human-readable, so the saved state can be inspected easily. Pickle is not readable, and loading a pickle file can run arbitrary code, so it is unsafe.
- **Crash safety:** the app writes to `data.json.tmp` first and then swaps it in with `os.replace`, so the save file is always either the complete old version or the complete new version, never half-written.
- **Ctrl+C:** because everything is saved right after each change, nothing is lost when the app is interrupted. Python may print a traceback on Ctrl+C, but no data is affected.
- **Missing or broken save file:** the app does not crash. It tells the user and starts fresh.
- **`cabs.json` vs `data.json`:** once a `data.json` exists, the cab list comes from it and `cabs.json` is ignored. To update the cab data (for example, to add a cab or change seats in `cabs.json`), or to start over, delete `data.json` first. Note that this also clears the waiting list and the record of cabs that have left.
- **If `cabs.json` breaks:** if `cabs.json` is missing or cannot be read but a `data.json` is available, the app does not lose the cabs. It loads them from `data.json` and tells the user.

## How it works

- `RideRequest` stores the student's name, destination, slot, year, a sequence number and the submit time.
- `Cab` stores the driver, destination, slot, seats (1-4), the list of students inside, and whether it has left.
- Both classes have `to_dict()` / `from_dict()` methods for saving and loading.
- There is **one priority queue (a `heapq` min-heap) per trip**, kept in a dictionary keyed by `(destination, slot)`. The queue belongs to the trip, not to any cab. Each entry is the tuple `(-year, seq, request)`. Using `-year` turns the min-heap into a max-heap, so 5th years come out first.
- Dispatch pops up to `seats` students from the trip's heap and puts them in the cab. The preview works on sorted copies of the heaps, so it never changes the real queues, and it goes through cabs in file order, so it matches what dispatch would actually do.

## Tricky situations

**1. Half-empty cab.** Any open cab can be dispatched even if it will not be full. It takes everyone waiting for its trip, up to its seats, and leaves with, say, 1/4. If nobody is waiting, it is not dispatched and the user sees a message.

**2. No cabs left.** Requests are accepted regardless of cabs. If there is no open cab for the trip, the student stays in the waiting queue and sees "No open cab for this trip right now. You're on the waiting list." Waiting students are saved to disk and shown in option 2, so they never disappear. If they are still waiting when a matching cab is available, dispatch picks them up.

**3. Same year.** Every request gets a unique, increasing `seq` number. The heap tuple is `(-year, seq, request)`, so two students of the same year are ordered by `seq`, meaning whoever asked first is seated first. Because `seq` is always unique, Python never needs to compare two `RideRequest` objects (which would crash). The counter is saved in `data.json`, so the order is kept after a restart.

**4. Lots of students.** Let `n` be the number of waiting requests and `c` the number of cabs (small).

| Operation | Time | Why |
|---|---|---|
| Add one request | O(log n) | One `heappush` into that trip's heap. The check for an open cab is a scan of `c` cabs, O(c). |
| Add all 1,000 requests | O(n log n) | n pushes at O(log n) each. |
| Dispatch one cab (up to 4 students) | O(log n) | At most 4 `heappop` calls, each O(log n). Finding the cab is O(c). |
| Find an open cab for a trip | O(c) | Linear scan over the cabs. Since `c` is tiny this is effectively constant, and it could be O(1) with a dictionary of open cabs per trip. |
| Preview (option 3) | O(n log n) | Sorts a copy of each heap so the real queues are untouched. |

**Cost of saving (honest note):** the app rewrites `data.json` after every change, and writing it sorts every heap and rewrites all data, which is O(n log n). So in practice each add or dispatch costs O(n log n) because of the save, not just O(log n), and entering 1,000 requests one by one is O(n² log n) in total. At campus scale this is instant, and it is a deliberate trade for never losing data. For much larger scale, an append-only log would make each change O(1).

## Design notes

- Duplicate requests (the same person asking twice) are not blocked, because the task does not ask for it.
- Blank names are allowed on purpose, for anonymous requests.
- Easy to extend: the valid destinations and time slots live in two lists (`valid_destinations` and `valid_slots`) in `main.py`. To support a new destination or slot, just add it to the matching list. Input checking and the rest of the app use those lists, so no other logic needs to change.
- Destinations, slots and years are checked when entered, and bad input gives a friendly message instead of a crash.
- Once a cab has left, it is no longer matched or dispatched, so nobody new can be added to it.
