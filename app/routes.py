from flask import render_template, url_for, flash, redirect, request, Blueprint, session, Response
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


@main_bp.route('/masterclass/<masterclass_id>', methods=['GET', 'POST'])
@login_required
def masterclass_profile(masterclass_id):
    masterclass = Masterclass.query.get(masterclass_id)
    already_attendee = MasterclassAttendee.is_attendee(current_user.id, masterclass_id)
    if request.method == 'POST':
            new_attendee = MasterclassAttendee(attendee_id = current_user.id, masterclass_id = masterclass_id) 
            db.session.add(new_attendee) 
            db.session.commit()
            return redirect(url_for('signup_confirmation', masterclass_id=masterclass_id))
    return render_template('masterclass-profile.html', masterclass_data=masterclass, already_attendee=already_attendee)


@main_bp.route('/signup-confirmation', methods=['GET'])
@login_required
def signup_confirmation():
    masterclass = Masterclass.query.get(request.args["masterclass_id"])
    return render_template('signup-confirmation.html', masterclass=masterclass)


@main_bp.route('/my_masterclasses', methods=['GET'])
@login_required
def my_masterclasses():
    user = current_user
    booked_masterclasses = user.booked_masterclasses
    return render_template('my-masterclasses.html')


@main_bp.route('/create-masterclass', methods=['GET', 'POST'])
@login_required
def create_masterclass_start():
    if request.method == 'POST':
        new_masterclass = Masterclass()
        db.session.add(new_masterclass)
        db.session.commit()
        session['draft_masterclass_id'] = new_masterclass.id
        return render_template('create-masterclass/content/choose-ddat-family.html')
    return render_template('create-masterclass/start.html')


@main_bp.route('/create-masterclass/content/job-family', methods=['GET', 'POST'])
@login_required
def choose_job_family():
    if request.method == 'GET':
        return render_template('create-masterclass/content/choose-ddat-family.html')
    elif request.method == 'POST':    
        chosen_job_family = request.form['select-job-family']
        session['job_family'] = chosen_job_family
        existing_masterclasses = MasterclassContent.query.filter_by(category=chosen_job_family)
        return render_template('create-masterclass/content/new-or-existing.html',  existing_masterclasses=existing_masterclasses)


@main_bp.route('/create-masterclass/content/new-or-existing', methods=['GET', 'POST'])
@login_required
def choose_new_or_existing_content():
    if request.method == 'POST':
        choice = request.form['which-masterclass']
        if choice =="new masterclass":
            return render_template('create-masterclass/content/create-new.html')
        else:
            draft_masterclass = Masterclass.query.filter_by(id=session['draft_masterclass_id']).first()
            draft_masterclass.masterclass_content_id = int(choice)
            db.session.add(draft_masterclass)
            db.session.commit()
            return redirect(url_for('main_bp.index'))
    elif request.method == 'GET':
        chosen_job_family = session['job_family']
        existing_masterclasses = MasterclassContent.query.filter_by(category=chosen_job_family)
        return render_template('create-masterclass/content/new-or-existing.html', existing_masterclasses=existing_masterclasses)
    else:
        return Response(status_code=405) 


@main_bp.route('/create-masterclass/content/create-new', methods=['GET', 'POST'])
@login_required
def create_new_content():
    if request.method == 'POST':
            new_content = MasterclassContent(name = request.form['masterclass-name'], description = request.form['masterclass-description'])
            db.session.add(new_content) 
            db.session.commit()
            draft_masterclass = Masterclass.query.get(session['draft_masterclass_id'])
            draft_masterclass.masterclass_content_id = new_content.id
            db.session.add(draft_masterclass)
            db.session.commit()
            return redirect(url_for('main_bp.index')) # TODO will take them back to task list page
    else:
        return render_template('create-masterclass/content/create-new.html')