from flask import Flask, jsonify, request, session, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Employee, User
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
import os
import jwt
import logging
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from logging.handlers import RotatingFileHandler 
import random


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

# ✅ Flask-Mail Configuration (Ensure .env variables are loaded)
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))  # Convert to int
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True") == "True"  # Convert to boolean
app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")  # Load email
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASS")  # Load password
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("EMAIL_USER")  # Set sender email

mail = Mail(app)

serializer=URLSafeTimedSerializer(app.secret_key)


# Configure Database URI
# using sqlite for local development
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/employees.db')

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

def token_required(f):
    """JWT Token Authentication Decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_employee = Employee.query.get(data['id'])
            if not current_employee:
                return jsonify({'message': 'Employee not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        
        return f(current_employee, *args, **kwargs)
    return decorated

# Initialize global objects
auth = Authentication()

# email test
@app.route('/test_email')
def test_email():
    with app.app_context():
        msg = Message("Test Email", recipients=["your_email@gmail.com"])
        msg.body = "This is a test email from Flask-Mail."
        mail.send(msg)
    return "Test email sent! Check your inbox."
# Routes
# home page
@app.route('/')
def home():
    if "username" in session:
        current_date = datetime.today().strftime('%A, %B %d, %Y')
        return render_template("dashboard.html", username=session["username"], current_date = current_date)
    return render_template("base.html")

#about us page
@app.route('/about')
def about_us():
    
    return render_template("about.html")

# contact us page
@app.route('/contact', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            flash("All fields are required!", "error")
            return redirect(url_for('contact_us'))

        # Log the message (optional)
        logging.info(f"📩 New Contact Message: {name} ({email}) - {message}")

        # You can also store this in a database or send an email here

        flash("Message sent successfully! We will get back to you soon.", "success")
        return redirect(url_for('contact_us'))  # Redirect after success

    return render_template("contact.html")


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        data = request.form
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")  # Get role from form

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

        # Check if username already exists in both users & employees tables
        existing_user = User.query.filter_by(username=username).first()
        existing_employee = Employee.query.filter_by(username=username).first()
        
        if existing_user or existing_employee:
            return render_template("register.html", error="Username already exists.")

        if role == "Admin":
            # Prevent non-admins from registering as an admin
            if not session.get("is_admin"):
                return render_template("register.html", error="Only an existing admin can create an admin account.")

            new_user = User(username=username, is_admin=True)
            new_user.set_password(password)
            db.session.add(new_user)

        elif role == "Employee":
            new_employee = Employee(
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                email=data.get("email"),
                salary=float(data.get("salary")),
                start_date=datetime.strptime(data.get("start_date"), "%Y-%m-%d"),
                title=data.get("title"),
                username=username
            )
            new_employee.set_password(password)  # Hash the password
            db.session.add(new_employee)

        else:
            return render_template("register.html", error="Invalid role selected.")

        db.session.commit()
        flash(f"Registration successful as {role}. Please log in.", "success")

        if role == "Admin":
            return redirect(url_for("login_user"))  # Redirect to admin login
        else:
            return redirect(url_for("employee_login"))  # Redirect to employee login

    return render_template("register.html")





# login page
@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if "username" in session:
        return redirect(url_for("dashboard"))

    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['username'] = user.username
            session['is_admin'] = user.is_admin 
            logging.info(f"User {username} logged in.")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")

# employee login
@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    if request.method == 'GET':
        return render_template("employee_login.html")

    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')

        print(f"🔍 Debug: Attempting login for {username}")  # Debugging

        # Find the employee
        employee = Employee.query.filter(Employee.username.ilike(username)).first()

        if not employee:
            print("⚠ Debug: Employee not found!")
            flash('User not found!', 'error')
            return render_template("employee_login.html")

        # Check the password
        if not employee.check_password(password):
            print("⚠ Debug: Incorrect password!")
            flash('Invalid password!', 'error')
            return render_template("employee_login.html")

        # ✅ Store Employee in Session
        session['employee_id'] = employee.id
        session['employee_username'] = employee.username
        session.permanent = True  # Make the session last longer

        print(f"✅ Debug: {username} successfully logged in!")
        return redirect(url_for('employee_dashboard'))  # Redirect to dashboard





# employee dashboard
@app.route('/employee/dashboard')
def employee_dashboard():
    if "employee_id" not in session:
        flash("You need to log in first!", "error")
        return redirect(url_for("employee_login"))

    employee = Employee.query.get(session["employee_id"])
    
    if not employee:
        flash("Employee not found!", "error")
        session.pop("employee_id", None)  # Remove invalid session
        return redirect(url_for("employee_login"))

    return render_template("employee_dashboard.html", employee=employee)



# dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    if "username" not in session:
        flash("You need to log in first.", "error")
        return redirect(url_for("login_user"))  # ✅ Redirect to login

    username = session["username"]
    current_date = datetime.now().strftime("%B %d, %Y")
    return render_template("dashboard.html", username=username, current_date=current_date)



# logout
@app.route('/logout', methods=['GET', 'POST'])
def logout_user():
    """Logs out the user and redirects to the homepage"""
    session.clear()  # ✅ Clears all session data
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))  # ✅ Redirect to home


# employees
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
    if not session.get("is_admin"):
        return jsonify({"error": "Unauthorized. Only admins can add employees."}), 403

    if request.method == 'POST':
        data = request.form
        print(f"🔍 Debug: Received Form Data -> {data}")  # Debugging

        try:
            first_name = data.get("first_name").strip()
            last_name = data.get("last_name").strip()
            email = data.get("email").strip()

            # ✅ Ensure the email is unique
            existing_employee = Employee.query.filter_by(email=email).first()
            if existing_employee:
                return jsonify({"error": "An employee with this email already exists."}), 400

            new_employee = Employee(
                first_name=first_name,
                last_name=last_name,
                email=email,
                salary=float(data.get("salary")),
                start_date=datetime.strptime(data.get("start_date"), "%Y-%m-%d"),
                title=data.get("title"),
                username=None,  # ✅ Keep NULL (employees set this when they register)
                password_hash=None  # ✅ Keep NULL (employees set this when they register)
            )

            db.session.add(new_employee)
            db.session.commit()
            flash("Employee added successfully!", "info")
            print(f"✅ Debug: Employee added successfully!")

            return redirect(url_for('get_employees'))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Debug: Error adding employee -> {str(e)}")  # Debugging
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
    
# data visualization
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route('/api/financial_data')
def financial_data():
    """Fetch financial data for visualization"""
    employees = Employee.query.all()
    
    total_salary = sum(emp.salary for emp in employees)
    num_employees = len(employees)
    monthly_revenue = round(random.uniform(300000, 500000), 2)  # Fake revenue for now
    profit = round(monthly_revenue - total_salary, 2)

    data = {
        "total_salary": total_salary,
        "num_employees": num_employees,
        "monthly_revenue": monthly_revenue,
        "profit": profit
    }

    return jsonify(data)

   



# Run the app
if __name__ == "__main__":
    app.run(debug=True)
