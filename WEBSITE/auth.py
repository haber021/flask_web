from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Test  # Make sure to import your models
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import numpy as np
bcrypt = Bcrypt()

auth = Blueprint('auth', __name__)


@auth.route('/hom')
def hom():
    return render_template('hom.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            flash('Logged in successfully', category='success')
            login_user(user, remember=True)
            return redirect(url_for('views.hom'))
        else:
            flash('Incorrect email or password, please try again.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Please log in.', category='error')
            return redirect(url_for('auth.login'))

        if len(email) < 4 or len(firstName) < 2 or len(lastName) < 1 or password1 != password2 or len(password1) < 7:
            flash('Invalid registration details. Please check and try again.', category='error')
        else:
            # Use Flask-Bcrypt's interface for generating a salt and hashing
            hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')

            new_user = User(email=email, firstName=firstName, lastName=lastName, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created successfully.', category='success')
            return redirect(url_for('views.hom'))

    return render_template("signup.html", user=current_user)



@auth.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    test_data = Test.query.limit(10).all()

    if request.method == 'POST':
        # Process the form data and save it to the database (adjust as needed)
        name = request.form.get('name', '')
        position = request.form.get('position', '')
        office = request.form.get('office', '')
        age = request.form.get('age', '')

        start_date_str = request.form.get('start_date', '')
        salary = request.form.get('salary', '')
        if not start_date_str or not salary:
            flash('Starting Date and Salary are required fields.', 'error')
            return render_template("upload.html", user=current_user, test_data=test_data)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid Starting Date format. Please use YYYY-MM-DD.', 'error')
            return render_template("upload.html", user=current_user, test_data=test_data)

        existing_data = Test.query.filter_by(name=name, position=position, age=age).first()
        if existing_data:
            return render_template("update_prompt.html", existing_data=existing_data)

        # Assuming you have features X and labels y from your existing data
        X = np.array([[existing_data.age, existing_data.salary] for existing_data in test_data])

        # Convert label to float with handling for invalid labels
        y = []
        invalid_label_indices = []

        for index, existing_data in enumerate(test_data):
            try:
                label_value = float(existing_data.label)
                y.append(1 if label_value > 10000 else 0)
            except ValueError:
                # Handle invalid labels by logging a warning and excluding the data point
                flash(f'Invalid label format for {existing_data.name}. Excluding from training.', 'warning')
                invalid_label_indices.append(index)

        # Remove data points with invalid labels
        X = np.delete(X, invalid_label_indices, axis=0)
        y = np.array(y)

        # Check if there's enough data for training
        if len(X) < 5 or len(y) < 5:
            flash('Not enough samples for training. Add more data.', 'error')
            return render_template("upload.html", user=current_user, test_data=test_data)

        # Reshape X to make it a 2D array
        X = X.reshape(-1, 2)

        # If there's not enough existing test data, generate synthetic data
        if len(X) < 5:  # Adjust the threshold as needed
            # Generate synthetic data or use default values
            synthetic_data = [
                [30, 50000],  # Example synthetic data
                [25, 60000],
                [35, 55000],
                [28, 52000],
                [32, 48000],
            ]
            synthetic_labels = [1] * len(synthetic_data)  # Generate synthetic labels

            X = np.concatenate([X, np.array(synthetic_data)])
            y = np.concatenate([y, np.array(synthetic_labels)])  # Add synthetic labels

        # Check if there are enough samples for splitting
        if len(X) <= 1 or len(y) <= 1:
            flash('Not enough samples for training. Add more data.', 'error')
            return render_template("upload.html", user=current_user, test_data=test_data)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        knn = KNeighborsClassifier(n_neighbors=3)
        knn.fit(X_train, y_train)

        # Assuming you have new data in the form of a request
        # Replace this with your actual new data from the form
        try:
            new_age = float(request.form.get('age'))
            new_salary = float(request.form.get('salary'))
        except ValueError:
            flash('Invalid input for age or salary.', 'error')
            return render_template("upload.html", user=current_user, test_data=test_data)

        new_data = np.array([[new_age, new_salary]])
        new_features = scaler.transform(new_data)

        predicted_labels = knn.predict(new_features)

        # Assuming you have a Test model and a database session db.session
        new_test_data = Test(
            name=name,
            position=position,
            office=office,
            age=age,
            start_date=start_date,
            salary=salary,
            label=str(predicted_labels[0])  # Convert label back to string
        )
        db.session.add(new_test_data)
        db.session.commit()

        flash('Data has been uploaded successfully!', 'success')
        return redirect(url_for('views.hom'))

    return render_template("upload.html", user=current_user, test_data=test_data)



@auth.route('/update_finish/<int:id>', methods=['GET'])
def update_prompt(id):
    existing_data = Test.query.get(id)
    return render_template("update_prompt.html", existing_data=existing_data)



@auth.route('/update_finish/<int:id>/finish', methods=['POST'])
def update_finish(id):
    existing_data = Test.query.get(id)

    if existing_data:
        # Process the update logic here
        # Check if the required fields are present in the form data
        name = request.form.get('name', '')  # Use get method with a default value
        if not name:
            flash('Name is required for updating data.', 'error')
            return redirect(url_for('auth.upload'))

        # Update the existing_data fields with the new data
        existing_data.name = name
        existing_data.position = request.form.get('position', '')
        existing_data.office = request.form.get('office', '')
        existing_data.age = request.form.get('age', '')
        
        # Convert the start_date string to a datetime object
        start_date_str = request.form.get('start_date', '')
        try:
            existing_data.start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        except ValueError:
            flash('Invalid Starting Date format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('auth.upload'))

        existing_data.salary = request.form.get('salary', '')

        db.session.commit()
        flash('Data has been updated successfully!', 'success')
        return redirect(url_for('views.hom'))

    # Redirect to the home page and pass the updated data
    test_data = Test.query.all()
    return render_template('hom.html', test_data=test_data)


@auth.route('/dashboard')
def dashboard():
    initial_location = {'lat': 17.365472, 'lon': 120.471776}
    google_static_map_url = f'https://maps.googleapis.com/maps/api/staticmap?center={initial_location["lat"]},{initial_location["lon"]}&zoom=15&size=500x500&key=YOUR_API_KEY'

    return render_template('dashboard.html', initial_location=initial_location, google_static_map_url=google_static_map_url)


from .models import Test  # Import the Test model

@auth.route('/tab', methods=['GET'])
def tab():
    test_data = Test.query.all()  # Fetch all data from the Test model
    return render_template("tab.html", test_data=test_data)

@auth.route('/home', methods=['GET'])
def home():
    return render_template("home.html")

@auth.route('/chart')
def chart():
    return render_template("chart.html")

@auth.route('/food_info')
def food_info():
    return render_template("food_info.html")

@auth.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search_query')

    # Perform a search in your Test database based on the search_query
    # Adjust this query based on your Test model
    results = Test.query.filter(Test.name.ilike(f'%{search_query}%')).all()

    return render_template('food_info.html', results=results)

