from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import current_user, login_user, login_required, logout_user
from app.models import *

main_bp = Blueprint("main_bp", __name__)


@main_bp.route('/')
@main_bp.route('/index', methods=['GET'])
@login_required
def index():
    masterclasses = Masterclass.query.filter_by(draft=None).order_by(Masterclass.timestamp.asc()).all()
    return render_template('index.html', title='Home', user=User, masterclasses=masterclasses)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email-address']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user,
                # remember=request.form.remember_me.data
                   )
        return redirect(url_for('main_bp.index'))
    return render_template('login.html', title='Sign In')


@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@login_required
@main_bp.route('/masterclass/<masterclass_id>', methods=['GET', 'POST'])
def masterclass_profile(masterclass_id):
    masterclass = Masterclass.query.get(masterclass_id)
    already_attendee = MasterclassAttendee.is_attendee(current_user.id, masterclass_id)
    if request.method == 'POST':
            new_attendee = MasterclassAttendee(attendee_id = current_user.id, masterclass_id = masterclass_id) 
            db.session.add(new_attendee) 
            db.session.commit()
            return redirect(url_for('signup_confirmation', masterclass_id=masterclass_id))
    return render_template('masterclass-profile.html', masterclass_data=masterclass, already_attendee=already_attendee)


@login_required
@main_bp.route('/signup-confirmation', methods=['GET'])
def signup_confirmation():
    masterclass = Masterclass.query.get(request.args["masterclass_id"])
    return render_template('signup-confirmation.html', masterclass=masterclass)


@login_required
@main_bp.route('/my_masterclasses', methods=['GET'])
def my_masterclasses():
    user = current_user
    booked_masterclasses = user.booked_masterclasses
    return render_template('my-masterclasses.html')
