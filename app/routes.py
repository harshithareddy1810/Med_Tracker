import os
import random
from datetime import datetime

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, jsonify)
from flask_login import login_user, logout_user, login_required, current_user
from twilio.rest import Client

from . import db
from .models import User, Medicine, Schedule, MedicationLog

# Initialize the Blueprint
main = Blueprint('main', __name__)


# --- USER AUTHENTICATION ROUTES ---

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        # Basic validation for mobile number format
        if len(mobile) > 10 and mobile.startswith('+'):
            session['mobile_for_verification'] = mobile
            if send_otp(mobile):
                flash('An OTP has been sent to your mobile number.', 'info')
                return redirect(url_for('main.verify_otp'))
            else:
                flash('Failed to send OTP. Please try again.', 'danger')
        else:
            flash('Please enter a valid mobile number with country code (e.g., +1234567890).', 'danger')

    return render_template('login.html')


@main.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'mobile_for_verification' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        # Ensure submitted_otp is not None before converting to int
        if 'otp' in session and submitted_otp and int(submitted_otp) == session['otp']:
            mobile = session['mobile_for_verification']
            user = User.query.filter_by(mobile_number=mobile).first()
            if not user:  # If user doesn't exist, create a new one
                user = User(mobile_number=mobile)
                db.session.add(user)
                db.session.commit()

            login_user(user, remember=True)
            session.pop('otp', None)  # Clear OTP from session
            session.pop('mobile_for_verification', None)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_otp.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


# --- MAIN APPLICATION ROUTES ---

@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    medicines = Medicine.query.filter_by(user_id=current_user.id).order_by(Medicine.name).all()

    # Query for the 20 most recent medication logs for the user
    logs = db.session.query(MedicationLog, Schedule, Medicine)\
        .join(Schedule, MedicationLog.schedule_id == Schedule.id)\
        .join(Medicine, Schedule.medicine_id == Medicine.id)\
        .filter(Medicine.user_id == current_user.id)\
        .order_by(MedicationLog.date_taken.desc())\
        .limit(20).all()

    return render_template('dashboard.html', medicines=medicines, logs=logs)


# @main.route('/add-medicine', methods=['POST'])
# @login_required
# def add_medicine():
#     name = request.form.get('name')
#     dosage = request.form.get('dosage')
#     times = request.form.getlist('times[]')

#     if name and dosage and times:
#         new_med = Medicine(name=name, dosage=dosage, user_id=current_user.id)
#         db.session.add(new_med)
#         db.session.commit()  # Commit to get the new_med.id

#         for t in times:
#             if t:
#                 time_obj = datetime.strptime(t, '%H:%M').time()
#                 schedule = Schedule(medicine_id=new_med.id, time_to_take=time_obj)
#                 db.session.add(schedule)

#         db.session.commit()
#         flash('Medicine added successfully!', 'success')
#     else:
#         flash('Please fill all fields.', 'danger')

#     return redirect(url_for('main.dashboard'))

# In app/routes.py, update the add_medicine function

@main.route('/add-medicine', methods=['POST'])
@login_required
def add_medicine():
    name = request.form.get('name')
    dosage = request.form.get('dosage')
    times = request.form.getlist('times[]')

    if name and dosage and times:
        new_med = Medicine(name=name, dosage=dosage, user_id=current_user.id)
        db.session.add(new_med)
        db.session.commit()

        # Loop through each time input to get its days
        for i, t in enumerate(times):
            if t:
                time_obj = datetime.strptime(t, '%H:%M').time()
                schedule = Schedule(
                    medicine_id=new_med.id, 
                    time_to_take=time_obj,
                    on_monday='days_{}_mon'.format(i) in request.form,
                    on_tuesday='days_{}_tue'.format(i) in request.form,
                    on_wednesday='days_{}_wed'.format(i) in request.form,
                    on_thursday='days_{}_thu'.format(i) in request.form,
                    on_friday='days_{}_fri'.format(i) in request.form,
                    on_saturday='days_{}_sat'.format(i) in request.form,
                    on_sunday='days_{}_sun'.format(i) in request.form
                )
                db.session.add(schedule)

        db.session.commit()
        flash('Medicine added successfully!', 'success')
    else:
        flash('Please fill all fields.', 'danger')

    return redirect(url_for('main.dashboard'))
# # In app/routes.py, update the edit_medicine function

@main.route('/edit-medicine/<int:med_id>', methods=['GET', 'POST'])
@login_required
def edit_medicine(med_id):
    med = Medicine.query.get_or_404(med_id)
    # ... (authorization check remains the same)

    if request.method == 'POST':
        med.name = request.form.get('name')
        med.dosage = request.form.get('dosage')
        
        Schedule.query.filter_by(medicine_id=med.id).delete() # Delete old schedules
        
        times = request.form.getlist('times[]')
        for i, t in enumerate(times):
            if t:
                time_obj = datetime.strptime(t, '%H:%M').time()
                schedule = Schedule(
                    medicine_id=med.id,
                    time_to_take=time_obj,
                    on_monday='days_{}_mon'.format(i) in request.form,
                    on_tuesday='days_{}_tue'.format(i) in request.form,
                    on_wednesday='days_{}_wed'.format(i) in request.form,
                    on_thursday='days_{}_thu'.format(i) in request.form,
                    on_friday='days_{}_fri'.format(i) in request.form,
                    on_saturday='days_{}_sat'.format(i) in request.form,
                    on_sunday='days_{}_sun'.format(i) in request.form
                )
                db.session.add(schedule)
        
        db.session.commit()
        flash('Medicine updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('edit_medicine.html', medicine=med)

@main.route('/delete-medicine/<int:med_id>', methods=['POST'])
@login_required
def delete_medicine(med_id):
    med = Medicine.query.get_or_404(med_id)
    if med.user_id != current_user.id:
        return 'You are not authorized to delete this item.', 403

    db.session.delete(med)
    db.session.commit()
    flash('Medicine deleted.', 'success')
    return redirect(url_for('main.dashboard'))


# --- API ROUTES FOR JAVASCRIPT ---

@main.route('/log-dose', methods=['POST'])
@login_required
def log_dose():
    data = request.get_json()
    schedule_id = data.get('schedule_id')
    status = data.get('status')

    schedule = Schedule.query.get(schedule_id)
    if not schedule or schedule.medicine.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Invalid schedule'}), 403

    log_entry = MedicationLog(
        schedule_id=schedule_id,
        date_taken=datetime.utcnow(),
        status=status
    )
    db.session.add(log_entry)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Log updated successfully'})


# @main.route('/api/schedules')
# @login_required
# def get_schedules():
#     schedules = db.session.query(Schedule, Medicine).join(Medicine).filter(Medicine.user_id == current_user.id).all()

#     schedule_list = []
#     for schedule, medicine in schedules:
#         schedule_list.append({
#             'schedule_id': schedule.id,
#             'medicine_name': medicine.name,
#             'dosage': medicine.dosage,
#             'time': schedule.time_to_take.strftime('%H:%M')
#         })

#     return jsonify(schedule_list)
# In app/routes.py, update the get_schedules function

@main.route('/api/schedules')
@login_required
def get_schedules():
    # Get the current day of the week (Monday is 0, Sunday is 6)
    today_weekday = datetime.utcnow().weekday()
    day_filter = {
        0: Schedule.on_monday,
        1: Schedule.on_tuesday,
        2: Schedule.on_wednesday,
        3: Schedule.on_thursday,
        4: Schedule.on_friday,
        5: Schedule.on_saturday,
        6: Schedule.on_sunday,
    }[today_weekday]

    # Query schedules that are active for the current day
    schedules = db.session.query(Schedule, Medicine)\
        .join(Medicine)\
        .filter(Medicine.user_id == current_user.id)\
        .filter(day_filter == True)\
        .all()
    
    # ... (the rest of the function remains the same)
    schedule_list = []
    for schedule, medicine in schedules:
        schedule_list.append({
            'schedule_id': schedule.id,
            'medicine_name': medicine.name,
            'dosage': medicine.dosage,
            'time': schedule.time_to_take.strftime('%H:%M')
        })
        
    return jsonify(schedule_list)

# --- HELPER FUNCTIONS ---

def send_otp(mobile_number):
    """Sends an OTP to the user's mobile number using Twilio."""
    try:
        client = Client(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
        otp = random.randint(100000, 999999)
        session['otp'] = otp
        message = client.messages.create(
            body=f'Your Smart Medicine Reminder OTP is: {otp}',
            from_=os.environ.get('TWILIO_PHONE_NUMBER'),
            to=mobile_number
        )
        return True
    except Exception as e:
        print(f"Error sending OTP: {e}")  # For debugging, log this properly in a real app
        return False