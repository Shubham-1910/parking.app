import enum
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()  
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Enum

class SpotStatus(enum.Enum):
    OCCUPIED = "O"
    AVAILABLE = "A"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    address = db.Column(db.String, nullable=True)
    state = db.Column(db.String, nullable=True)
    city = db.Column(db.String, nullable=True)
    reservations = db.relationship("Reservation", back_populates="user")
    role = db.Column(db.String, nullable=False, default='user')  # 'admin' or 'user'

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    prime_location_name = db.Column(String, nullable=False)
    price = db.Column(Float, nullable=False)
    address = db.Column(String, nullable=False)
    pin_code = db.Column(String, nullable=False)
    maximum_number_of_spots = db.Column(Integer, nullable=False)
    spots = db.relationship("ParkingSpot", back_populates="lot", cascade="all, delete-orphan")

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    lot_id = db.Column(Integer, ForeignKey('parking_lots.id'), nullable=False)
    status = db.Column(Enum(SpotStatus), default=SpotStatus.AVAILABLE, nullable=False)
    lot = db.relationship("ParkingLot", back_populates="spots")
    reservations = db.relationship("Reservation", back_populates="spot", cascade="all, delete-orphan")
 
class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    spot_id = db.Column(Integer, ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    parking_timestamp = db.Column(DateTime, default=datetime.datetime.utcnow)
    leaving_timestamp = db.Column(DateTime, nullable=True)
    parking_cost = db.Column(Float, nullable=False)
    vehicle_number = db.Column(String, nullable=False)   
    spot = db.relationship("ParkingSpot", back_populates="reservations")
    user = db.relationship("User", back_populates="reservations")


# Initialize the datadb.Model
def init_db(app):
    db.init_app(app)

