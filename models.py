from database import db
from datetime import datetime


class ParkingSlot(db.Model):

    __tablename__ = "parking_slots"

    id = db.Column(db.Integer, primary_key=True)

    slot_number = db.Column(db.String(10), unique=True, nullable=False)

    status = db.Column(db.String(20), default="Available")

    vehicle_number = db.Column(db.String(30))

    owner_name = db.Column(db.String(80))

    phone_number = db.Column(db.String(20))

    booking_time = db.Column(db.String(50))

    manually_booked = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Slot {self.slot_number}>"


class VehicleHistory(db.Model):
    __tablename__ = 'vehicle_history'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(30), nullable=False)
    owner_name = db.Column(db.String(80))
    phone_number = db.Column(db.String(20))
    slot_number = db.Column(db.String(10))
    entry_time = db.Column(db.String(50))
    exit_time = db.Column(db.String(50))
    duration = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'owner_name': self.owner_name,
            'phone_number': self.phone_number,
            'slot_number': self.slot_number,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'duration': self.duration
        }