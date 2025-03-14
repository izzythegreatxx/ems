from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import bcrypt

# Initialize SQLAlchemy
db = SQLAlchemy()

# User Model (For Admins)
class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

# Employee Model (For Employees)
class Employee(db.Model):
    __tablename__ = "employees"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)

    def set_password(self, password):
        """Hashes and sets the employee password."""
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password):
        """Verifies the employee password."""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def to_dict(self):
        """Convert Employee objects to dictionary for API responses"""
        return {
            "id": self.id, 
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "salary": self.salary,
            "start_date": self.start_date.strftime('%Y-%m-%d'),
            "title": self.title,
            "username": self.username 
        }
