import time
import json
import heapq

# Defining necessary classes
class RideRequest:
    def __init__(self, name, destination, slot, year, seq):
        self.name = name.strip()
        self.destination = destination.strip().title()
        self.slot = slot.strip().title()
        self.year = int(year)
        self.timestamp = time.time()
        self.seq = seq

    def __str__(self):
        return f"{self.name} | Year {self.year} | {self.destination.title()} ({self.slot.title()})"



class Cab:
    def __init__(self, driver_name, destination, slot, seats):
        self.name = driver_name.strip()
        self.destination = destination.strip().title()
        self.slot = slot.strip().title()  
        self.seats = int(seats)
        self.students_list = []
        self.is_dispatched = False           #Cab availability 

    def __str__(self):
        status = "Left" if self.is_dispatched else "Open"
        seats_taken = len(self.students_list)
        return f"Driver {self.name} | {self.destination} ({self.slot}) | Seats: {seats_taken}/{self.seats} | Status: {status}"


# Defining functions used
def get_valid_input(prompt, valid_options):
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
        if year_str.isdigit() and 1 <= int(year_str) <= 5:
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

def dispatch_cab(cab, waiting_requests):
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

def has_cab(key,cabs):
    for c in cabs:
        if not c.is_dispatched and (c.destination,c.slot) == key:
            return True
    return False


# Needed variables
valid_destinations = ["delhi","jaipur"]                              # Available destinations
valid_slots = ["morning","afternoon","evening","night"]              # Valid Slots
waiting_requests = {}
next_seq = 0
cabs = []

# Reading Cabs data and storing in all_cabs list
try:
    with open("cabs.json","r") as f:
        cabs_data = json.load(f)
    for c in cabs_data:
        new_cab = Cab(c["driver_name"], c["destination"], c["slot"], c["seats"])
        cabs.append(new_cab)
except FileNotFoundError:
    print("Warning: cabs.json not found. Starting with 0 cabs.")


#printables
title_text = """========================================
    CAB POOL MATCHER - MAIN MENU"""
menu_text = """========================================
1. Add a New Ride Request
2. View All Cabs & Waiting Requests
3. Find Matches (Preview Seat Allocation)
4. Dispatch a Cab
5. Quit
========================================"""

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
        """
            using - year because heap keeps smallest element first while here bigger year is prioritized
            so we can just use -ve of year to rev the priority as now bigger year means smaller (-year)
        """
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
                print(f"\nCab ({cab}):")
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
