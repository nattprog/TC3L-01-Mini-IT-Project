from flask import Flask, redirect, url_for, render_template, session, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = 'sessionsecretkey'
search = None

# Database for block, floor, and number of rooms.
class fci_room(db.Model):
        __tablename__ = "fci_room"
        id = db.Column(db.Integer, primary_key=True, nullable=False)
        room_name = db.Column(db.String(50), nullable=False )
        room_block = db.Column(db.String(1), nullable=False)
        room_floor = db.Column(db.Integer, nullable=False)
        room_number = db.Column(db.Integer, nullable=False)
        room_status = db.Column(db.Integer, nullable=False)
        def __repr__(self, id, room_name, room_block, room_floor, room_number, room_status):
            self.id = id
            self.room_name = room_name
            self.room_block = room_block
            self.room_floor = room_floor
            self.room_number = room_number
            self.room_status = room_status

class room_aliases(db.Model):
    __tablename__ = "room_aliases"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    fci_room_id = db.Column(db.Integer, db.ForeignKey("fci_room.id"), nullable=False)
    room_name_aliases = db.Column(db.String(50), nullable=False)

# Database for user info
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# -------------------------------------------------------

@app.route("/")
def redirect_home():
    return redirect("/map/0")

floor_markers = {
    '0': [
        {'lat': 2.9285, 'lng': 101.6411, 'popup': 'Marker 0-1'},
        {'lat': 2.9286, 'lng': 101.6412, 'popup': 'Marker 0-2'},
    ],
    '1': [
        {'lat': 2.9290, 'lng': 101.6405, 'popup': 'Marker 1-1'},
        {'lat': 2.9291, 'lng': 101.6406, 'popup': 'Marker 1-2'},
    ],
}

@app.route("/get_markers/<floor>")
def get_markers(floor):
    markers = floor_markers.get(floor, [])
    return jsonify(markers)

@app.route("/map/<floor>/", methods=["GET", "POST"])
def home(floor):
    search = None
    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")
    markers = floor_markers.get(floor,[])
    return render_template("index.html", ActivePage="index", ActiveFloor = floor, markers = markers)

@app.route("/roompage/<room_name>", methods=["GET", "POST"])
def room_page(room_name):
    room = db.session.execute(db.select(fci_room).filter_by(room_name = room_name)).scalar()
    search = None
    if request.method == "POST":
        try:
            request.form["search"]
        except:
            pass
        else:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        try:
            request.form["room_status"]
        except:
            pass
        else:
            room_status = int(request.form["room_status"])
            if (int(room.room_status) < 5) and (room_status > 0):
                room.room_status = int(room.room_status) + int(room_status)
            elif (int(room.room_status) > -5) and (room_status < 0):
                room.room_status = int(room.room_status) + int(room_status)
            db.session.commit()

    room_status = room.room_status
    if abs(room_status) == 0:
        room_status_modifier = ""
    if 1 <= abs(room_status) <= 2:
        room_status_modifier = "Likely"
    elif 3 <= abs(room_status) <= 4:
        room_status_modifier = "Probably"
    elif abs(room_status) == 5:
        room_status_modifier = "Definitely"
    
    if room_status == 0:
        room_status = "Unknown"
    elif room_status > 0:
        room_status = "Empty"
    elif room_status < 0:
        room_status = "Occupied"
    
    return render_template("roompage.html", room_name = room.room_name, room_block = room.room_block, room_floor = room.room_floor, room_number = room.room_number, room_status = room_status, room_status_modifier = room_status_modifier)

@app.route("/account/", methods=["GET", "POST"])
def account():
    return redirect("/signup")

@app.route("/search/<search>", methods=["GET", "POST"])
def search(search):
    session["search"] = search
    search_results = db.session.execute(db.select(fci_room).filter_by(room_name = search)).all()

    results_list = []
    for i in range(len(search_results)):
        for ii in range(len(search_results[i])):
            results_list.append(search_results[i][ii].room_name)
    
    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")
    return render_template("search.html", ActivePage="search", search=session["search"], results_list=results_list)

# -------------------------------------------------------

@app.route('/signup_success')
def signup_success():
    return render_template('signup_success.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Password validation
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'[0-9]', password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return render_template('signup.html', error="Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.")

        # Check if the username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                return render_template('signup.html', error="Username already registered.", login_link=True)
            elif existing_user.email == email:
                return render_template('signup.html', error="Email address already registered.", login_link=True)

        # Hash the password using pbkdf2:sha256
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('signup_success'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        # Check if the user exists and verify the password
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect("/")
        else:
            return render_template('login.html', error="Invalid email or password.")

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Change password route
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.get(session['user_id'])

        if not check_password_hash(user.password, current_password):
            return render_template('change_password.html', error="Current password is incorrect.")

        if len(new_password) < 8 or not re.search(r'[A-Z]', new_password) or not re.search(r'[a-z]', new_password) or not re.search(r'[0-9]', new_password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            return render_template('change_password.html', error="New password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.")

        # Check if new password and confirmation match
        if new_password != confirm_password:
            return render_template('change_password.html', error="New password and confirmation password do not match.")

        # Hash the new password before storing it in the database
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        user.password = hashed_password
        db.session.commit()

        # Redirect to the login page after successful password change
        return redirect(url_for('login'))

    return render_template('change_password.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
