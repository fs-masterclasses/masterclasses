from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    Response,
    session,
    url_for,
)

from flask_login import current_user, login_user, login_required, logout_user

from app.models import (
    Location,
    Masterclass,
    MasterclassAttendee,
    MasterclassContent,
    User,
    db,
)
from app import gmaps

main_bp = Blueprint("main_bp", __name__)


@main_bp.route('/')
@main_bp.route('/index', methods=['GET'])
@login_required
def index():
    masterclasses = Masterclass.query.filter_by(draft=False).order_by(Masterclass.timestamp.asc()).all()
    return render_template('index.html', title='Home', user=User, masterclasses=masterclasses)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.index'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email-address']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password')
            return redirect(url_for('main_bp.login'))
        login_user(user,
                # remember=request.form.remember_me.data
                   )
        return redirect(url_for('main_bp.index'))
    return render_template('login.html', title='Sign In')


@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main_bp.index'))


@main_bp.route('/masterclass/<masterclass_id>', methods=['GET', 'POST'])
@login_required
def masterclass_profile(masterclass_id):
    masterclass = Masterclass.query.get(masterclass_id)
    already_attendee = MasterclassAttendee.is_attendee(current_user.id, masterclass_id)
    if request.method == 'POST':
            new_attendee = MasterclassAttendee(attendee_id = current_user.id, masterclass_id = masterclass_id) 
            db.session.add(new_attendee) 
            db.session.commit()
            return redirect(url_for('main_bp.signup_confirmation', masterclass_id=masterclass_id))
    return render_template('masterclass-profile.html', masterclass=masterclass, already_attendee=already_attendee)


@main_bp.route('/signup-confirmation', methods=['GET'])
@login_required
def signup_confirmation():
    masterclass = Masterclass.query.get(request.args["masterclass_id"])
    return render_template('signup-confirmation.html', masterclass=masterclass)


@main_bp.route('/my-masterclasses', methods=['GET'])
@login_required
def my_masterclasses():
    user = current_user
    booked_masterclasses = user.get_booked_masterclasses()
    return render_template('my-masterclasses.html', booked_masterclasses=booked_masterclasses)


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


@main_bp.route("/create-masterclass/location/type", methods=["GET", "POST"])
@login_required
def choose_location_type():
    if request.method == "POST":
        if not request.form.get("location-type"):
            return render_template(
                "create-masterclass/location/choose-location-type.html",
                validation_error=True
            ), 403
        if request.form["location-type"] == "online":
            return redirect(url_for("main_bp.add_online_details"))
        elif request.form["location-type"] == "in person":
            return redirect(url_for("main_bp.search_for_location"))
    else:
        return render_template(
            "create-masterclass/location/choose-location-type.html"
        )


@main_bp.route("/create-masterclass/location/online", methods=["GET", "POST"])
@login_required
def add_online_details():
    if request.method == "POST":
        if not request.form.get("url"):
            return render_template(
                "create-masterclass/location/online-details.html",
                validation_error=True,
                joining_instructions=request.form.get("joining_instructions"),
            ), 403
        draft_masterclass = Masterclass.query.get(
            session["draft_masterclass_id"]
        )
        draft_masterclass.set_location_details(
            data=request.form, is_remote=True,
        )
        return redirect(url_for("main_bp.index"))

    return render_template("create-masterclass/location/online-details.html")


@main_bp.route("/create-masterclass/location/search", methods=["GET", "POST"])
@login_required
def search_for_location():
    if request.method == "POST":
        if not request.form.get("location"):
            return render_template(
                "create-masterclass/location/search.html",
                validation_error=True
            ), 403
        query = request.form["location"]
        results = Location.return_existing_location_or_none(query)[0:3]
        if results:
            results = [location.to_dict() for location in results]
            is_database_data = True
        else:
            results = gmaps.places(query=query)["results"][0:3]
            is_database_data = False

        session["location_search_results"] = results
        session["location_in_db"] = is_database_data

        return redirect(url_for("main_bp.location_search_results"))

    return render_template("create-masterclass/location/search.html")


@main_bp.route("/create-masterclass/location/search/results", methods=["GET", "POST"])
@login_required
def location_search_results():
    results = session["location_search_results"]
    is_database_data = session["location_in_db"]
    if request.method == "POST":
        if not request.form.get("select-location"):
            return render_template(
                "create-masterclass/location/search-results.html",
                validation_error=True,
                results=results,
                is_database_data=is_database_data,
            ), 403
        draft_masterclass = Masterclass.query.get(session["draft_masterclass_id"])
        location = results[int(request.form["select-location"])]
        if is_database_data:
            draft_masterclass.location_id = location["id"]
        else:
            new_location = Location(
                maps_id=location["place_id"],
                name=location["name"],
                address=location["formatted_address"],
            )
            db.session.add(new_location)
            db.session.commit()
            draft_masterclass.location_id = new_location.id

        db.session.add(draft_masterclass)
        db.session.commit()

        return redirect(url_for("main_bp.add_in_person_location_details"))

    return render_template(
        "create-masterclass/location/search-results.html",
        results=results,
        is_database_data=is_database_data,
    )


@main_bp.route("/create-masterclass/location/details", methods=["GET", "POST"])
@login_required
def add_in_person_location_details():
    if request.method == "POST":
        mandatory_fields = ["room", "floor"]
        filled_fields = [
            field for field in mandatory_fields if request.form[field] != ''
        ]
        if not all(field in filled_fields for field in mandatory_fields):
            return render_template(
                "create-masterclass/location/in-person-details.html",
                validation_error=True,
                empty_fields=[
                    field for field in mandatory_fields if field not in filled_fields
                ],
                form_data=request.form
            ), 403
        draft_masterclass = Masterclass.query.get(session["draft_masterclass_id"])
        draft_masterclass.set_location_details(data=request.form, is_remote=False)
        return redirect(url_for("main_bp.index"))
    return render_template("create-masterclass/location/in-person-details.html")
