from models import db, User, ParkingLot, ParkingSpot, Reservation, SpotStatus
import datetime

# 1. Create Admin User (if not exists)
def create_indian_admin():
    admin = User.query.filter_by(username="bharat_admin", role="admin").first()
    if admin is None:
        new_admin = User(
            username="bharat_admin",
            password="bharat123",  # Use hashed passwords in production
            email="admin@india.com",
            address="Admin Bhawan, New Delhi",
            state="Delhi",
            city="New Delhi",
            role="admin"
        )
        db.session.add(new_admin)
        db.session.commit()
        print("Indian admin user created.")
    else:
        print("Indian admin user already exists.")

# 2. Add a Parking Lot with Spots and Reservation
def add_parking_lot(location, price, address, pin_code, max_spots, reserved_index, vehicle_number, user_id=1):
    lot = ParkingLot(
        prime_location_name=location,
        price=price,
        address=address,
        pin_code=pin_code,
        maximum_number_of_spots=max_spots
    )
    spots = []
    for i in range(max_spots):
        status = SpotStatus.OCCUPIED if i == reserved_index else SpotStatus.AVAILABLE
        spot = ParkingSpot(lot=lot, status=status)
        spots.append(spot)
    db.session.add(lot)
    db.session.add_all(spots)
    db.session.commit()

    # Add reservation for the reserved spot
    reserved_spot = spots[reserved_index]
    reservation = Reservation(
        spot=reserved_spot,
        user_id=user_id,
        parking_timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=1 + reserved_index),
        leaving_timestamp=None,
        parking_cost=0.0,
        vehicle_number=vehicle_number
    )
    db.session.add(reservation)
    db.session.commit()
    print(f"Lot '{location}' with {max_spots} spots added.")

# 3. Seed All Data
def seed_indian_data():
    if ParkingLot.query.first() is not None:
        print("Parking lots already exist. Skipping seeding.")
        return

    add_parking_lot(
        location="Andheri East",
        price=60.0,
        address="Andheri Kurla Road, Mumbai",
        pin_code="400059",
        max_spots=2,
        reserved_index=1,
        vehicle_number="MH01AB1234"
    )
    add_parking_lot(
        location="Connaught Place",
        price=80.0,
        address="Rajiv Chowk, New Delhi",
        pin_code="110001",
        max_spots=3,
        reserved_index=1,
        vehicle_number="DL3CAB5678"
    )
    add_parking_lot(
        location="MG Road",
        price=70.0,
        address="MG Road, Bengaluru",
        pin_code="560001",
        max_spots=2,
        reserved_index=1,
        vehicle_number="KA02CD4321"
    )
    print("All Indian parking lots and reservations added.")

# 4. Initialize the Database
def setup_indian_parking_db():
    db.create_all()
    create_indian_admin()
    seed_indian_data()
    print("Database setup complete.")

# To run everything, just call:
# setup_indian_parking_db()
