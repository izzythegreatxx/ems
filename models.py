from flask_sqlalchemy import SQLAlchemy
import logging
import bcrypt


#initialize SQLAlchemy
db = SQLAlchemy()

# create a user model
class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    @staticmethod
    def hash_password(password):
        """Hash password before storing it using bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def check_password(self, password):
        """verify password against stored hash"""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

# create Employee model and convert objects to dictionary for API handling 
class Employee(db.Model):
    __tablename__ = "employees"
    
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(50), nullable=False)
    
    def to_dict(self):
        """Convert Employee objects to dictioinary for API responses"""
        return {
            "id": self.id, 
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "salary": self.salary,
            "start_date":self.start_date.strftime('%Y-%m-%d'),
            "title": self.title
        }
        
# Class that manages the employee list 
class Employees:
    """ Handles CRUD operations using SQLAlchemy"""
        
    #adds new employee to the database 
    def add_employee(self, employee):
        db.session.add(employee)
        db.session.commit()
        logging.info(f"Added employee: {employee.id} - {employee.first_name} {employee.last_name}")
        
    # removes existing employees from the current list
    def remove_employee(self, employeeId):
        employee = Employee.query.get(employeeId)
        if employee:
            db.session.delete(employee)
            db.session.commit()
            logging.info(f"Removed employee: {employeeId}")
            return True
        logging.warning(f"Employee ID {employeeId} not found.")
        return False
        
    # updates a current employees information
    def update_employee_info(self, employeeId, **kwargs):
        employee = Employee.query.get(employeeId)
        if employee:
            for key, value in kwargs.items():
                if hasattr(employee, key) and value is not None:
                    setattr(employee, key, value)
            db.session.commit()
            logging.info(f"Updated employee: {employeeId}")
            return True
        logging.warning(f"Employee ID {employeeId} not found")
        return False
    
    def get_all_employees(self):
        """Retrieves all employees from the database"""
        return Employee.query.all()