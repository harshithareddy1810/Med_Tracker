# app/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from . import db # We will create this 'db' object in __init__.py

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    medicines = db.relationship('Medicine', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.mobile_number}>'

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False) # e.g., "500mg", "1 tablet"
    schedules = db.relationship('Schedule', backref='medicine', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Medicine {self.name}>'

# class Schedule(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
#     time_to_take = db.Column(db.Time, nullable=False) # e.g., 09:00, 21:00
#     logs = db.relationship('MedicationLog', backref='schedule', lazy=True, cascade="all, delete-orphan")

#     def __repr__(self):
#         return f'<Schedule for medicine {self.medicine_id} at {self.time_to_take}>'
# In app/models.py

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    time_to_take = db.Column(db.Time, nullable=False)
    
    # New fields for days of the week
    on_monday = db.Column(db.Boolean, default=False, nullable=False)
    on_tuesday = db.Column(db.Boolean, default=False, nullable=False)
    on_wednesday = db.Column(db.Boolean, default=False, nullable=False)
    on_thursday = db.Column(db.Boolean, default=False, nullable=False)
    on_friday = db.Column(db.Boolean, default=False, nullable=False)
    on_saturday = db.Column(db.Boolean, default=False, nullable=False)
    on_sunday = db.Column(db.Boolean, default=False, nullable=False)
    
    logs = db.relationship('MedicationLog', backref='schedule', lazy=True, cascade="all, delete-orphan")

    # Optional helper function to make display easier
    def get_active_days(self):
        days = []
        if self.on_monday: days.append('Mon')
        if self.on_tuesday: days.append('Tue')
        if self.on_wednesday: days.append('Wed')
        if self.on_thursday: days.append('Thu')
        if self.on_friday: days.append('Fri')
        if self.on_saturday: days.append('Sat')
        if self.on_sunday: days.append('Sun')
        if len(days) == 7: return "Every Day"
        return ", ".join(days) if days else "No days selected"

class MedicationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    date_taken = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(10), nullable=False) # "Taken", "Missed"

    def __repr__(self):
        return f'<Log {self.id} - Status: {self.status}>'