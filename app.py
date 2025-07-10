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
    # 1. Find the parking lot by its ID, or show 404 if not found
    lot = ParkingLot.query.get_or_404(lot_id)

    # 2. Update the lot's details from the form
    lot.prime_location_name = request.form['prime_location_name']
    lot.address = request.form['address']
    lot.pin_code = request.form['pin_code']
    lot.price = float(request.form['price'])

    # 3. Find out how many spots the lot should have now
    new_max_spots = int(request.form['maximum_number_of_spots'])
    current_spots_count = len(lot.spots)
    lot.maximum_number_of_spots = new_max_spots

    # 4. Save the lot's new details to the database
    db.session.commit()

    # 5. If more spots are needed, add new available spots
    if new_max_spots > current_spots_count:
        spots_to_add = new_max_spots - current_spots_count
        for _ in range(spots_to_add):
            new_spot = ParkingSpot(lot_id=lot.id, status=SpotStatus.AVAILABLE)
            db.session.add(new_spot)
        db.session.commit()

    # 6. If fewer spots are needed, remove available spots (never remove occupied spots!)
    elif new_max_spots < current_spots_count:
        # Find all available spots in this lot
        available_spots = [spot for spot in lot.spots if spot.status == SpotStatus.AVAILABLE]
        spots_to_remove = current_spots_count - new_max_spots
        # Remove only as many available spots as needed
        for spot in available_spots[:spots_to_remove]:
            db.session.delete(spot)
        db.session.commit()

    # 7. Show a success message and redirect back
    flash('Parking lot updated!', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    # 1. Find the parking lot by its ID, or show 404 if not found
    lot = ParkingLot.query.get_or_404(lot_id)

    # 2. Check if any spot in this lot is occupied
    for spot in lot.spots:
        if spot.status == SpotStatus.OCCUPIED:
            flash('Cannot delete lot: one or more spots are currently occupied.', 'danger')
            # Go back to the previous page or admin dashboard
            return redirect(request.referrer or url_for('admin_dashboard'))

    # 3. If all spots are free, delete the lot from the database
    db.session.delete(lot)
    db.session.commit()

    # 4. Show a success message and redirect back
    flash('Parking lot deleted!', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/delete_spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    # 1. Find the parking spot by its ID, or show 404 if not found
    spot = ParkingSpot.query.get_or_404(spot_id)

    # 2. Check if this spot has any reservations
    if spot.reservations:
        flash('Cannot delete spot: it has reservations.', 'danger')
        # Go back to the previous page or admin dashboard
        return redirect(request.referrer or url_for('admin_dashboard'))

    # 3. Find the lot this spot belongs to
    lot = spot.lot

    # 4. Delete the spot from the database
    db.session.delete(spot)
    db.session.commit()

    # 5. Update the lot's maximum number of spots
    lot.maximum_number_of_spots = len(lot.spots)
    db.session.commit()

    # 6. Show a success message and redirect back
    flash('Parking spot deleted!', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/reserve/<int:lot_id>', methods=['POST'])
def reserve_spot(lot_id):
    # 1. Check if the user is logged in and is a regular user
    user_id = session.get('user_id')
    user_role = session.get('role')
    if not user_id or user_role != 'user':
        return redirect(url_for('login'))
    # 2. Find the parking lot by its ID, or show 404 if not found
    lot = ParkingLot.query.get_or_404(lot_id)

    # 3. Find an available spot in this lot
    available_spot = ParkingSpot.query.filter_by(lot_id=lot.id, status=SpotStatus.AVAILABLE).first()

    # 4. If no spot is available, show a message and go back to dashboard
    if not available_spot:
        flash('No available spots in this lot.', 'danger')
        return redirect(url_for('user_dashboard'))
    # 5. Get the vehicle number from the form
    vehicle_number = request.form.get('vehicle_no')

    # 6. Create a new reservation for this spot and user
    new_reservation = Reservation(
        spot_id=available_spot.id,
        user_id=user_id,
        parking_timestamp=datetime.datetime.now(),
        parking_cost=0,  # Cost is 0 at reservation time
        vehicle_number=vehicle_number
    )
    # 7. Mark the spot as occupied
    available_spot.status = SpotStatus.OCCUPIED

    # 8. Save the reservation and update the spot in the database
    db.session.add(new_reservation)
    db.session.commit()

    # 9. Show a success message and go back to dashboard
    flash(f'Spot #{available_spot.id} reserved!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/release/<int:reservation_id>', methods=['POST'])
def release_spot(reservation_id):
    # 1. Find the reservation by its ID, or show 404 if not found
    reservation = Reservation.query.get_or_404(reservation_id)
    
    # 2. Check if the logged-in user owns this reservation
    current_user_id = session.get('user_id')
    if reservation.user_id != current_user_id:
        flash('You are not allowed to release this spot.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # 3. If the spot is already released, inform the user
    if reservation.leaving_timestamp is not None:
        flash('This spot has already been released.', 'info')
        return redirect(url_for('user_dashboard'))
    
    # 4. Set the leaving time to now
    now = datetime.datetime.now()
    reservation.leaving_timestamp = now
    
    # 5. Calculate the parking duration in hours
    parked_time = reservation.leaving_timestamp - reservation.parking_timestamp
    hours_parked = parked_time.total_seconds() / 3600  # convert seconds to hours
    
    # 6. Calculate the cost (lot.price is the price per hour)
    lot = reservation.spot.lot
    cost = round(hours_parked * lot.price, 2)
    reservation.parking_cost = cost
    
    # 7. Mark the spot as available again
    reservation.spot.status = SpotStatus.AVAILABLE
    
    # 8. Save all changes to the database
    db.session.commit()
    
    # 9. Show a success message to the user
    flash(f'Spot released! Total cost: ₹{cost}', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/history')
def history():
    # Step 1: Check if user is logged in and is a 'user'
    user_id = session.get('user_id')
    user_role = session.get('role')
    if not user_id or user_role != 'user':
        # Step 2: Redirect to login if not logged in or not a user
        return redirect(url_for('login'))
    
    # Step 3: Get all reservations for this user, newest first
    user_reservations = Reservation.query.filter_by(user_id=user_id)\
                                         .order_by(Reservation.parking_timestamp.desc())\
                                         .all()
    
    # Step 4: Render the history page with these reservations
    return render_template('history.html', reservations=user_reservations)

if __name__ == '__main__':
    app.run(debug=True)
