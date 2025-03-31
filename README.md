# 🧑‍💼 Flask Employee Management System (EMS)

A web-based **Employee Management System** built with **Python (Flask)**, using **HTML**, **CSS**, and **JavaScript** for the frontend.

This system supports admin-managed employee records, user authentication, secure password handling, and persistent storage via **SQLite**.

---

## 🚀 Features

### 🔐 User Authentication
- Secure **Admin** and **Employee** login
- Role-based access control
- Password validation and hashing with `bcrypt`
- Session management

### 👥 Employee Management
- Add, view, update, and delete employee records
- Fields include:
  - Employee ID
  - Name (first + last)
  - Email
  - Salary
  - Start Date
  - Job Title

### 📜 Logging
- Tracks important actions (e.g., login, CRUD operations)
- Error logging with log rotation (`RotatingFileHandler`)

### 🗃️ Data Storage
- Powered by **SQLite**
- ORM via **SQLAlchemy**
- Automatic DB migrations with **Flask-Migrate**

### 📧 Email Support
- Integrated with Flask-Mail
- Email alerts and contact form notifications
- Gmail SMTP compatible (App Password support)

### 📊 Admin Dashboard (Optional)
- Overview of salaries, employee count, and revenue
- Live charts with Chart.js

---

## 📂 Tech Stack

- **Backend**: Flask, Python 3
- **Frontend**: HTML5, CSS3, Vanilla JS
- **Database**: SQLite + SQLAlchemy
- **Security**: bcrypt, Flask-Login, JWT
- **Other**: Flask-Migrate, dotenv

---

## ⚙️ Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/flask-ems.git
cd flask-ems

