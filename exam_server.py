from flask import Flask, render_template, request, redirect, session, flash
from exam_mysqlconnection import connectToMySQL
import re
from flask_bcrypt import Bcrypt
app = Flask(__name__)   
app.secret_key='yoloswag'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)


@app.route('/')
def logreg():
    return render_template("login.html")

@app.route('/success')
def success():
    if 'userid' in session:
        mysql = connectToMySQL("exam")
        email_query = "SELECT * FROM exam.users WHERE email = %(em)s;"
        email_data = {
            "em": session['reg_email']
        }
        email = mysql.query_db(email_query, email_data)
        session['userid'] = email[0]['id']
        print(session['userid'])
        return render_template('dashboard.html')
    flash("Please register or login")
    return redirect('/')

@app.route('/dashboard')
def dash():
    if 'userid' in session:
        # GETTING TRIP LOCATION AND PLAN
        mysql = connectToMySQL("exam")
        userTrips_query = "SELECT * FROM exam.trips WHERE user_id = %(uid)s;"
        userTrips_data = {
            "uid": session['userid']
        }
        userTrips = mysql.query_db(userTrips_query, userTrips_data)

        return render_template("dashboard.html", alltrips = userTrips)
    flash("Please login to continue")
    return redirect('/')

@app.route('/remove_trip/<id>')
def remove_trip(id):
    if 'userid' in session:
        mysql = connectToMySQL("exam")
        tripDelete_query = "DELETE FROM exam.trips WHERE id = %(tid)s and user_id = %(uid)s;"
        tripDelete_data = {
            "tid": id,
            "uid": session['userid']
        }
        tripDeleted = mysql.query_db(tripDelete_query, tripDelete_data)
        return redirect('/dashboard')
    flash("Please login to continue")
    return redirect('/')

@app.route('/trips/edit/<id>')
def edit_trip_page(id):
    if 'userid' in session:
        session['trip_id'] = id

        return render_template('edit_trip.html')
    flash("Please login to continue")
    return redirect('/')

@app.route('/edit_trip', methods=['post'])
def edit_trip():
    if 'userid' in session:
        if request.form['button'] == 'Submit':
            if len(request.form['destination']) < 4:
                flash("A trip destination must consist of at least 3 characters")
            if len(request.form['plan']) < 4:
                flash("A plan must be provided!")
                return redirect('/trips/edit/<id>')
            if request.form['button'] == 'Submit':
                mysql = connectToMySQL("exam")
                edit_query = "UPDATE exam.trips SET destination = %(des)s, plan = %(p)s, start_date = %(sd)s, end_date = %(ed)s WHERE id = %(tid)s;"
                edit_data = {
                    "des": request.form['destination'],
                    "p": request.form['plan'],
                    "sd": request.form['start'],
                    "ed": request.form['end'],
                    "tid": session['trip_id']
                }
                trip_edited = mysql.query_db(edit_query, edit_data)
            return redirect('/dashboard')
        return redirect('/dashboard')
    flash("Please login to continue")
    return redirect('/')

@app.route('/register', methods=['post'])
def register():
    if len(request.form['r_fname']) < 2:
        flash("Please enter a valid first name")
    if len(request.form['r_lname']) < 3:
        flash("Please enter a valid last name")
    if not EMAIL_REGEX.match(request.form['r_email']):
        flash("Invalid email address")
    if len(request.form['r_password']) < 8:
        flash("Password too short")
    if request.form['r_password'] != request.form['r_confirm']:
        flash("Passwords do not match")
        return redirect('/')
    elif EMAIL_REGEX.match(request.form['r_email']):
        pw_hash = bcrypt.generate_password_hash(request.form['r_password'])
        mysql = connectToMySQL("exam")
        reg_query = "INSERT INTO exam.users (first_name, last_name, email, password) VALUES (%(rfn)s, %(rln)s, %(rem)s, %(rpw)s);"
        reg_data = {
            "rfn": request.form['r_fname'],
            "rln": request.form['r_lname'],
            "rem": request.form['r_email'],
            "rpw": pw_hash
        }
        session['reg_email'] = request.form['r_email']
        session['name'] = request.form['r_fname']
        reg_users = mysql.query_db(reg_query, reg_data)
        session['userid'] = reg_users
        return redirect('/success')
    return redirect('/')

@app.route('/login', methods=['post'])
def login():
    mysql = connectToMySQL("exam")
    log_query = "SELECT * FROM exam.users WHERE email = %(rem)s;"
    log_data = { 
        "rem": request.form['l_email'] 
        }
    log_users = mysql.query_db(log_query, log_data)
    if len(log_users) > 0:
        if bcrypt.check_password_hash(log_users[0]['password'], request.form['l_password']):
            session['userid'] = log_users[0]['id']
            session['name'] = log_users[0]['first_name']
            return redirect('/dashboard')

    flash("Please check email and/or password")
    return redirect('/')

@app.route('/trips/new')
def new_trip():
    if 'userid' in session:
        return render_template('newtrip.html')
    flash("Please login to continue")
    return redirect("/")

@app.route('/create_trip', methods=['post'])
def create_trip():
    if request.form['button'] == 'Submit':
        if len(request.form['destination']) < 4:
            flash("A trip destination must consist of at least 3 characters")
        if len(request.form['start']) < 1:
            flash("Invalid start date")
        if len(request.form['end']) < 1:
            flash("Invalid end date")
        if len(request.form['plan']) < 4:
            flash("A plan must be provided!")
            return redirect('/trips/new')
        # ADD NEW TRIP
        mysql = connectToMySQL("exam")
        create_query = "INSERT INTO exam.trips (destination, plan, start_date, end_date, user_id) VALUES (%(des)s, %(p)s, %(sd)s, %(ed)s, %(uid)s);"
        create_data = {
            "des": request.form['destination'],
            "p": request.form['plan'],
            "sd": request.form['start'],
            "ed": request.form['end'],
            "uid": session['userid']
        }
        trip_created = mysql.query_db(create_query, create_data)
        return redirect('/dashboard')
    return redirect('/dashboard')

@app.route('/cancel', methods=['post'])
def cancel():
    return redirect('/dashboard')

@app.route('/trips/<id>')
def view_trip(id):
    if 'userid' in session:
        mysql = connectToMySQL("exam")
        trip_query = "SELECT * FROM exam.trips JOIN exam.users ON exam.users.id = exam.trips.user_id WHERE exam.trips.id = %(tid)s;"
        trip_data = {
            "tid": id
        }
        trips = mysql.query_db(trip_query, trip_data)
        session['trip_name'] = trips[0]['destination']
        return render_template('view_trip.html', trips = trips)
    flash("Please login to continue")
    return redirect("/")

@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')

if __name__=="__main__":       
    app.run(debug=True)  