def calculate_room_price(hours):
    base_price = 45000
    additional_hour_price = 9000
    total_price = base_price

    if hours > 6:
        additional_hours = hours - 6
        total_price += additional_hours * additional_hour_price

    return total_price

class Room:
    def __init__(self, room_number):
        self.room_number = room_number
        self.status = "disponible"  # "disponible", "ocupada", "limpieza"
        self.hours_booked = 0

    def book_room(self, hours):
        if self.status == "disponible":
            self.status = "ocupada"
            self.hours_booked = hours
            return True
        return False

    def set_cleaning(self):
        if self.status == "ocupada":
            self.status = "limpieza"
            self.hours_booked = 0

    def set_available(self):
        if self.status == "limpieza":
            self.status = "disponible"

    def checkout(self):
        if self.status == "ocupada":
            price = calculate_room_price(self.hours_booked)
            self.set_cleaning()
            return price
        return 0

class RoomManager:
    def __init__(self, conn):
        self.conn = conn
        self.rooms = [Room(i) for i in range(1, 23)]  # 22 rooms

    def find_available_room(self):
        for room in self.rooms:
            if room.status == "disponible":
                return room
        return None

    def book_room(self, hours):
        room = self.find_available_room()
        if room:
            room.book_room(hours)
            return room.room_number
        return None

    def checkout_room(self, room_number):
        for room in self.rooms:
            if room.room_number == room_number:
                return room.checkout()
        return 0

    def get_room_status(self):
        return [(room.room_number, room.status) for room in self.rooms]

    def set_room_cleaning(self, room_number):
        for room in self.rooms:
            if room.room_number == room_number:
                room.set_cleaning()

    def set_room_available(self, room_number):
        for room in self.rooms:
            if room.room_number == room_number:
                room.set_available()