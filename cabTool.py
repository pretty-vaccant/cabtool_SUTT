import time
import json

# Defining necessary classes
class RideRequest:
    def __init__(self, name, destination, slot, year):
        self.name = name.strip()
        self.destination = destination.strip().title()
        self.slot = slot.strip().title()
        self.year = int(year)
        self.timestamp = time.time()

    def __str__(self):
        return f"{self.name} | Year {self.year} | {self.destination.title()} ({self.slot.title()})"


class Cab:
    def __init__(self, driver_name, destination, slot, seats):
        self.name = driver_name.strip()
        self.destination = destination.strip().title()
        self.slot = slot.strip().title()  
        self.seats = int(seats)
        self.students_list = []
        self.is_dispatched = False           #Cab avialability 

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
    waiting_requests2=waiting_requests.copy()
    for cab in cabs:
        if cab.is_dispatched:
            continue
        else:
            key = (cab.destination, cab.slot)
            waiting = waiting_requests2.get(key, [])
            match_preview[cab] = waiting[:cab.seats]
            waiting_requests2[key] = waiting[cab.seats:]
    return match_preview



# Needed variables
valid_destinations = ["delhi","jaipur"]                              # Avialable destinaions
valid_slots = ["morning","afternoon","evening","night"]              # Valid Slots
waiting_requests = {}
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

        req = RideRequest(name, destination, slot, year)
        key=(req.destination,req.slot)
        waiting_requests.setdefault(key,[]).append(req)
        print(f"Successfully added ride request for {name}!")


        
    elif choice == "2":
        print("\n--- WAITING REQUESTS ---")
        if not waiting_requests:
            print("No students waiting.")
        else:
            for (dest, slot), req_list  in waiting_requests.items():
                print(f"\nrequests for ({dest},{slot}) are-")
                for Index,req in enumerate(req_list):
                    print(f"{Index+1}-{req}")


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

    
    elif choice=="4": print("coming soon")

    elif choice=="5":
        break #handeling quit

    else: print("invalid input, valid inputs are(1-5)")
