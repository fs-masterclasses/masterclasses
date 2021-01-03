import pytest

from flask import session, template_rendered, url_for
from contextlib import contextmanager
from datetime import datetime

from app.models import Location, Masterclass, MasterclassContent


@pytest.fixture
def test_content_data_category(db, blank_session):
    mc = MasterclassContent(id=1, name='Introduction to R', description='This masterclass will give you a solid understanding of how to run queries using R.', category='Data')
    db.session.add(mc)
    db.session.commit()
    yield mc

@pytest.fixture()
def test_location(db, blank_session):
    test_location = Location(id=1, name='Test building', address='1 Road, SW1 1RE')
    db.session.add(test_location)
    db.session.commit()
    yield test_location


@pytest.fixture()
def test_masterclass_with_details(db, blank_session):
    m = Masterclass(id=1, is_remote=False, max_attendees=10, timestamp=datetime(2020, 10, 30, 15, 30), location_id=1, masterclass_content_id=1)
    db.session.add(m)
    db.session.commit()
    yield m


@pytest.fixture()
def test_masterclass_remote(db, blank_session):
    m = Masterclass(id=2, is_remote=True, max_attendees=10, timestamp=datetime(2020, 10, 30, 15, 30))
    db.session.add(m)
    db.session.commit()
    yield m


def test_logging_in(test_client, db, test_user):
    response = test_client.post(
            url_for("main_bp.login"), data={"email-address": "test@example.com", "password": "password"}
        )
    assert response.status_code == 302
    assert response.location == f'http://localhost{url_for("main_bp.index")}'


@pytest.mark.parametrize(
    'route',
    (
        ('/'),
        ('/masterclass/1'),
        ('/signup-confirmation'),
        ('/create-masterclass'),
        ('/create-masterclass/content/job-family'),
        ('/create-masterclass/content/new-or-existing'),
        ('/create-masterclass/content/create-new')
    )
)
def test_cannot_access_routes_when_not_logged_in(test_client, db, test_masterclass, route):
    response = test_client.get(route)
    assert response.status_code == 302
    assert url_for("main_bp.login") in response.location


def test_access_homepage_logged_in(logged_in_user, db):
    response = logged_in_user.get('/')
    assert response.status_code == 200


@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

@pytest.mark.parametrize('endpoint, data, expected_template, expected_status_code',
(
    ('/create-masterclass/content/job-family', {'select-job-family': 'Data'}, 'create-masterclass/content/new-or-existing.html', 200),
    ('/create-masterclass/content/new-or-existing', {'which-masterclass': 'new masterclass'}, 'create-masterclass/content/create-new.html', 200),
))
def test_user_is_displayed_the_correct_template_according_to_request(test_app, test_client, logged_in_user, test_content_data_category, endpoint, data, expected_template, expected_status_code):
    with captured_templates(test_app) as templates:
        response = test_client.post(endpoint, data = data)
    assert response.status_code == expected_status_code
    assert len(templates) == 1
    template, context = templates[0]
    assert template.name == expected_template

@pytest.mark.parametrize('endpoint, data, expected_route',
(
('/create-masterclass/content/new-or-existing', {'which-masterclass': 1}, 'main_bp.index'),
('/create-masterclass/content/create-new', {'masterclass-name': 'A name', 'masterclass-description': 'A description'}, 'main_bp.index'),
))
def test_user_is_redirected_to_correct_url(test_client, logged_in_user, test_content_data_category, endpoint, data, expected_route, test_masterclass, blank_session):
    with logged_in_user.session_transaction() as session:
        session['draft_masterclass_id'] = 1
    response = test_client.post(endpoint, data = data)
    assert response.status_code == 302
    assert response.location == f'http://localhost{url_for(expected_route)}'

def test_chosen_job_family_is_added_to_session(logged_in_user, blank_session):
    with logged_in_user.post('/create-masterclass/content/job-family', data = {'select-job-family': 'Data'}):
        assert session['job_family'] == 'Data'

def test_draft_masterclass_id_is_added_to_session(logged_in_user, blank_session):
    with logged_in_user.post('/create-masterclass'):
        assert session['draft_masterclass_id'] == 1

def test_add_existing_content_to_draft_masterclass(logged_in_user, db, test_content_data_category, test_masterclass, blank_session):
    with logged_in_user.session_transaction() as session:
        session['draft_masterclass_id'] = 1
    logged_in_user.post('/create-masterclass/content/new-or-existing', data = {'which-masterclass': test_content_data_category.id})
    assert test_masterclass.masterclass_content_id == test_content_data_category.id

def test_add_new_content_to_draft_masterclass(logged_in_user, test_masterclass, blank_session):
    with logged_in_user.session_transaction() as session:
        session['draft_masterclass_id'] = 1
    logged_in_user.post('/create-masterclass/content/create-new', data = {'masterclass-name': 'Test name', 'masterclass-description': 'A description'})
    new_content = MasterclassContent.query.filter_by(name='Test name').first()
    assert test_masterclass.masterclass_content_id == new_content.id

@pytest.mark.parametrize('location_details_to_display, masterclass_id',
(
('Test building', 1),
('Remote', 2)
))
def test_correct_location_details_displayed(logged_in_user, test_masterclass_remote, test_masterclass_with_details, blank_session, location_details_to_display, masterclass_id, test_location):
    response = logged_in_user.get(f'/masterclass/{masterclass_id}')
    assert f'<p class="govuk-body">{location_details_to_display}</p>' in response.get_data(as_text=True)

def test_remote_joining_info_hidden_in_masterclass_profile_if_user_not_attendee(logged_in_user, test_masterclass_remote, blank_session):
    response = logged_in_user.get('/masterclass/2')
    assert '<h2 class="govuk-heading-m">Joining link</h2>' not in response.get_data(as_text=True)

def test_remote_joining_info_visible_in_masterclass_profile_if_user_is_attendee(logged_in_user, test_masterclass_remote, blank_session):
    # Sign current user up to masterclass
    logged_in_user.post('/masterclass/2')
    response = logged_in_user.get('/masterclass/2')
    assert '<h2 class="govuk-heading-m">Joining link</h2>' in response.get_data(as_text=True)

def test_display_my_masterclasses_with_none_booked(logged_in_user, blank_session):
    response = logged_in_user.get('/my-masterclasses')
    assert '<p class="govuk-body">You haven\'t booked any masterclasses.</p>' in response.get_data(as_text=True)

def test_display_my_masterclasses(logged_in_user, test_masterclass_with_details, test_content_data_category, blank_session):
    logged_in_user.post(f'/masterclass/{test_masterclass_with_details.id}')
    response = logged_in_user.get('/my-masterclasses')
    assert f'<a class="govuk-link--no-visited-state" href="/masterclass/1">{test_masterclass_with_details.content.name}</a>' in response.get_data(as_text=True)

# Add location tests


@pytest.mark.parametrize(
    "location_type, redirect_url",
    (("online", "add_online_details"), ("in person", "search_for_location"),),
)
def test_redirect_to_correct_template_after_choose_location_type(
    logged_in_user, location_type, redirect_url
):
    response = logged_in_user.post(
        "/create-masterclass/location/type", data={"location-type": location_type}
    )
    assert response.status_code == 302
    assert response.location == f'http://localhost{url_for(f"main_bp.{redirect_url}")}'


def test_add_online_details(logged_in_user, test_masterclass, blank_session):
    with logged_in_user.session_transaction() as session:
        session["draft_masterclass_id"] = 1
    response = logged_in_user.post(
        "/create-masterclass/location/online",
        data={"url": "testing.com", "joining_instructions": "Please join"},
    )
    assert response.status_code == 302
    assert test_masterclass.is_remote == True
    assert test_masterclass.remote_url == "testing.com"
    assert test_masterclass.remote_joining_instructions == "Please join"


@pytest.mark.parametrize(
    "query_string",
    (("TEST BUILDING"), ("test"), ("bUiLdInG"), ("SW1"), ("sw1 1re"), ("1re")),
)
def test_get_existing_location_from_db_by_query_string_success(
    logged_in_user, blank_session, test_location, query_string
):
    assert (
        Location.return_existing_location_or_none(query_string)[0].name
        == "Test building"
    )


def test_get_existing_location_from_db_by_query_string_failure(
    logged_in_user, blank_session
):
    assert Location.return_existing_location_or_none("Nice skyscraper") == []


def test_location_search_results_appear_on_page(
    logged_in_user, blank_session, test_location
):
    response = logged_in_user.post(
        "/create-masterclass/location/search",
        data={"location": "test building"},
        follow_redirects=True,
    )
    assert "Test building" in response.get_data(as_text=True)


def test_new_location_added_to_db(logged_in_user, test_masterclass, blank_session):
    places_api_results = [
        {"place_id": "123", "name": "A place", "formatted_address": "An address"}
    ]
    with logged_in_user.session_transaction() as session:
        session["draft_masterclass_id"] = 1
        session["location_search_results"] = places_api_results
        session["location_in_db"] = False
    response = logged_in_user.post(
        "/create-masterclass/location/search/results", data={"select-location": "0"}
    )
    new_location = Location.query.filter_by(maps_id="123").first()
    assert response.status_code == 302
    assert test_masterclass.location_id == new_location.id


def test_add_in_person_details(logged_in_user, test_masterclass, blank_session):
    with logged_in_user.session_transaction() as session:
        session["draft_masterclass_id"] = 1
    response = logged_in_user.post(
        "/create-masterclass/location/details",
        data={"room": "1D", "floor": "1", "building_instructions": "Some instructions"},
    )
    assert response.status_code == 302
    assert test_masterclass.room == "1D"
    assert test_masterclass.floor == "1"
    assert test_masterclass.building_instructions == "Some instructions"
    assert test_masterclass.is_remote == False


@pytest.mark.parametrize(
    "route, form_data, empty_fields",
    (
        ("/create-masterclass/location/type", {}, []),
        ("/create-masterclass/location/online", {}, []),
        ("/create-masterclass/location/online", {"joining_instructions": "Test"}, []),
        ("/create-masterclass/location/search", {}, []),
        ("/create-masterclass/location/search/results", {}, []),
        (
            "/create-masterclass/location/details",
            {"room": "", "floor": "", "building_instructions": ""},
            ["room", "floor"]
        ),
        (
            "/create-masterclass/location/details",
            {"room": "1", "floor": "", "building_instructions": ""},
            ["floor"]
        ),
        (
            "/create-masterclass/location/details",
            {"room": "", "floor": "1", "building_instructions": ""},
            ["room"]
        ),
    ),
)
def test_handle_empty_location_fields(
    test_app, logged_in_user, route, form_data, empty_fields
):
    """
    Tests that a 403 error is returned when forms are submitted without
    required fields and that 'validation_error' and, if multiple fields are
    mandatory, the 'empty_fields' variable are set in the template context.
    """
    with captured_templates(test_app) as templates:
        response = logged_in_user.post(route, data=form_data)
        context = templates[0][1]
    assert response.status_code == 403
    assert context["validation_error"]
    if empty_fields:
        assert context["empty_fields"] == empty_fields
