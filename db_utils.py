from models import db, User
from models import db, User, ParkingLot, ParkingSpot, Reservation,SpotStatus
import datetime

def create_admin_user():
    """Creates a default admin user if it doesn't exist."""
    admin_user = User.query.filter_by(username="admin_user", role="admin").first()

    if not admin_user:
        admin = User(
            username="admin_user",
            password="admin123",  # You should hash this in production
            email="admin@example.com",  # Provide a valid email
            address="Admin Address",
            state="Admin State",
            city="Admin City",
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created!")
    else:
        print("Admin user already exists.")
 

def seed_dummy_data():
    if not ParkingLot.query.first():
        lots = []
 
        # 📍 Bandra, Mumbai
        mumbai_lot = ParkingLot(
            prime_location_name="Bandra West",
            price=50.0,
            address="Hill Road, Mumbai",
            pin_code="400050",
            maximum_number_of_spots=2
        )
        mumbai_spots = [
            ParkingSpot(lot=mumbai_lot, status=SpotStatus.AVAILABLE),
            ParkingSpot(lot=mumbai_lot, status=SpotStatus.OCCUPIED)
        ]
        mumbai_res = Reservation(
            spot=mumbai_spots[1],
            user_id=1,
            parking_timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
            leaving_timestamp=None,
            parking_cost=0.0,
            vehicle_number="MH12AB9999"
        )
        lots.append((mumbai_lot, mumbai_spots, mumbai_res))

        # 📍 Times Square, New York
        nyc_lot = ParkingLot(
            prime_location_name="Times Square",
            price=75.0,
            address="Broadway, New York, NY",
            pin_code="10036",
            maximum_number_of_spots=3
        )
        nyc_spots = [
            ParkingSpot(lot=nyc_lot, status=SpotStatus.AVAILABLE),
            ParkingSpot(lot=nyc_lot, status=SpotStatus.OCCUPIED),
            ParkingSpot(lot=nyc_lot, status=SpotStatus.AVAILABLE)
        ]
        nyc_res = Reservation(
            spot=nyc_spots[1],
            user_id=1,
            parking_timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=90),
            leaving_timestamp=None,
            parking_cost=0.0,
            vehicle_number="NY9876ZX"
        )
        lots.append((nyc_lot, nyc_spots, nyc_res))

        # 📍 Oxford Street, London
        london_lot = ParkingLot(
            prime_location_name="Oxford Street",
            price=65.0,
            address="Oxford Street, London",
            pin_code="W1D 1BS",
            maximum_number_of_spots=2
        )
        london_spots = [
            ParkingSpot(lot=london_lot, status=SpotStatus.AVAILABLE),
            ParkingSpot(lot=london_lot, status=SpotStatus.OCCUPIED)
        ]
        london_res = Reservation(
            spot=london_spots[1],
            user_id=1,
            parking_timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=3),
            leaving_timestamp=None,
            parking_cost=0.0,
            vehicle_number="UK19CAR001"
        )
        lots.append((london_lot, london_spots, london_res))

        # 🔄 Save everything
        for lot, spots, res in lots:
            db.session.add(lot)
            db.session.add_all(spots)
            db.session.add(res)

        db.session.commit()
        print("✅ Multiple dummy lots seeded successfully.")


def initialize_database():
    """Creates database tables and ensures the admin user exists."""
    db.create_all()
    create_admin_user()  # Call the separate function
    seed_dummy_data()
    print("Database initialized successfully!")
