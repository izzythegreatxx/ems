from flask import Flask, jsonify, request, session, render_template, redirect, url_for
from functools import wraps
from datetime import datetime
import json
import bcrypt
import logging
import random


# Initialize Flask app
app = Flask(__name__)
app.secret_key = "asdkj51325khgbjjkmk"

# Logging 
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("employee_management.log"),
        logging.StreamHandler()
    ]
)


# Define Employee class
class Employee:
    def __init__(self, employeeId, firstName, lastName, email, salary, startDate, title):
        self.employeeId = employeeId
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.salary = salary
        self.startDate = startDate
        self.title = title

    def emp_to_dict(self):
        return {
            "employeeId": self.employeeId,
            "firstName": self.firstName,
            "lastName": self.lastName,
            "email": self.email,
            "salary": self.salary,
            "startDate": self.startDate,
            "title": self.title,
        }

    @staticmethod
    def from_dict(data):
        return Employee(
            data.get("employeeId", ""),
            data.get("firstName", ""),
            data.get("lastName", ""),
            data.get("email", ""),
            data.get("salary", 0),
            data.get("startDate", "N/A"), 
            data.get("title", "")
        )

# Define Employees class
class Employees:
    def __init__(self):
        self.employeeList = []

    def add_employee(self, employee):
        self.employeeList.append(employee)
        logging.info(f"Added employee: {employee.employeeId} - {employee.firstName} {employee.lastName}")

    def remove_employee(self, employeeId):
        self.employeeList = [emp for emp in self.employeeList if emp.employeeId != employeeId]

    def update_employee_info(self, employeeId, **kwargs):
        for emp in self.employeeList:
            if emp.employeeId == employeeId:
                for key, value in kwargs.items():
                    if value is not None:  # Update only non-None values
                        setattr(emp, key, value)
                logging.info(f"Updated employee: {employeeId}")
                return True
        logging.warning(f"Employee ID {employeeId} not found")
        return False

    def save_to_file(self, filename="employees.json"):
        with open(filename, "w") as file:
            json.dump([emp.emp_to_dict() for emp in self.employeeList], file)

    def load_from_file(self, filename="employees.json"):
        try:
            with open(filename, "r") as file:
                self.employeeList = [Employee.from_dict(emp) for emp in json.load(file)]
        except FileNotFoundError:
            print("No employee file found. Starting with an empty list.")
        except json.JSONDecodeError:
            print("Corrupted employee file. Starting fresh.")

# Authentication class
class Authentication:
    def __init__(self, users_file="users.json"):
        self.users_file = users_file
        self.users = {}
        self.load_users()

    def load_users(self):
        try:
            with open(self.users_file, "r") as file:
                self.users = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.users = {}

    def save_users(self):
        with open(self.users_file, "w") as file:
            json.dump(self.users, file)

    def register_user(self, username, password):
        username = username.lower().strip()
        if username in self.users:
            return False
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.users[username] = hashed_password.decode()
        self.save_users()
        return True

    def authenticate(self, username, password):
        username = username.lower().strip()
        if username in self.users:
            hashed_password = self.users[username].encode()
            return bcrypt.checkpw(password.encode(), hashed_password)
        return False

# Decorator for login-required routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Initialize global objects
employees = Employees()
employees.load_from_file()
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
            return redirect(url_for('dashboard'))  # Ensure this points to the correct dashboard route
        else:
            return render_template("login.html", error="Invalid username or password.")
    
    return render_template("login.html")  # Render login page for GET request

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
    return render_template("employees.html", employees=employees.employeeList)


@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        # Check if the request is JSON (API call)
        if request.is_json:
            data = request.get_json()
        else:
            # Otherwise, handle form data (HTML form submission)
            data = request.form

        try:
            # Convert salary to float for both JSON and form data
            salary = float(data.get("salary", 0))
            new_employee = Employee(
                employeeId=str(random.randint(1000, 9999)),  # Generate a random ID
                firstName=data.get("firstName"),
                lastName=data.get("lastName"),
                email=data.get("email"),
                salary=salary,
                startDate=data.get("startDate"),
                title=data.get("title"),
            )
            employees.add_employee(new_employee)
            employees.save_to_file()

            # Return JSON response for API calls
            if request.is_json:
                return jsonify({"message": "Employee added successfully"}), 201

            # Redirect to employees list for form submissions
            return redirect(url_for('get_employees'))
        except Exception as e:
            # Handle errors
            if request.is_json:
                return jsonify({"error": f"Failed to add employee: {str(e)}"}), 400
            return render_template("add_employee.html", error=f"Failed to add employee: {str(e)}")

    # Render the "Add Employee" form for GET requests
    return render_template("add_employee.html")


@app.route('/employees/edit/<string:employee_id>', methods=['GET', 'POST', 'PUT'])
@login_required
def edit_employee(employee_id):
    # Find the employee in the list
    emp = next((e for e in employees.employeeList if e.employeeId == employee_id), None)
    if not emp:
        return "Employee not found", 404

    if request.method == 'GET':
        # Render the edit employee form with the current employee data
        return render_template("edit_employee.html", employee=emp)

    if request.method in ['POST', 'PUT']:
        # Handle form data from HTML for 'POST' and JSON data for 'PUT'
        if request.method == 'POST':
            data = request.form  # Use form data from HTML
        else:
            data = request.get_json()  # Use JSON data from PUT request

        try:
            # Convert salary to float with proper error handling for both 'POST' and 'PUT'
            salary = float(data.get("salary", 0))
        except ValueError:
            return render_template("edit_employee.html", employee=emp, error="Invalid salary input.")

        # Proceed with the update logic
        success = employees.update_employee_info(
            employeeId=employee_id,
            firstName=data.get("firstName"),
            lastName=data.get("lastName"),
            email=data.get("email"),
            salary=salary,
            startDate=data.get("startDate"),
            title=data.get("title")
        )

        if success:
            employees.save_to_file()
            if request.method == 'PUT':
                logging.info(f"User {employee_id} updated.")
                return jsonify({"message": "Employee updated successfully"}), 200
            else:
                return redirect(url_for('get_employees'))
        else:
            if request.method == 'PUT':
                return jsonify({"error": "An error occurred when updating."}), 500
            else:
                return render_template("edit_employee.html", employee=emp, error="An error occurred when updating.")



@app.route('/employees/remove/<string:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    # Check for the `_method` override
    if request.form.get('_method') == 'DELETE':
        employees.remove_employee(employee_id)
        employees.save_to_file()
        return redirect(url_for('get_employees'))
    return jsonify({"error": "Invalid request method"}), 400


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
