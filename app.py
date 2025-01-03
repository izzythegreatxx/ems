import json
import bcrypt
import logging
import time
import random
import string


#session times out after 10 minutes of being logged in
SESSION_TIMEOUT = 10 * 60 
#max login attempts in 10 minute window
MAX_ATTEMPTS = 5
#max attempts before CAPTCHA is triggered
MAX_ATTEMPTS_BEFORE_CAPTCHA = 3
#duration blocked user will have to wait (5 minutes)
BLOCK_DURATION = 300
#10 minute time window 
TIME_WINDOOW = 10 * 60

#dictionary to hold login attempts for each user
login_attempts = {}

def generate_captcha():
    """Generate a random 6-character CAPTCHA."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

def verify_captcha(user_input, captcha):
    """Verify if the CAPTCHA entered is correct."""
    return user_input.strip() == captcha

                
logging.basicConfig(
    filename = "employee_management.log",
    level=logging.DEBUG, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# class to handle individual employees
class Employee:
    def __init__(self, employeeId, firstName, lastName, email, salary, startDate, title):
        self.employeeId = employeeId
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.salary = salary
        self.startDate = startDate
        self.title = title
    # dictionary to store Employee objects for JSON serialization
    def emp_to_dict(self):
        return{
            "employeeId": self.employeeId,
            "firstName": self.firstName, 
            "lastName": self.lastName,
            "email": self.email,
            "salary": self.salary,
            "start date": self.startDate,
            "title": self.title
        }
    @staticmethod
    def from_dict(data):
        return Employee(
            data["employeeId"], 
            data["firstName"],
            data["lastName"],
            data["email"],
            data["salary"],
            data["start date"],
            data["title"]
        )
# class to handle list of employees        
class Employees:
    def __init__(self) -> None:
        self.employeeList = []
    #appends employees to the list
    def add_employee(self, employee):
        self.employeeList.append(employee)
        logging.info(f"Added employee: {employee.employeeId} - {employee.firstName} {employee.lastName}")
        
    #shows all employees except for the one that matches the employee id
    def remove_employee(self, employeeId):
        before_count = len(self.employeeList)
        self.employeeList = [emp for emp in self.employeeList if emp.employeeId != employeeId]
        after_count = len(self.employeeList)
        if before_count > after_count:
            logging.info(f"Removed employee: {employeeId}")
        else:
            logging.warning(f"Attempted to remove non-exixtent employee ID: {employeeId}")
            
    #updates employee. If nothing updated it skips the option
    def update_employee_info(self, employeeId, firstName = None, lastName = None, email=None, salary= None, startDate=None, title= None):
        updated = False
        for emp in self.employeeList:
            if emp.employeeId == employeeId:
                if firstName is not None and emp.firstName != firstName:
                    emp.firstName = firstName
                    updated = True
                if lastName is not None and emp.lastName != lastName:
                    emp.lastName = lastName
                    updated = True
                if email is not None and emp.email != email:
                    emp.email = email
                    updated = True
                if salary is not None and emp.salary != salary:
                    emp.salary = salary
                    updated = True
                if startDate is not None and emp.startDate != startDate:
                    emp.startDate = startDate
                    updated = True
                if title is not None and emp.title != title:
                    emp.title = title
                    updated = True
                if updated:
                    logging.info(f"Updated employee: {employeeId}")
                else: 
                    print(f"No updates made to employee: {employeeId}")
                return 
        logging.warning(f"Attempted to update non-existent employee ID: {employeeId}")
        
    # save employee data to a JSON file
    def save_to_file(self, filename="employees.json"):
        with open(filename, "w") as file:
            json.dump([emp. emp_to_dict() for emp in self.employeeList], file)
            
    # load employee list from JSON file
    def load_from_file(self, filename="employees.json"):
        try:
            with open(filename, "r") as file:
                self.employeeList = [Employee.from_dict(emp) for emp in json.load(file)]
        except FileNotFoundError:
            print(f"File {filename} not found. Starting with an empty employee list.")
        except json.JSONDecodeError:
            print(f"File {filename} is not in valid JSON format. Starting wiht an empty list. ")


#Utility functions
def showAllEmployees(employeeList):
    for emp in employeeList:
        print(f"ID: {emp.employeeId}, First Name: {emp.firstName}, Last Name: {emp.lastName}, Email: {emp.email}, Salary: {emp.salary}, Start Date: {emp.startDate}, Title: {emp.title}")
        

def addNewEmployee(employeeList, employeeId, firstName, lastName, email, salary, startDate, title):
    new_employee = Employee(employeeId, firstName, lastName, email, salary, startDate, title)
    employeeList.add_employee(new_employee)
    
def removeEmployee(employeeList, employeeId):
    employeeList.remove_employee(employeeId)
    
def updateEmployeeInfo(employeeList, employeeId, firstName=None, lastName=None, email=None, salary=None, startDate=None, title=None):
    employeeList.update_employee_info(employeeId, firstName, lastName, email, salary, title)
    
#register and authenticate password
class Authentication:
    def __init__(self, users_file="users.json"):
        self.users_file = users_file
        self.users = {}
        self.load_users()
        
    def load_users(self):
    #load users and hashed passwords from JSON
        try: 
            with open(self.users_file, "r") as file:
                self.users = json.load(file)
        except FileNotFoundError:
            print(f"{self.users_file} not found. Starting with an empty user database.")
            self.users = {}
        except json.JSONDecodeError:
            print(f"{self.users_file} is not in valid JSON format. Starting fresh.")
            self.users = {}
            
    def save_users(self):
        #save users and hashed passwords to a JSON file.
        with open(self.users_file, "w") as file:
            json.dump(self.users, file)
            
    def register_user(self, username, password):
        #register a new user and hashed password
        username = username.lower().strip()
        if username in self.users:
            print("Username already exists. Choose a different username.")
            return False
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.users[username]=hashed_password.decode()
        self.save_users()
        print("User registered successfully.")
        logging.info(f"Added '{username}' to users.")
        return True
        
    def authenticate(self, username, password):
        #verify user by comparing provided password with hashed password
        if username not in self.users:
            print("Invalid username.")
            return False
        stored_hashed_password = self.users[username].encode()
        if bcrypt.checkpw(password.encode(), stored_hashed_password):
            print("Authentication successful!")
            logging.info(f"User '{username}' logged in.")
            return True
        else: 
            print("Invalid password.")
            logging.warning(f"User '{username}' attempted to log in.")
            return False
    #removes user from users    
    def remove_user(self, username):
        if username in self.users:
            del self.users[username]
            self.save_users()
            logging.info(f"Removed '{username}' from users.")
            return True
        else:
            print(f"User '{username}' does not exist.")
            logging.warning("Attempted removal of user.")
            return False
#login or register
if __name__ == "__main__":
    auth = Authentication()
    
    while True:
        print("-"*10 + "Register or Login" + "-"*10)
        print("1) Register user")
        print("2) Login")
        print("3) Exit")
        
        choice = int(input("Please select an option (1-3): "))
        
        if choice == 1:
            username = input("Enter a new username: ").lower().strip()
        
            
            while True:
                password = input("Enter a new password: ")
                if len(password) < 10:
                    print("Password must be longer than 10 characters.")
                elif not any(char.isdigit() for char in password):
                    print("Password must contain both letters and numbers.")
                elif not any(char.isalpha() for char in password): 
                    print("Password must contain both letters and numbers.")
                else:
                    break
            auth.register_user(username, password)
            auth.save_users()
            
        elif choice == 2:
            while True:
                username = input("Enter your username: ").strip().lower()
                current_time = time.time()
                # Initialize login attempts for user if they're not in dictionary
                if username not in login_attempts: 
                    login_attempts[username] = {"attempts": [], "blocked until": 0}
                # check if current user is blocked
                if login_attempts[username]["blocked until"]> current_time:
                    print("Too many failed attemts. Please try again later.")
                    continue
                
                # Remove expired attempts from log
                login_attempts[username]["attempts"] =[attempt for attempt in login_attempts[username]["attempts"] if current_time - attempt < TIME_WINDOOW]
                
                #check if CAPTCHA is required
                if len(login_attempts[username]["attempts"]) >= MAX_ATTEMPTS_BEFORE_CAPTCHA:
                    captcha = generate_captcha()
                    print(f"CAPTCHA Challenge: {captcha}")
                    captcha_input = input("Enter CAPTCHA: ").strip()
                    if not verify_captcha(captcha_input, captcha):
                        print("Incorrect CAPTCHA. Please try again.")
                        logging.warning(f"User '{username}' failed CAPTCHA validation.")
                        login_attempts[username]["attempts"].append(current_time)
                        continue
                # if login attempts exceed the max limit, block the user
                if len(login_attempts[username]["attempts"])>+MAX_ATTEMPTS:
                    login_attempts[username]["blocked_until"] = current_time + BLOCK_DURATION
                    print("Too many failed attempts. You are temporarily blocked. Please try again in 5 minutes.")
                    logging.warning(f"User '{username}' blocked due to excessive login atempts.")
                    continue
                #Validate username                        
                if username not in auth.users:
                    print("Invalid username. Please try again.")
                    logging.warning(f"Invalid username attempt:  {username}")
                    login_attempts[username]["attempts"].append(current_time)
                    continue
                break
            #prompt for passwod
            password = input("Enter your password: ")
            if auth.authenticate(username, password):
                print("Welcome!")
                logging.info(f"User '{username}' logged in successfully.")
                #clear attempts on successful login
                login_attempts.pop(username, None)
                
                employees = Employees()
                #load data at start of program
                employees.load_from_file()
                
                login_time = time.time()
                while True:
                    elapsed_time= time.time() - login_time
                    if elapsed_time > SESSION_TIMEOUT:
                        print("Your session has expired. Please log in to resume.")
                        break
                    #show menu
                    print("-"*10 + "Menu" + "-"*10)
                    print("1) Add New Employee")
                    print("2) Update Employee Info")
                    print("3) Remove Employee")
                    print("4) Show Current Employees")
                    print("5) Remove user")
                    print("6) Exit")
                    
                    try:
                        choice = int(input("Please select an option (1-6)"))
                    except ValueError:
                        print("Invalid input. Please enter a number between 1 and 6.")
                        continue
                    
                    if choice == 1:
                    # Add New Employee
                        employeeId = input("Enter new employee ID: ")
                        if any(emp.employeeId == employeeId for emp in employees.employeeList):
                            print(f"Employee ID '{employeeId}' already exists. Please use a unique ID.")
                            continue
                        
                        if len(employeeId) < 4:
                            print("Employee ID must be at least 4 numbers.")
                            continue
                        firstName = input("Enter First Name: ")
                        lastName = input("Enter Last Name: ")
                        email = input("Enter email: ")
                        salary = float(input("Enter Salary: "))
                        startDate = input("Enter Start Date (YYYY-MM-DD): ")
                        title = input("Enter employee title: ")
                        addNewEmployee(employees, employeeId, firstName, lastName, email, salary, startDate, title)
                        print("Employee added successfully.")
                        logging.info(f"Employee '{employeeId}' added to Employees.")
    
                    elif choice == 2:
                    # Update Employee Info
    
                        employeeId = input("Enter Employee ID to update: ")
                        if not any(emp.employeeId == employeeId for emp in employees.employeeList):
                            print(f"Employee {employeeId} not found. Please enter valid employee ID.")
                            continue  
                        firstName = input("Enter new First Name (leave blank to skip): ")
                        lastName = input("Enter new Last Name (leave blank to skip): ")
                        email = input("Enter new Email (leave blank to skip): ")
                        startDate = input("Enter new start Date (leave blank to skip): ")
                        salary = input("Enter new salary (leave blank to skip): ")
                        try:
                            salary = float(salary.strip()) if salary.strip() else None
                        except ValueError:
                            print("Invalid salary input. Please enter a valid number.")
                            continue
                        title= input("Enter new title (leave blank to skip): ")
                        updateEmployeeInfo(employees, employeeId, firstName or None, lastName or None, email or None, salary or None, startDate or None, title or None)
                        print("Employee information updated successfully.")
                        logging.info(f"Employee'{employeeId}' has been updated.")
        
                    elif choice == 3:
                    #Remove Employee
                        employeeId = input("Enter Employee ID to remove: ")
                        if any(emp.employeeId == employeeId for emp in employees.employeeList):
                            removeEmployee(employees, employeeId)
                            employees.save_to_file()
                            print(f"Employee {employeeId} removed successfully.")
                            logging.info(f"Employee'{employeeId}' has been removed.")
                        else:
                            print(f"Employee {employeeId} not found.")
                            logging.warning(f"Attempted to remove non-existent employee: {employeeId}")
                            
                    elif choice == 4: 
                    # Show Current Employees 
                        showAllEmployees(employees.employeeList)
                    
                    elif choice == 5:
                    # remove user
                        remove_username = input("Enter the username to remove: ").strip().lower()
                        if remove_username == username:
                            print("You cannot remove your own account while logged in.")
                            continue
                        if auth.remove_user(remove_username):
                            print(f"User '{remove_username}' has been removed successfully.")
                        else:
                           print(f"user '{remove_username}' does not exist.")
                        auth.save_users()
        
                    elif choice == 6:
                    # Exit
                        employees.save_to_file()
                        print("Data saved. Exiting program.")
                        break
                    else:
                        print("Invalid choice, please select a valid option.")
            else:
                print("Invalid password. Please try again.")
                logging.warning(f"User '{username}' failed to log in.")
                # Add failed attempt
                current_time = time.time()
                login_attempts[username]["attempts"].append(current_time)

        elif choice == 3:
            print("Exiting. Goodbye.")
            break
        else:
            print("Invalid choice. Please select a valid option.")