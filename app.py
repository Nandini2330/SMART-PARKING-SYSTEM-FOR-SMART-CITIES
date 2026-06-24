from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from config import Config
from database import db
from models import ParkingSlot, VehicleHistory
from sensor import get_random_status
from datetime import datetime
import random
import io
import csv

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


# -----------------------------
# Create database and sample slots
# -----------------------------
with app.app_context():
    db.create_all()

    if ParkingSlot.query.count() == 0:
        # Generate slots A1-A10 through E1-E10
        rows = ['A', 'B', 'C', 'D', 'E']
        for r in rows:
            for n in range(1, 11):
                slot_number = f"{r}{n}"
                slot = ParkingSlot(
                    slot_number=slot_number,
                    status="Available",
                    vehicle_number="",
                    owner_name="",
                    phone_number="",
                    booking_time="",
                    manually_booked=False
                )
                db.session.add(slot)

        db.session.commit()


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/")
def dashboard():

    slots = ParkingSlot.query.order_by(ParkingSlot.slot_number).all()

    available = ParkingSlot.query.filter_by(status="Available").count()

    occupied = ParkingSlot.query.filter_by(status="Occupied").count()

    total = ParkingSlot.query.count()

    occupancy = round((occupied / total) * 100, 2) if total else 0

    # Vehicles entered/exited today (from history)
    today = datetime.now().strftime('%Y-%m-%d')
    entered_today = VehicleHistory.query.filter(VehicleHistory.entry_time.like(f"%{today}%")).count()
    exited_today = VehicleHistory.query.filter(VehicleHistory.exit_time.like(f"%{today}%")).count()

    revenue = 0

    return render_template(
        "dashboard.html",
        slots=slots,
        available=available,
        occupied=occupied,
        total=total,
        occupancy=occupancy,
        entered_today=entered_today,
        exited_today=exited_today,
        revenue=revenue
    )


# API: Get slots JSON
@app.route('/api/slots')
def api_slots():
    slots = ParkingSlot.query.order_by(ParkingSlot.slot_number).all()
    data = []
    for s in slots:
        data.append({
            'id': s.id,
            'slot_number': s.slot_number,
            'status': s.status,
            'vehicle_number': s.vehicle_number,
            'owner_name': s.owner_name,
            'phone_number': s.phone_number,
            'booking_time': s.booking_time,
            'manually_booked': s.manually_booked
        })
    return jsonify(data)


# -----------------------------
# Book Parking Slot
# -----------------------------
@app.route('/api/book', methods=['POST'])
def api_book():
    data = request.json or request.form
    slot_id = data.get('slot_id')
    vehicle_number = data.get('vehicle_number')
    owner_name = data.get('owner_name')
    phone_number = data.get('phone_number')

    slot = ParkingSlot.query.get_or_404(slot_id)
    if slot.status == 'Occupied' and slot.manually_booked:
        return jsonify({'success': False, 'message': 'Slot already manually booked'}), 400

    slot.status = 'Occupied'
    slot.vehicle_number = vehicle_number
    slot.owner_name = owner_name
    slot.phone_number = phone_number
    slot.booking_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    slot.manually_booked = True

    # Add history entry (entry_time set now)
    h = VehicleHistory(
        vehicle_number=vehicle_number,
        owner_name=owner_name,
        phone_number=phone_number,
        slot_number=slot.slot_number,
        entry_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        exit_time='',
        duration=''
    )
    db.session.add(h)

    db.session.commit()

    return jsonify({'success': True})


# -----------------------------
# Cancel Booking
# -----------------------------
@app.route('/api/cancel', methods=['POST'])
def api_cancel():
    data = request.json or request.form
    slot_id = data.get('slot_id')
    slot = ParkingSlot.query.get_or_404(slot_id)

    # find latest history entry for this vehicle and set exit
    latest = None
    if slot.vehicle_number:
        latest = VehicleHistory.query.filter_by(vehicle_number=slot.vehicle_number, slot_number=slot.slot_number).order_by(VehicleHistory.id.desc()).first()

    exit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if latest and not latest.exit_time:
        entry_dt = datetime.strptime(latest.entry_time, '%Y-%m-%d %H:%M:%S')
        exit_dt = datetime.strptime(exit_time, '%Y-%m-%d %H:%M:%S')
        duration = str(exit_dt - entry_dt)
        latest.exit_time = exit_time
        latest.duration = duration

    slot.status = 'Available'
    slot.vehicle_number = ''
    slot.owner_name = ''
    slot.phone_number = ''
    slot.booking_time = ''
    slot.manually_booked = False

    db.session.commit()

    return jsonify({'success': True})


# -----------------------------
# Random Sensor Update
# -----------------------------
@app.route('/random')
def random_update():
    slots = ParkingSlot.query.all()

    for slot in slots:
        # Do not override manually booked slots
        if slot.manually_booked:
            continue

        if random.randint(0, 100) < 20:
            new_status = get_random_status()
            slot.status = new_status
            if new_status == 'Available':
                slot.vehicle_number = ''
                slot.owner_name = ''
                slot.phone_number = ''
                slot.booking_time = ''

    db.session.commit()
    return jsonify({'success': True})


# -----------------------------
# Reset Parking
# -----------------------------
@app.route('/reset')
def reset():
    slots = ParkingSlot.query.all()
    for slot in slots:
        slot.status = 'Available'
        slot.vehicle_number = ''
        slot.owner_name = ''
        slot.phone_number = ''
        slot.booking_time = ''
        slot.manually_booked = False

    # add no history entries on reset
    db.session.commit()
    return jsonify({'success': True})


@app.route('/history')
def history():
    rows = VehicleHistory.query.order_by(VehicleHistory.id.desc()).all()
    return render_template('history.html', rows=rows)


@app.route('/export_csv')
def export_csv():
    rows = VehicleHistory.query.order_by(VehicleHistory.id.desc()).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID','Vehicle Number','Owner Name','Phone','Slot','Entry Time','Exit Time','Duration'])
    for r in rows:
        cw.writerow([r.id,r.vehicle_number,r.owner_name,r.phone_number,r.slot_number,r.entry_time,r.exit_time,r.duration])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='vehicle_history.csv')


@app.route('/analytics')
def analytics():
    # Prepare data for charts
    total = ParkingSlot.query.count()
    available = ParkingSlot.query.filter_by(status='Available').count()
    occupied = ParkingSlot.query.filter_by(status='Occupied').count()

    # entries per day (last 7 days)
    from datetime import timedelta
    labels = []
    entered = []
    exited = []
    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        label = day.strftime('%Y-%m-%d')
        labels.append(label)
        e = VehicleHistory.query.filter(VehicleHistory.entry_time.like(f"%{label}%")).count()
        x = VehicleHistory.query.filter(VehicleHistory.exit_time.like(f"%{label}%")).count()
        entered.append(e)
        exited.append(x)

    return render_template('analytics.html', total=total, available=available, occupied=occupied, labels=labels, entered=entered, exited=exited)


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)