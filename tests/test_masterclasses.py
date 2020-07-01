import pytest

from flask import session
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
