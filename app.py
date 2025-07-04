from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, ParkingLot, ParkingSpot, Reservation, SpotStatus
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'
db.init_app(app)

# Helper function for session validation
def validate_session():
    if 'user_id' not in session or 'role' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    return None

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    result = validate_session()
    if result:
        return result
    role = session['role']
    if role == 'user':
        return redirect(url_for('user_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return "Invalid role!", 403

@app.route('/admin_dashboard')
def admin_dashboard():
    result = validate_session()
    if result:
        return result
    lots_data = ParkingLot.query.all()
    return render_template('admin_dashboard/adminUI.html', lots=lots_data, SpotStatus=SpotStatus)

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    lots = ParkingLot.query.all()
    reserve = Reservation.query.filter_by(user_id=session['user_id']).all()
    return render_template('user_dashboard/user_dashboard.html', lots=lots, reservations=reserve, SpotStatus=SpotStatus)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if "username" in session and "role" in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if len(password) > 10:
            return "Error: password must be less than 10 characters."
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    from static.constant import form_fields, stateCityMap
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        address = request.form['address']
        state = request.form['state']
        city = request.form['city']
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('signup'))
        new_user = User(
            username=username,
            password=password,
            email=email,
            address=address,
            state=state,
            city=city,
            role='user'
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('sign_up.html', form_fields=form_fields, stateCityMap=stateCityMap)

@app.route('/fetchUser')
def fetch_user():
    result = validate_session()
    if result:
        return result
    users = User.query.all()
    return render_template('admin_dashboard/user_list/user_list.html', users=users)

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    user = User.query.get_or_404(id)
    from static.constant import form_fields, stateCityMap
    if request.method == 'POST':
        user.username = request.form['username']
        user.password = request.form['password']
        user.email = request.form['email']
        user.address = request.form['address']
        user.state = request.form['state']
        user.city = request.form['city']
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('sign_up.html', user=user, form_fields=form_fields, stateCityMap=stateCityMap)

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    search_by = request.args.get('search_by', '') or request.form.get('search_by', '')
    query = request.args.get('query', '').strip() or request.form.get('query', '').strip()
    user_fields = ['user_id', 'username', 'user_email', 'user_address', 'user_city', 'user_state']
    lot_fields = ['lot_id', 'prime_location_name', 'lot_address', 'pin_code']
    spot_fields = ['spot_id', 'spot_status']
    reservation_fields = ['reservation_id', 'reservation_user_id', 'reservation_spot_id']
    parent_field = None
    if search_by in user_fields:
        parent_field = 'user'
    elif search_by in lot_fields:
        parent_field = 'lot'
    elif search_by in spot_fields:
        parent_field = 'spot'
    elif search_by in reservation_fields:
        parent_field = 'reservation'
    user_id = session.get('user_id')
    user_role = session.get('role')
    if user_role == 'admin':
        if search_by == 'user_id' and query.isdigit():
            results = User.query.filter(User.id == int(query)).all()
        elif search_by == 'username':
            results = User.query.filter(User.username.ilike(f"%{query}%")).all()
        elif search_by == 'user_email':
            results = User.query.filter(User.email.ilike(f"%{query}%")).all()
        elif search_by == 'user_address':
            results = User.query.filter(User.address.ilike(f"%{query}%")).all()
        elif search_by == 'user_city':
            results = User.query.filter(User.city.ilike(f"%{query}%")).all()
        elif search_by == 'user_state':
            results = User.query.filter(User.state.ilike(f"%{query}%")).all()
        elif search_by == 'lot_id' and query.isdigit():
            results = ParkingLot.query.filter(ParkingLot.id == int(query)).all()
        elif search_by == 'prime_location_name':
            results = ParkingLot.query.filter(ParkingLot.prime_location_name.ilike(f"%{query}%")).all()
        elif search_by == 'lot_address':
            results = ParkingLot.query.filter(ParkingLot.address.ilike(f"%{query}%")).all()
        elif search_by == 'pin_code':
            results = ParkingLot.query.filter(ParkingLot.pin_code.ilike(f"%{query}%")).all()
        elif search_by == 'spot_id' and query.isdigit():
            results = ParkingSpot.query.filter(ParkingSpot.id == int(query)).all()
        elif search_by == 'spot_status':
            results = ParkingSpot.query.filter(ParkingSpot.status == query.upper()).all()
        elif search_by == 'reservation_id' and query.isdigit():
            results = Reservation.query.filter(Reservation.id == int(query)).all()
        elif search_by == 'reservation_user_id' and query.isdigit():
            results = Reservation.query.filter(Reservation.user_id == int(query)).all()
        elif search_by == 'reservation_spot_id' and query.isdigit():
            results = Reservation.query.filter(Reservation.spot_id == int(query)).all()
    elif user_role == 'user':
        if search_by in ['reservation_user_id', 'reservation_id', 'reservation_spot_id']:
            if search_by == 'reservation_user_id' and query.isdigit() and int(query) == user_id:
                results = Reservation.query.filter(Reservation.user_id == user_id).all()
            elif search_by == 'reservation_id' and query.isdigit():
                reservation = Reservation.query.filter(Reservation.id == int(query), Reservation.user_id == user_id).first()
                if reservation:
                    results = [reservation]
            elif search_by == 'reservation_spot_id' and query.isdigit():
                results = Reservation.query.filter(Reservation.spot_id == int(query), Reservation.user_id == user_id).all()
        else:
            flash("Not authorized to search this information.", "danger")
            return redirect(url_for('search'))
    else:
        flash("Not authorized. Please log in.", "danger")
        return redirect(url_for('login'))
    return render_template('search.html', results=results, search_by=search_by, query=query, parent_field=parent_field, SpotStatus=SpotStatus)

@app.route('/add_lot', methods=['POST'])
def add_lot():
    prime_location_name = request.form['prime_location_name']
    address = request.form['address']
    pin_code = request.form['pin_code']
    price = float(request.form['price'])
    max_spots = int(request.form['maximum_number_of_spots'])
    lot = ParkingLot(
        prime_location_name=prime_location_name,
        address=address,
        pin_code=pin_code,
        price=price,
        maximum_number_of_spots=max_spots
    )
    db.session.add(lot)
    db.session.flush()
    for _ in range(max_spots):
        spot = ParkingSpot(lot_id=lot.id, status=SpotStatus.AVAILABLE)
        db.session.add(spot)
    db.session.commit()
    flash('Parking lot and spots added!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_lot/<int:lot_id>', methods=['POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    lot.prime_location_name = request.form['prime_location_name']
    lot.address = request.form['address']
    lot.pin_code = request.form['pin_code']
    lot.price = float(request.form['price'])
    new_spots_len = int(request.form['maximum_number_of_spots'])
    current_spots = len(lot.spots)
    lot.maximum_number_of_spots = new_spots_len
    db.session.commit()
    if new_spots_len > current_spots:
        for _ in range(new_spots_len - current_spots):
            new_spot = ParkingSpot(lot_id=lot.id, status=SpotStatus.AVAILABLE)
            db.session.add(new_spot)
        db.session.commit()
    elif new_spots_len < current_spots:
        available_spots = [spot for spot in lot.spots if spot.status == SpotStatus.AVAILABLE]
        spots_to_remove = current_spots - new_spots_len
        for spot in available_spots[:spots_to_remove]:
            db.session.delete(spot)
        db.session.commit()
    flash('Parking lot updated!', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    occupied_spots = [spot for spot in lot.spots if spot.status == SpotStatus.OCCUPIED]
    if occupied_spots:
        flash('Cannot delete lot: one or more spots are currently occupied.', 'danger')
        return redirect(request.referrer or url_for('admin_dashboard'))
    db.session.delete(lot)
    db.session.commit()
    flash('Parking lot deleted!', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/delete_spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.reservations:
        flash('Cannot delete spot: it has reservations.', 'danger')
        return redirect(request.referrer or url_for('admin_dashboard'))
    lot = spot.lot
    db.session.delete(spot)
    db.session.commit()
    lot.maximum_number_of_spots = len(lot.spots)
    db.session.commit()
    flash('Parking spot deleted!', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/reserve/<int:lot_id>', methods=['POST'])
def reserve_spot(lot_id):
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    lot = ParkingLot.query.get_or_404(lot_id)
    spot = ParkingSpot.query.filter_by(lot_id=lot.id, status=SpotStatus.AVAILABLE).first()
    if not spot:
        flash('No available spots in this lot.', 'danger')
        return redirect(url_for('user_dashboard'))
    vehicle_no = request.form.get('vehicle_no')
    reservation = Reservation(
        spot_id=spot.id,
        user_id=session['user_id'],
        parking_timestamp=datetime.datetime.now(),
        parking_cost=0,
        vehicle_number=vehicle_no
    )
    spot.status = SpotStatus.OCCUPIED
    db.session.add(reservation)
    db.session.commit()
    flash(f'Spot #{spot.id} reserved!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/release/<int:reservation_id>', methods=['POST'])
def release_spot(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != session.get('user_id'):
        flash('Unauthorized', 'danger')
        return redirect(url_for('user_dashboard'))
    if reservation.leaving_timestamp:
        flash('Spot already released.', 'info')
        return redirect(url_for('user_dashboard'))
    reservation.leaving_timestamp = datetime.datetime.now()
    lot = reservation.spot.lot
    duration_hours = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600
    reservation.parking_cost = round(duration_hours * lot.price, 2)
    reservation.spot.status = SpotStatus.AVAILABLE
    db.session.commit()
    flash(f'Spot released. Total cost: ₹{reservation.parking_cost}', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/history')
def history():
    if 'user_id' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    reservations = Reservation.query.filter_by(user_id=session['user_id']).order_by(Reservation.parking_timestamp.desc()).all()
    return render_template('history.html', reservations=reservations)

if __name__ == '__main__':
    app.run(debug=True)
