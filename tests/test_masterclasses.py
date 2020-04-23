import pytest

from flask import template_rendered, session, url_for
from contextlib import contextmanager
from app import create_app
from app import db as _db
from config import *
from app.models import MasterclassContent

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
def logged_in_user(test_client):
    with test_client:
        test_client.post(
            "main_bp.login", data={"email-address": "test@user.com", "password": "Password"}
        )
        yield
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
def new_masterclass_content_data_category(db):
    mc = MasterclassContent(name='Introduction to R', description='This masterclass will give you a solid understanding of how to run queries using R.', category='Data')
    db.session.add(mc)
    db.session.commit()
    yield
    db.session.delete(mc)
    db.session.commit()

def test_login_not_required(test_client, db):
    rv = test_client.get('/')
    assert rv.status_code == 200


def test_login_required(logged_in_user, test_client):
    rv = test_client.get('/')
    assert rv.status_code == 200

@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
        print('hereeeeee', context)
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

@pytest.mark.parametrize('endpoint, data, expected_template, expected_status_code',
(
    ('/choose-content', {'select-job-family': 'Data'}, 'create-masterclass/content/new-or-existing.html', 200),
    ('/choose-content/new-or-existing', {'which-masterclass': 'new masterclass'}, 'create-masterclass/content/create-new.html', 200),
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
('/choose-content/new-or-existing', {'which-masterclass': 'Introduction to R'}, 'main_bp.index'),
('/choose-content/create-new', {'masterclass-name': 'A name', 'masterclass-description': 'A description'}, 'main_bp.index'),
))
def test_user_is_redirected_to_correct_url(test_client, logged_in_user, new_masterclass_content_data_category, endpoint, data, expected_route):
    response = test_client.post(endpoint, data = data)
    assert response.status_code == 302
    assert response.location == f'http://localhost{url_for(expected_route)}'

def test_chosen_job_family_is_added_to_session(test_client, logged_in_user):
    with test_client.post('/choose-content', data = {'select-job-family': 'Data'}):
        assert session['job_family'] == 'Data'
