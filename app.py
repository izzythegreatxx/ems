from flask import Flask, jsonify, request, session, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Employee, User
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler 


"""
This Flask application serves as the backend for the Employee Management System.

Features:
- Configures and initializes an SQLite database using SQLAlchemy.
- Implements logging with file rotation for better log management.
- Provides user authentication and registration through the `Authentication` class.
- Manages user sessions and access control.
- Handles routing for employee CRUD (Create, Read, Update, Delete) operations.
- Supports both HTML form-based interactions and JSON API requests.

This system enables efficient employee data management, including salary tracking,
start dates, and job titles, making HR processes more streamlined.
"""

load_dotenv()

# Initialize Flask app
app = Flask(__name__)


# Set environment variables
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")
# Configure Database URI
# using sqlite for local development
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///employees.db')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)


with app.app_context():
    db.create_all()

# Logging 
# configure log file rotation
log_handler = RotatingFileHandler("employee_management.log", maxBytes=5 * 1024 *1024, backupCount=5) # 5MB per file. keep 5 backups
log_handler.setLevel(logging.DEBUG)

# log format
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(log_formatter)

# Apply configurations
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        log_handler, # uses rotating logs
        logging.StreamHandler() # logs to console
    ]
)

# Authentication class manages user registration and login functionality 
class Authentication:
    # function to register new users. Uses bcrypt for password hashing
    def register_user(self, username, password):
        username = username.lower().strip()
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return False
        # hash password and save user
        hashed_password = User.hash_password(password)
        new_user = User(username=username, password_hash = hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return True
    
    # authenticates user by using bcrypt for validating passwords
    def authenticate(self, username, password):
        username = username.lower().strip()
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            return True
        return False

# Decorator for login-required routes
def login_required(f):
    #helps maintain the original data of the function that is decorated
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Initialize global objects
auth = Authentication()

# Routes
@app.route('/')
def home():
    return render_template("base.html")

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # Handle form submission
        data = request.form
        username = data.get("username")
        password = data.get("password")
        
        # Validate input
        if not username or not password:
            return render_template("register.html", error="Username and password are required.")
        
        # Password validation
        if len(password) < 10:
            return render_template("register.html", error="Password must be at least 10 characters long.")
        if not any(char.isdigit() for char in password):
            return render_template("register.html", error="Password must contain at least one number.")
        if not any(char.isalpha() for char in password):
            return render_template("register.html", error="Password must contain at least one letter.")
        
        # Register user
        if auth.register_user(username, password):
            logging.info(f"User {username} has registered.")
            return render_template("login.html", success="Registration successful. Please log in.")
        else:
            return render_template("register.html", error="Username already exists.")
    
    # Render registration page for GET request
    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        data = request.form
        username = data.get("username")
        password = data.get("password")
        
        if auth.authenticate(username, password):
            session['username'] = username
            logging.info(f"User {username} has logged in.")
            return redirect(url_for('dashboard'))  
        else:
            return render_template("login.html", error="Invalid username or password.")
    
    return render_template("login.html")  

@app.route('/dashboard')
@login_required
def dashboard():
    current_date = datetime.now().strftime("%B %d, %Y") 
    return render_template("dashboard.html", username=session['username'], current_date = current_date)


@app.route('/logout', methods=['POST', 'GET'])
def logout_user():
    session.pop('username', None)
    
    return redirect(url_for('login_user'))  # Redirect to the login page


@app.route('/employees', methods=['GET'])
@login_required
def get_employees():
    employees = Employee.query.all()
    return render_template("employees.html", employees=employees)

#--------EMPLOYEE CRUD OPERATIONS--------------->


# Add employee
@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        data = request.form
        print("Received Form Data:", data)  # Debugging

        start_date_str = data.get("start_date")
        if not start_date_str:
            print("Error: Start date is missing!")
            return jsonify({"error": "Start date is required"}), 400

        try:
            new_employee = Employee(
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                email=data.get("email"),
                salary=float(data.get("salary")),
                start_date=datetime.strptime(data.get("start_date"), "%Y-%m-%d"),
                title=data.get("title")
            )
            
            db.session.add(new_employee)
            db.session.commit()
            print("Employee added successfully:", new_employee)
            
            return redirect(url_for('get_employees'))
        
        except Exception as e:
            db.session.rollback()
            print("Error adding employee:", str(e))  # Debugging
            return jsonify({"error": str(e)}), 400

    return render_template("add_employee.html")


# Edit employee
@app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST', 'PUT'])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)  # Get employee or return 404

    if request.method in ['POST', 'PUT']:
        data = request.form if request.method == 'POST' else request.get_json()
        
        try:
            # Update employee fields
            employee.first_name = data.get("first_name", employee.first_name)
            employee.last_name = data.get("last_name", employee.last_name)
            employee.email = data.get("email", employee.email)
            employee.salary = float(data.get("salary", employee.salary))
           
            
            if data.get("start_date"):
                 employee.start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d")  
                
            employee.title = data.get("title", employee.title)

            db.session.commit()  # Save changes to the database
            logging.info(f"Employee {employee_id} updated successfully.")

            if request.method == 'PUT':  # JSON response for API requests
                return jsonify({"message": "Employee updated successfully"}), 200
            else:
                return redirect(url_for('get_employees'))  # Redirect on form submission

        except Exception as e:
            db.session.rollback()  # Rollback changes if error occurs
            logging.error(f"Error updating employee {employee_id}: {str(e)}")
            return jsonify({"error": "Employee update failed", "details": str(e)}), 400

    return render_template("edit_employee.html", employee=employee)


# Delete employee
@app.route('/employees/remove/<int:employee_id>', methods=['DELETE'])
@login_required
def delete_employee(employee_id):
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({"Error": "Employee not found."}), 400
    try:
        db.session.delete(employee)
        db.session.commit()
        logging.info(f"Employee {employee_id} has been removed.")
        return jsonify({"message": "Employee deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error":f"Failed to delete employee: {str(e)}"}), 500
   



# Run the app
if __name__ == "__main__":
    app.run(debug=True)
