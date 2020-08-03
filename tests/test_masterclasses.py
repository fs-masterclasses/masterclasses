import pytest

from flask import session, template_rendered, url_for
from contextlib import contextmanager
from app import create_app
from app import db as _db
from config import *
from app.models import MasterclassContent, Masterclass, User

@pytest.fixture(scope="session")
def test_app():
    app = create_app(TestConfig)
    yield app

@pytest.fixture(scope="session", autouse=True)
def test_client(test_app):

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = test_app.test_client()

    # Establish an application context before running the tests.
    ctx = test_app.test_request_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()

@pytest.fixture
def logged_in_user(test_client, db, test_user):
    with test_client:
        test_client.post(
            url_for("main_bp.login"), data={"email-address": "test@user.com", "password": "password"}
        )
        yield test_client
        test_client.get("main_bp.logout")

@pytest.fixture(scope="session")
def db(test_client):
    """
    This takes the FlaskClient object and applies it to the database.app attribute. Once this fixture is finished with, it drops everything in there
    """
    _db.app = test_client.application
    _db.create_all()

    yield _db

    _db.drop_all()

@pytest.fixture
def test_user(db, blank_session):
    u = User(email='test@example.com')
    u.set_password('password')
    db.session.add(u)
    db.session.commit()
    yield

@pytest.fixture(scope="function", autouse=False)
def blank_session(db):
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session_ = db.create_scoped_session(options=options)

    db.session = session_

    print("Yielding blank session")
    yield session_

    transaction.rollback()
    connection.close()
    session_.remove()
    print("Rolled back blank session")

@pytest.fixture
def new_masterclass_content_data_category(db, blank_session):
    mc = MasterclassContent(name='Introduction to R', description='This masterclass will give you a solid understanding of how to run queries using R.', category='Data')
    db.session.add(mc)
    db.session.commit()
    yield 

@pytest.fixture()
def new_masterclass(db, blank_session):
    m = Masterclass(id=1)
    db.session.add(m)
    db.session.commit()
    yield


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
def test_cannot_access_routes_when_not_logged_in(test_client, db, new_masterclass, route):
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
def test_user_is_displayed_the_correct_template_according_to_request(test_app, test_client, logged_in_user, new_masterclass_content_data_category, endpoint, data, expected_template, expected_status_code):
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
def test_user_is_redirected_to_correct_url(test_client, logged_in_user, new_masterclass_content_data_category, endpoint, data, expected_route, new_masterclass, blank_session):
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

def test_add_existing_content_to_draft_masterclass(logged_in_user, db, new_masterclass_content_data_category, new_masterclass, blank_session):
    with logged_in_user.session_transaction() as session:    
        session['draft_masterclass_id'] = 1
    masterclass_content = MasterclassContent.query.filter_by(name='Introduction to R').first()
    logged_in_user.post('/create-masterclass/content/new-or-existing', data = {'which-masterclass': masterclass_content.id})
    draft_masterclass = Masterclass.query.get(1)
    assert draft_masterclass.masterclass_content_id == masterclass_content.id

def test_add_new_content_to_draft_masterclass(logged_in_user, new_masterclass, blank_session):
    with logged_in_user.session_transaction() as session:    
        session['draft_masterclass_id'] = 1
    logged_in_user.post('/create-masterclass/content/create-new', data = {'masterclass-name': 'Test name', 'masterclass-description': 'A description'})
    draft_masterclass = Masterclass.query.get(1)
    new_content = MasterclassContent.query.filter_by(name='Test name').first()
    assert draft_masterclass.masterclass_content_id == new_content.id
