import time
import json
import heapq
import os
SAVE_FILE ="data.json"


# Defining necessary classes
class RideRequest:
    def __init__(self, name, destination, slot, year, seq, timestamp = None):
        self.name = name.strip()
        self.destination = destination.strip().title()
        self.slot = slot.strip().title()
        self.year = int(year)
        self.seq = seq
        self.timestamp = timestamp if timestamp is not None else time.time()

    def __str__(self):
        return f"{self.name} | Year {self.year} | {self.destination.title()} ({self.slot.title()})"

    def to_dict(self):
        """Turns this request into a plain dict that json can save."""
        return {
            "name": self.name,
            "destination": self.destination,
            "slot": self.slot,
            "year": self.year,
            "seq": self.seq,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d):
        """Builds a RideRequest from a dict (the reverse of to_dict)."""
        return cls(d["name"], d["destination"], d["slot"], d["year"], d["seq"],
                   timestamp=d["timestamp"])


class Cab:
    def __init__(self, driver_name, destination, slot, seats=4, students_list=None, is_dispatched=False):
        self.name = driver_name.strip()
        self.destination = destination.strip().title()
        self.slot = slot.strip().title()  
        seats = int(seats)
        if not 1 <= seats <= 4:
            raise ValueError(f"seats must be 1-4, got {seats}")
        self.seats = seats
        self.students_list = list(students_list) if students_list is not None else []
        self.is_dispatched = bool(is_dispatched)

    def __str__(self):
        status = "Left" if self.is_dispatched else "Open"
        seats_taken = len(self.students_list)
        return f"Driver {self.name} | {self.destination} ({self.slot}) | Seats: {seats_taken}/{self.seats} | Status: {status}"

    def to_dict(self):
        """Turns this cab (and the students inside it) into a plain dict."""
        return {
            "driver_name": self.name,
            "destination": self.destination,
            "slot": self.slot,
            "seats": self.seats,
            "students_list": [s.to_dict() for s in self.students_list],
            "is_dispatched": self.is_dispatched,
        }

    @classmethod
    def from_dict(cls, d):
        """Builds a Cab from a dict. students_list and is_dispatched are optional,
        so the same method works for cabs.json (bare cabs) and data.json (saved cabs)."""
        students = [RideRequest.from_dict(s) for s in d.get("students_list", [])]
        return cls(d["driver_name"], d["destination"], d["slot"], d["seats"],
                   students, d.get("is_dispatched", False))


# Defining functions used
def get_valid_input(prompt:str, valid_options:list):
    """Prompts the user until a valid choice is provided."""
    while True:
        value = input(prompt).strip()
        if value.lower() in valid_options:
            return value.title()
        print(f"Invalid option. Choose from: {', '.join(valid_options)}")

def get_valid_year():
    """Prompts until a valid year between 1 and 5 is entered."""
    while True:
        year_str = input("Enter year of study (1-5): ").strip()
        if year_str.isdecimal() and 1 <= int(year_str) <= 5:
            return int(year_str)
        print("Invalid year! Must be a number between 1 and 5.")

def match_cabs(cabs: list, waiting_requests: dict) -> dict:
    match_preview = {}

    remaining = {}
    for trip, heap in waiting_requests.items():
        requests_only = []                           
        for item in sorted(heap):
            requests_only.append(item[2])
        remaining[trip] = requests_only         # Now remaiang is dict of {(destination,slot):[list of req sorted on basis of year,seq]}

    for cab in cabs:
        if cab.is_dispatched:
            continue
        key = (cab.destination, cab.slot)
        waiting = remaining.get(key, [])
        match_preview[cab] = waiting[:cab.seats]
        remaining[key] = waiting[cab.seats:]
    return match_preview

def dispatch_cab(cab:Cab, waiting_requests:dict):
    key = (cab.destination, cab.slot)
    heap = waiting_requests.get(key, [])
    if not heap:
        return cab.is_dispatched
    boarding = []
    while heap and len(boarding) < cab.seats:
        _, _, req = heapq.heappop(heap)
        boarding.append(req)
    cab.students_list = boarding
    if not heap:
        del waiting_requests[key]                                               # Deleting empty keys from waiting requests
    cab.is_dispatched = True
    return cab.is_dispatched

def has_cab(key,cabs:list):
    for c in cabs:
        if not c.is_dispatched and (c.destination,c.slot) == key:
            return True
    return False

def save_state(cabs:list[Cab],waiting_requests:dict,next_seq:int):
    cab_data = [cab.to_dict() for cab in cabs]
    waiting_data = []                                              # Now remaiang is dict of {(destination,slot):[list of req sorted on basis of year,seq]}
    for heap in waiting_requests.values():
        for _,_,req in sorted(heap):
            waiting_data.append(req.to_dict())
    saving_data = {
        "next_seq":next_seq,
        "cab_data":cab_data,
        "waiting_data":waiting_data
        }
    try:
        tmp_file = SAVE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(saving_data, f, indent=4)                     # usinf Os.replace so that file data is swapped only once and to avoid any errors that may be
        os.replace(tmp_file, SAVE_FILE)                             # brought up later due to incomplete files [file is either complete old or complete new version]
    except OSError as e:
        print(f"Warning: could not save data ({e}). Continuing without saving.")

def load_state():
    try:                                                            # Handeling errors while acessing a file
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("No previous save found. Starting new.")
        return None                     
    except (OSError, ValueError) as e:
        print(f"Warning: could not read {SAVE_FILE} ({e}). Starting fresh.")
        return None
    try:                                                            # Handeling errors while reading a file
        next_seq = int(data["next_seq"])
        waiting_requests = {}
        cabs = [Cab.from_dict(c) for c in data["cab_data"]]
        for d in data["waiting_data"]:
            req = RideRequest.from_dict(d)
            key=(req.destination,req.slot)
            heapq.heappush(waiting_requests.setdefault(key, []), (-req.year, req.seq, req))
    
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        print(f"Warning: {SAVE_FILE} is damaged ({e}). Starting fresh.")
        return None
    return cabs, waiting_requests, next_seq

if  __name__ == "__main__":
    
    # Needed variables
    valid_destinations = ["delhi","jaipur"]                              # Available destinations
    valid_slots = ["morning","afternoon","evening","night"]              # Valid Slots
    waiting_requests = {}
    next_seq = 0
    cabs = []
    cabs_error = False

    # Reading Cabs data and storing in all_cabs list
    try:
        with open("cabs.json","r") as f:
            cabs_data = json.load(f)
        for c in cabs_data:
            cabs.append(Cab.from_dict(c))                                  # in case of a bad entry those above it are stil entered to the list
    except FileNotFoundError:
        print("Warning: cabs.json not found. Starting with 0 cabs.")
        cabs_error = True
    except Exception as e:
        print(f"Cabs.json could not be read-{e} ")
        cabs_error = True



    #printables
    title_text = """========================================
CAB POOL (BITS-PILANI) - MAIN MENU"""
    menu_text = """========================================
1. Add a New Ride Request
2. View All Cabs & Waiting Requests
3. Find Matches (Preview Seat Allocation)
4. Dispatch a Cab
5. Quit
========================================"""

    # Loading save state
    state = load_state()
    if state is not None:
        cabs, waiting_requests, next_seq = state
        if cabs_error:
            print("Loaded cabs and requests from data.json (cabs.json couldn't be read.).")
        else:
            print("Loaded previous session from data.json (cabs.json is ignored while a save exists).")
        print("(delete data.json to get a fresh start)")


    # Infinite Loop for menu
    print(title_text)
    while True:
        print(menu_text)
        choice = input("Enter your choice (1-5):")
        if choice == "1":
            name = input("Enter student name: ").strip().title()
            destination = get_valid_input("Enter destination (Delhi/Jaipur): ",valid_destinations )
            slot = get_valid_input("Enter slot (Morning/Afternoon/Evening/Night): ", valid_slots)
            year = get_valid_year()

            req = RideRequest(name, destination, slot, year, next_seq)
            next_seq += 1
            key=(req.destination,req.slot)
            heapq.heappush(waiting_requests.setdefault(key, []), (-req.year, req.seq, req))
                # using - year because heap keeps smallest element first while here bigger year is prioritized
                # so we can just use -ve of year to rev the priority as now bigger year means smaller (-year)
            save_state(cabs, waiting_requests, next_seq)
            print(f"Successfully added ride request for {name}!")
            if not has_cab(key, cabs):
                print("No open cab for this trip right now. You're on the waiting list.")


            
        elif choice == "2":
            print("\n--- WAITING REQUESTS ---")
            if not waiting_requests:
                print("No students waiting.")
            else:
                for (dest, slot), req_list  in waiting_requests.items():
                    print(f"\nrequests for ({dest},{slot}) are-")
                    for Index, item in enumerate(sorted(req_list)):
                        print(f"{Index+1}-{item[2]}")


            print("\n--- CABS ---")
            if not cabs: 
                print("No Cabs loaded")
            else:
                for index,cab in enumerate(cabs,1):
                    print(f"{index}-{cab}")
        
    
        elif choice == "3": 
            match_preview = match_cabs(cabs, waiting_requests)
            print("\n--- MATCH PREVIEW ---")
            if not match_preview:
                print(" ↳ No open cabs available.")
            else:
                for cab, students in match_preview.items():
                    print(f"\nCab (Driver {cab.name} | {cab.destination} ({cab.slot}) | Seats: {len(students)}/{cab.seats} | Status: Open):")
                    if not students:
                        print(" No waiting students for this trip.")
                    else:
                        for index, student in enumerate(students, 1):
                            print(f"  {index}. {student}")

        
        elif choice=="4": 
            print("\n--- DISPATCH A CAB ---")
            open_cabs = [c for c in cabs if not c.is_dispatched]
            if not open_cabs:
                print("No open cabs to dispatch")
            else:
                cab_not_available = True
                dispatch_destination = get_valid_input("Enter destination (Delhi/Jaipur): ",valid_destinations )
                dispatch_slot = get_valid_input("Enter slot (Morning/Afternoon/Evening/Night): ", valid_slots)
                for selected_cab in open_cabs:
                    if selected_cab.destination == dispatch_destination and selected_cab.slot == dispatch_slot:
                        cab_not_available = False
                        if dispatch_cab(selected_cab, waiting_requests):
                            save_state(cabs, waiting_requests, next_seq)
                            names = ", ".join(s.name for s in selected_cab.students_list)
                            print(f"{selected_cab.name}'s cab left with ({len(selected_cab.students_list)}/{selected_cab.seats}): {names}")
                        else:
                            print("Nobody is waiting for this trip. Cab not dispatched.")
                        break
                if cab_not_available:
                    print("No open cab is available for selected destination and slot")

        elif choice=="5":
            break #handling quit

        else: print("invalid input, valid inputs are(1-5)")
